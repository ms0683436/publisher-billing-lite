from fastapi import APIRouter, Query

from ...api.deps import CurrentUserDep, SessionDep
from ...schemas.change_history import ChangeHistoryListResponse
from ...services import change_history_service
from ...services.change_history_service import EntityType

router = APIRouter(tags=["history"])


@router.get(
    "/history/{entity_type}/{entity_id}", response_model=ChangeHistoryListResponse
)
async def get_entity_history(
    entity_type: EntityType,
    entity_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get change history for a specific entity."""
    return await change_history_service.get_history_for_entity(
        session,
        entity_type,
        entity_id,
        limit=limit,
        offset=offset,
    )
