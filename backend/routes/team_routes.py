from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from backend.database.database import get_db
from backend.routes.auth_routes import get_current_user
from backend.models.company_model import Company
from backend.models.team_invite_model import TeamInvite
from backend.models.user_model import User
from backend.models.user_company_model import UserCompany
from backend.mail_utils import send_team_invite_email
from backend.schemas import TeamInviteCreate, TeamInviteAccept, TeamInviteResponse

router = APIRouter(
    prefix="/team",
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

    # Automatically send the email invitation
    send_team_invite_email(payload.invited_email, company.name, token)

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

    # Check if they are already a member
    existing_member = db.query(UserCompany).filter(
        UserCompany.user_id == current_user.id,
        UserCompany.company_id == invite.company_id
    ).first()
    
    if not existing_member:
        # Create new membership
        new_member = UserCompany(
            user_id=current_user.id,
            company_id=invite.company_id,
            role="Member"
        )
        db.add(new_member)
    
    # Update active company (immediate switch as per user request)
    current_user.company_id = invite.company_id
    invite.status = "accepted"
    invite.accepted_by_user_id = current_user.id

    db.commit()

    return {"message": "Successfully joined team. Context switched.", "company_id": invite.company_id}


@router.get("/my-companies")
def list_my_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Companies where they are a member in the UserCompany table
    memberships = db.query(UserCompany).filter(UserCompany.user_id == current_user.id).all()
    company_ids = [m.company_id for m in memberships]
    
    # 2. Companies they own (for back-compatibility/robustness)
    owned_companies = db.query(Company).filter(Company.owner_user_id == current_user.id).all()
    for oc in owned_companies:
        if oc.id not in company_ids:
            company_ids.append(oc.id)

    # Fetch company details
    companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "is_owner": c.owner_user_id == current_user.id,
            "is_active": c.id == current_user.company_id
        }
        for c in companies
    ]


@router.post("/switch-context/{company_id}")
def switch_active_team(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user belongs to this company
    is_member = db.query(UserCompany).filter(
        UserCompany.user_id == current_user.id,
        UserCompany.company_id == company_id
    ).first()
    
    is_owner = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_user_id == current_user.id
    ).first()
    
    if not is_member and not is_owner:
        raise HTTPException(status_code=403, detail="You do not have access to this company.")
        
    current_user.company_id = company_id
    db.commit()
    
    return {"message": "Context switched successfully.", "company_id": company_id}


@router.get("/members")
def list_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User has no company.")

    members = (
        db.query(User)
        .filter(User.company_id == current_user.company_id)
        .all()
    )

    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    return [
        {
            "id": m.id,
            "username": m.username,
            "email": m.email,
            "role": "Owner" if company and company.owner_user_id == m.id else "Member",
        }
        for m in members
    ]


@router.get("/invites", response_model=List[TeamInviteResponse])
def list_pending_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User has no company.")

    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company or company.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the company owner can view invites.")

    invites = (
        db.query(TeamInvite)
        .filter(TeamInvite.company_id == current_user.company_id, TeamInvite.status == "pending")
        .order_by(TeamInvite.created_at.desc())
        .all()
    )

    return [
        {
            "id": inv.id,
            "company_id": inv.company_id,
            "invited_email": inv.invited_email,
            "token": inv.token,
            "status": inv.status,
            "created_at": inv.created_at,
            "expires_at": inv.expires_at
        }
        for inv in invites
    ]


@router.delete("/invites/{invite_id}")
def delete_team_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")

    company = db.query(Company).filter(Company.id == invite.company_id).first()
    if not company or company.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the company owner can remove invites.")

    db.delete(invite)
    db.commit()

    return {"message": "Invitation removed successfully."}
