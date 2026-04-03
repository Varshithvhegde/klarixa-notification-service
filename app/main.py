from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, notifications, webhooks, analytics, templates
from app.workers.queue import notification_queue
from app.core.logging import setup_logging

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import engine lazily so test patches represent DB state
    from app.db.database import engine, SessionLocal
    from app.models.base_class import Base
    from app.models.notification import Notification, NotificationStatus
    from sqlalchemy import select

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start the worker queue
    await notification_queue.start(workers=2)

    # RECOVERY: Re-enqueue any PENDING or in-flight notifications from previous runs
    async with SessionLocal() as db:
        # In a real system, we'd also check 'sent' if we don't have a delivery confirmation yet
        res = await db.execute(select(Notification).where(Notification.status == NotificationStatus.PENDING))
        stale_notifications = res.scalars().all()
        for sn in stale_notifications:
             # We put them back in the queue
             await notification_queue.enqueue(sn.id, priority=sn.priority.value)
    
    yield
    await notification_queue.stop()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Notipy Notification Service",
    description="Backend service for dispatching multi-channel notifications",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(templates.router, prefix="/templates", tags=["Templates"])

@app.get("/ping")
def health_check():
    return {"status": "ok", "message": "Notification service is running"}

