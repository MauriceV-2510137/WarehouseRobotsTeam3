from queue import Empty, Queue
from core.events import Event

class EventQueue:
    def __init__(self) -> None:
        self._queue: Queue[Event] = Queue()

    def publish(self, event: Event) -> None:
        self._queue.put(event)

    def poll_all(self) -> list[Event]:
        events = []
        try:
            while True:
                events.append(self._queue.get_nowait())
        except Empty:
            pass
        return events