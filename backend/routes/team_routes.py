from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from backend.database.database import get_db
from backend.routes.auth_routes import get_current_user
from backend.models.company_model import Company
from backend.models.team_invite_model import TeamInvite
from backend.models.user_model import User
from backend.schemas import TeamInviteCreate, TeamInviteAccept, TeamInviteResponse

router = APIRouter(
    prefix="/api/team",
    tags=["Team"]
)


@router.post("/invites", response_model=TeamInviteResponse)
def create_team_invite(
    payload: TeamInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User has no company.")

    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company or company.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the company owner can invite.")

    existing_user = db.query(User).filter(User.email == payload.invited_email).first()
    if existing_user and existing_user.company_id == company.id:
        raise HTTPException(status_code=400, detail="User is already in your company.")
    if existing_user and existing_user.company_id and existing_user.company_id != company.id:
        raise HTTPException(status_code=400, detail="User already belongs to another company.")

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)

    invite = TeamInvite(
        company_id=company.id,
        invited_email=payload.invited_email,
        token=token,
        status="pending",
        expires_at=expires_at
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    return invite


@router.post("/invites/accept")
def accept_team_invite(
    payload: TeamInviteAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(TeamInvite).filter(TeamInvite.token == payload.token).first()
    if not invite or invite.status != "pending":
        raise HTTPException(status_code=404, detail="Invite not found or already used.")

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invite has expired.")

    if current_user.company_id and current_user.company_id != invite.company_id:
        current_company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if current_company and current_company.owner_user_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Company owners cannot join another company with this account."
            )

    current_user.company_id = invite.company_id
    invite.status = "accepted"
    invite.accepted_by_user_id = current_user.id

    db.commit()

    return {"message": "Invite accepted.", "company_id": invite.company_id}
