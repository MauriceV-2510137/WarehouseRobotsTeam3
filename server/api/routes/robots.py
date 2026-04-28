from fastapi import APIRouter, Depends, HTTPException
 
from server.api.dependencies import get_registry
from server.api.schemas.robot import PoseSchema, RobotSchema, RobotStatus
from server.core.registry import RobotRecord, RobotRegistry
 
router = APIRouter(prefix="/robots", tags=["robots"])
 
def _serialize(record: RobotRecord) -> RobotSchema:
    return RobotSchema(
        robot_id=record.robot_id,
        status=RobotStatus(record.status.name),
        pose=PoseSchema(x=record.pose.x, y=record.pose.y, theta=record.pose.theta),
        active_task_id=record.active_task_id,
        last_heartbeat=record.last_heartbeat,
        registered_at=record.registered_at,
    )
 
@router.get("/", response_model=list[RobotSchema])
def list_robots(registry: RobotRegistry = Depends(get_registry)) -> list[RobotSchema]:
    return [_serialize(r) for r in registry.get_all()]
 
@router.get("/{robot_id}", response_model=RobotSchema)
def get_robot(robot_id: str, registry: RobotRegistry = Depends(get_registry)) -> RobotSchema:
    record = registry.get(robot_id)
    if not record:
        raise HTTPException(status_code=404, detail="Robot not found")
    return _serialize(record)