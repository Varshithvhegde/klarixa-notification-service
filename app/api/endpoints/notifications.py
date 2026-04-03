from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.dependencies import get_db
from app.models.notification import Notification, NotificationStatus
from app.models.template import NotificationTemplate
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationBatchCreate
from app.workers.queue import notification_queue
from app.core.rate_limiter import check_rate_limit

router = APIRouter()

async def process_single_notification(noti: NotificationCreate, db: AsyncSession):
    """Internal helper to create notifications per channel (does NOT enqueue yet)."""
    check_rate_limit(noti.user_id)
    
    # 1. Resolve message body from template or payload
    final_body = noti.message_body
    
    if noti.template_name:
        res = await db.execute(select(NotificationTemplate).where(NotificationTemplate.name == noti.template_name))
        tpl = res.scalars().first()
        if not tpl:
            raise HTTPException(status_code=400, detail=f"Drafting logic failed: Template '{noti.template_name}' not found locally.")
        final_body = tpl.body
        
    if not final_body:
        raise HTTPException(status_code=400, detail="Missing notification content: provide either 'message_body' or a valid 'template_name'.")

    created_notifications = []
    
    for channel in noti.channels:
        channel_key = f"{noti.idempotency_key}_{channel}" if noti.idempotency_key else None
        
        if channel_key:
            result = await db.execute(
                select(Notification).where(Notification.idempotency_key == channel_key)
            )
            existing = result.scalars().first()
            if existing:
                # We return a tuple to skip enqueuing later for existing
                created_notifications.append((existing, False)) 
                continue
                
        db_noti = Notification(
            user_id=noti.user_id,
            channel=channel,
            priority=noti.priority,
            message_body=final_body,
            idempotency_key=channel_key,
            status=NotificationStatus.PENDING
        )
        db.add(db_noti)
        # Flush to get ID
        await db.flush() 
        created_notifications.append((db_noti, True))
        
    return created_notifications

@router.post("/", response_model=List[NotificationResponse], status_code=201)
async def create_notification(noti: NotificationCreate, db: AsyncSession = Depends(get_db)):
    """Single-user multi-channel notification dispatch."""
    items = await process_single_notification(noti, db)
    await db.commit() # Database must be committed before workers can see the IDs
    
    results = []
    for db_noti, is_new in items:
        if is_new:
            await notification_queue.enqueue(
                db_noti.id, 
                priority=db_noti.priority.value, 
                template_vars=noti.template_vars
            )
        results.append(db_noti)
    return results

@router.post("/batch", response_model=dict)
async def create_batch_notifications(batch: NotificationBatchCreate, db: AsyncSession = Depends(get_db)):
    """Batch API: Dispatch notifications for multiple users simultaneously."""
    all_items = []
    
    for noti in batch.notifications:
        try:
            # We need to capture both the object and its template vars for enqueuing later
            items = await process_single_notification(noti, db)
            all_items.append((items, noti.template_vars))
        except HTTPException:
            continue

    await db.commit() # Atomic commit for the entire batch
    
    total_queued = 0
    for items, t_vars in all_items:
        for db_noti, is_new in items:
            if is_new:
                await notification_queue.enqueue(
                    db_noti.id, 
                    priority=db_noti.priority.value, 
                    template_vars=t_vars
                )
                total_queued += 1

    return {"status": "success", "queued_count": total_queued}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    noti = result.scalars().first()
    if not noti:
        raise HTTPException(status_code=404, detail="Notification not found")
    return noti
