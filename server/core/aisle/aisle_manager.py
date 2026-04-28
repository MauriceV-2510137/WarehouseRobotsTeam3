from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from server.core.events import AisleReleaseEvent, AisleRequestEvent, Event
from server.interfaces.server_comm import IServerComm

_LOCK_TIMEOUT_S = 60.0

@dataclass
class _AisleLease:
    robot_id: str
    task_id: str
    expires_at: datetime

class AisleManager:
    def __init__(self, comm: IServerComm) -> None:
        self._comm = comm
        self._leases: dict[str, _AisleLease] = {}

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def handle_event(self, event: Event) -> None:
        if isinstance(event, AisleRequestEvent):
            self._handle_request(event)
        elif isinstance(event, AisleReleaseEvent):
            self._handle_release(event)

    def update(self) -> None:
        """Expire stale leases."""
        now = datetime.now(timezone.utc)

        for aisle_id in list(self._leases.keys()):
            lease = self._leases[aisle_id]

            if lease.expires_at <= now:
                self._expire(aisle_id, lease)

    # ------------------------------------------------------------
    # Request flow
    # ------------------------------------------------------------
    def _handle_request(self, event: AisleRequestEvent) -> None:
        self._expire_if_needed(event.aisle_id)

        if self._can_acquire(event.aisle_id, event.robot_id):
            self._acquire(event)
            self._comm.respond_aisle(event.robot_id, event.aisle_id, granted=True)
        else:
            self._comm.respond_aisle(event.robot_id, event.aisle_id, granted=False)

    def _can_acquire(self, aisle_id: str, robot_id: str) -> bool:
        lease = self._leases.get(aisle_id)
        return lease is None or lease.robot_id == robot_id

    def _acquire(self, event: AisleRequestEvent) -> None:
        now = datetime.now(timezone.utc)

        self._leases[event.aisle_id] = _AisleLease(
            robot_id=event.robot_id,
            task_id=event.task_id,
            expires_at=now + timedelta(seconds=_LOCK_TIMEOUT_S),
        )

    # ------------------------------------------------------------
    # Release flow
    # ------------------------------------------------------------
    def _handle_release(self, event: AisleReleaseEvent) -> None:
        lease = self._leases.get(event.aisle_id)
        if not lease:
            return

        if lease.robot_id != event.robot_id:
            return

        self._release(event.aisle_id)

    def _release(self, aisle_id: str) -> None:
        self._leases.pop(aisle_id, None)

    # ------------------------------------------------------------
    # Expiry handling
    # ------------------------------------------------------------
    def _expire_if_needed(self, aisle_id: str) -> None:
        lease = self._leases.get(aisle_id)
        if lease and lease.expires_at <= datetime.now(timezone.utc):
            self._expire(aisle_id, lease)

    def _expire(self, aisle_id: str, lease: _AisleLease) -> None:
        self._leases.pop(aisle_id, None)

        # Notify robot that lease is no longer valid
        self._comm.respond_aisle(
            lease.robot_id,
            aisle_id,
            granted=False,
        )

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def is_locked(self, aisle_id: str) -> bool:
        lease = self._leases.get(aisle_id)
        return lease is not None and lease.expires_at > datetime.now(timezone.utc)

    def get_owner(self, aisle_id: str) -> str | None:
        lease = self._leases.get(aisle_id)
        if not lease or lease.expires_at <= datetime.now(timezone.utc):
            return None
        return lease.robot_id