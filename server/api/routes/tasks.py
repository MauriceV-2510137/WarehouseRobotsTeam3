from fastapi import APIRouter, Depends, HTTPException

from server.api.dependencies import get_task_dispatcher, get_task_store
from server.api.schemas.task import SubmitTaskRequest, TaskSchema
from server.core.task_dispatcher import TaskDispatcher
from server.core.task_store import TaskRecord, TaskStore

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize(record: TaskRecord) -> TaskSchema:
    return TaskSchema(
        task_id=record.task_id,
        aisle=record.aisle,
        shelf=record.shelf,
        status=record.status.name,
        robot_id=record.robot_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/", response_model=list[TaskSchema])
def list_tasks(task_store: TaskStore = Depends(get_task_store)):
    return [_serialize(t) for t in task_store.get_all()]


@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: str, task_store: TaskStore = Depends(get_task_store)):
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(record)


@router.post("/", response_model=TaskSchema, status_code=201)
def submit_task(
    body: SubmitTaskRequest,
    dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
):
    try:
        return _serialize(dispatcher.submit(body.aisle, body.shelf))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))