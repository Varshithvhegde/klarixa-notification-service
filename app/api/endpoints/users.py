from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import math

from app.api.dependencies import get_db
from app.models.user_preference import UserPreference
from app.models.notification import Notification
from app.schemas.user_preference import UserPreferenceCreate, UserPreferenceResponse, UserPreferenceBulkUpdate
from app.schemas.notification import PaginatedNotificationResponse, NotificationResponse

router = APIRouter()

@router.post("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def set_user_preference(
    user_id: str, 
    preference: UserPreferenceCreate, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.channel == preference.channel
        )
    )
    pref = result.scalars().first()
    
    if pref:
        pref.is_opted_in = preference.is_opted_in
    else:
        pref = UserPreference(
            user_id=user_id,
            channel=preference.channel,
            is_opted_in=preference.is_opted_in
        )
        db.add(pref)
        
    await db.commit()
    await db.refresh(pref)
    return pref

@router.get("/{user_id}/preferences", response_model=List[UserPreferenceResponse])
async def get_user_preferences(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/{user_id}/preferences-bulk", response_model=List[UserPreferenceResponse])
async def bulk_set_preferences(
    user_id: str,
    payload: UserPreferenceBulkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Syncs all 3 main channel preferences in one request."""
    mapping = {
        "email": payload.email_enabled,
        "sms": payload.sms_enabled,
        "push": payload.push_enabled
    }
    
    responses = []
    for channel, is_opted_in in mapping.items():
        result = await db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.channel == channel
            )
        )
        pref = result.scalars().first()
        
        if pref:
            pref.is_opted_in = is_opted_in
        else:
            pref = UserPreference(
                user_id=user_id,
                channel=channel,
                is_opted_in=is_opted_in
            )
            db.add(pref)
        responses.append(pref)
        
    await db.commit()
    for r in responses:
        await db.refresh(r)
    return responses


@router.get("/{user_id}/notifications", response_model=PaginatedNotificationResponse)
async def get_user_notifications(
    user_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db)
):
    """Get notification history for a user."""
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = count_result.scalar_one()
    data_result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = data_result.scalars().all()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedNotificationResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1
    )
