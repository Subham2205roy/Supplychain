from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime

# --- IMPORTS ---
from backend.database.database import get_db
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.models.team_invite_model import TeamInvite
from backend.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.routes.auth_utils import hash_password, verify_password, create_access_token

# --- CONFIG ---
SECRET_KEY = "supersecretkey"  # Make sure this matches auth_utils.py if you have one there
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

router = APIRouter(tags=["Authentication"])

# 1. REGISTER
@router.post("/api/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check for a pending invite for this email
    invite = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.invited_email == user.email,
            TeamInvite.status == "pending"
        )
        .order_by(TeamInvite.created_at.desc())
        .first()
    )

    if invite and invite.expires_at and invite.expires_at < datetime.utcnow():
        invite = None

    hashed_pwd = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pwd)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if invite:
        # Join the inviter's company
        new_user.company_id = invite.company_id
        invite.status = "accepted"
        invite.accepted_by_user_id = new_user.id
        db.commit()
        db.refresh(new_user)
        return new_user

    # Create a new company for this user
    company_name = f"{user.username}'s Company"
    new_company = Company(name=company_name, owner_user_id=new_user.id)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    new_user.company_id = new_company.id
    db.commit()
    db.refresh(new_user)

    return new_user

# 2. LOGIN
@router.post("/api/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user by Email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    # Create Token
    access_token = create_access_token(data={"sub": user.email}) # Store email in token
    
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

# ==========================================
# 👇 THIS IS THE MISSING FUNCTION 👇
# ==========================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user
