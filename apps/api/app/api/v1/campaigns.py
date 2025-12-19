from fastapi import APIRouter, HTTPException

from ...api.deps import (
    CampaignSortDep,
    CurrentUserDep,
    PaginationDep,
    SearchDep,
    SessionDep,
)
from ...schemas.campaign import CampaignDetail, CampaignListResponse
from ...services import NotFoundError, campaign_service

router = APIRouter(tags=["campaigns"])


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    session: SessionDep,
    pagination: PaginationDep,
    search_params: SearchDep,
    sort_params: CampaignSortDep,
    current_user: CurrentUserDep,
):
    return await campaign_service.list_campaigns(
        session,
        pagination=pagination,
        search=search_params.search,
        sort_by=sort_params.sort_by,
        sort_dir=sort_params.sort_dir.value,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    try:
        return await campaign_service.get_campaign_detail(
            session, campaign_id=campaign_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
