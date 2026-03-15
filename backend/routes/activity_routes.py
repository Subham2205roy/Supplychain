from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database.database import get_db
from backend import schemas
from backend.models.activity_model import Notification, ActivityLog
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User

router = APIRouter(
    prefix="/api/activity",
    tags=["Activity & Notifications"]
)

@router.get("/notifications", response_model=List[schemas.Notification])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.company_id == current_user.company_id
    ).order_by(Notification.created_at.desc()).all()

@router.post("/notifications/read/{notification_id}")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    return {"status": "success"}

@router.post("/notifications/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "success"}

@router.get("/logs", response_model=List[schemas.ActivityLog])
def get_activity_logs(
    entity_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ActivityLog).filter(
        ActivityLog.company_id == current_user.company_id
    )
    
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
        
    return query.order_by(ActivityLog.created_at.desc()).limit(100).all()
