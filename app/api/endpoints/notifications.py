from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.models.notification import Notification, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter()

@router.post("/", response_model=NotificationResponse)
def create_notification(noti: NotificationCreate, db: Session = Depends(get_db)):
    # Basic Idempotency check (Step 7 will enhance this, but we get a head start)
    if noti.idempotency_key:
        existing = db.query(Notification).filter(Notification.idempotency_key == noti.idempotency_key).first()
        if existing:
            return existing # Return the already processed identical request
            
    # Save the notification as pending
    db_noti = Notification(
        user_id=noti.user_id,
        channel=noti.channel,
        priority=noti.priority,
        message_body=noti.message_body,
        idempotency_key=noti.idempotency_key,
        status=NotificationStatus.PENDING
    )
    db.add(db_noti)
    db.commit()
    db.refresh(db_noti)
    
    # In Step 4 we will push this to a Background Worker queue here!
    
    return db_noti

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    noti = db.query(Notification).filter(Notification.id == notification_id).first()
    if not noti:
        raise HTTPException(status_code=404, detail="Notification not found")
    return noti

@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
