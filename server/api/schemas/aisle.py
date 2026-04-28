from pydantic import BaseModel

class AisleSchema(BaseModel):
    aisle_id: str
    locked: bool
    owner_robot_id: str | None