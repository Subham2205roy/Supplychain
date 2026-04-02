import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database.database import get_db
from backend.models.user_model import User
from backend.models.automation_model import Automation
from backend.schemas import AutomationRequestOTP, AutomationVerifyOTP, AutomationResponse
from backend.routes.auth_routes import get_current_user
from backend.mail_utils import send_otp_email, send_success_confirmation

router = APIRouter(prefix="/api/automation", tags=["Automation"])

@router.post("/request-otp")
def request_otp(
    request: AutomationRequestOTP,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate a random 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Check if an automation record already exists for this sender
    automation = db.query(Automation).filter(
        Automation.user_id == current_user.id,
        Automation.sender_email == request.sender_email
    ).first()
    
    if automation:
        automation.otp_code = otp
        automation.is_verified = False
    else:
        automation = Automation(
            user_id=current_user.id,
            sender_email=request.sender_email,
            otp_code=otp
        )
        db.add(automation)
    
    db.commit()
    
    # Send REAL email
    success = send_otp_email(request.sender_email, otp)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to send verification email. Please check your credentials or try again later."
        )
    
    return {"message": f"OTP successfully sent to {request.sender_email}"}

@router.post("/verify-otp", response_model=AutomationResponse)
def verify_otp(
    request: AutomationVerifyOTP,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    automation = db.query(Automation).filter(
        Automation.user_id == current_user.id,
        Automation.sender_email == request.sender_email,
        Automation.otp_code == request.otp_code
    ).first()
    
    if not automation:
        raise HTTPException(status_code=400, detail="Invalid OTP or sender email")
    
    duration = request.duration_days
    expiry_date = datetime.utcnow().date() + timedelta(days=duration)
    
    automation.is_verified = True
    automation.otp_code = None  # Clear OTP after verification
    automation.expires_at = expiry_date
    
    db.commit()
    db.refresh(automation)
    
    # Send confirmation instructions to the sender
    send_success_confirmation(automation.sender_email)
    
    return automation

@router.get("/list", response_model=List[AutomationResponse])
def list_automations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Automation).filter(Automation.user_id == current_user.id).all()

@router.delete("/{automation_id}")
def delete_automation(
    automation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    automation = db.query(Automation).filter(
        Automation.id == automation_id,
        Automation.user_id == current_user.id
    ).first()
    
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
        
    db.delete(automation)
    db.commit()
    
    return {"message": "Automation deleted"}
