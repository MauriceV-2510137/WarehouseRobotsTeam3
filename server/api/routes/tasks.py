from fastapi import APIRouter, Depends, HTTPException, Query

from server.api.dependencies import get_task_dispatcher, get_task_store
from server.api.schemas.task import SubmitTaskRequest, TaskSchema
from server.core.task_dispatcher import TaskDispatcher
from server.core.task_store import TaskRecord, TaskStore
from core.task import TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize(record: TaskRecord) -> TaskSchema:
    return TaskSchema(
        task_id=record.task_id,
        aisle=record.aisle,
        shelf=record.shelf,
        status=record.status,
        robot_id=record.robot_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/", response_model=list[TaskSchema])
def list_tasks(status: TaskStatus | None = Query(default=None), task_store: TaskStore = Depends(get_task_store)) -> list[TaskSchema]:
    tasks = task_store.get_all()

    if status is not None:
        tasks = [t for t in tasks if t.status == status]

    tasks.sort(key=lambda t: t.created_at)

    return [_serialize(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: str, task_store: TaskStore = Depends(get_task_store)) -> TaskSchema:
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(record)


@router.post("/", response_model=TaskSchema, status_code=201)
def submit_task(body: SubmitTaskRequest, dispatcher: TaskDispatcher = Depends(get_task_dispatcher)) -> TaskSchema:
    try:
        return _serialize(dispatcher.submit(body.aisle, body.shelf))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{task_id}", status_code=204)
def cancel_task(task_id: str, dispatcher: TaskDispatcher = Depends(get_task_dispatcher), task_store: TaskStore = Depends(get_task_store)) -> None:
    record = task_store.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")

    if record.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel task with status '{record.status.name}'",
        )

    dispatcher.cancel(task_id)