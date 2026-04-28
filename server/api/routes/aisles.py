from fastapi import APIRouter, Depends, HTTPException

from server.api.dependencies import get_aisle_manager, get_warehouse_map
from server.api.schemas.aisle import AisleSchema
from server.core.aisle.aisle_manager import AisleManager
from server.core.warehouse import WarehouseMap

router = APIRouter(prefix="/aisles", tags=["aisles"])

def _serialize(aisle_id: str, manager: AisleManager) -> AisleSchema:
    return AisleSchema(
        aisle_id=aisle_id,
        locked=manager.is_locked(aisle_id),
        owner_robot_id=manager.get_owner(aisle_id),
    )

@router.get("/", response_model=list[AisleSchema])
def list_aisles(manager: AisleManager = Depends(get_aisle_manager), warehouse_map: WarehouseMap = Depends(get_warehouse_map)) -> list[AisleSchema]:
    aisle_ids = [f"aisle_{i}" for i in sorted(warehouse_map.AISLE_RANGE)]
    return [_serialize(aisle_id, manager) for aisle_id in aisle_ids]

@router.get("/{aisle_id}", response_model=AisleSchema)
def get_aisle(aisle_id: str, manager: AisleManager = Depends(get_aisle_manager), warehouse_map: WarehouseMap = Depends(get_warehouse_map)) -> AisleSchema:
    valid_ids = {f"aisle_{i}" for i in warehouse_map.AISLE_RANGE}

    if aisle_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Aisle '{aisle_id}' not found",
        )

    return _serialize(aisle_id, manager)