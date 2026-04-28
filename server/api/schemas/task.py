from datetime import datetime

from pydantic import BaseModel, Field

class SubmitTaskRequest(BaseModel):
    aisle: int = Field(..., ge=1, le=5)
    shelf: int = Field(..., ge=1, le=3)

class TaskSchema(BaseModel):
    task_id: str
    aisle: int
    shelf: int
    status: str
    robot_id: str | None
    created_at: datetime
    updated_at: datetime