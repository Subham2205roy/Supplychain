from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.database.database import Base


class TeamInvite(Base):
    __tablename__ = "team_invites"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    invited_email = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, index=True, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
