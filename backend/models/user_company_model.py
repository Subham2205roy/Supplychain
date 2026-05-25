from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.database.database import Base


class UserCompany(Base):
    """
    Junction table for many-to-many relationship between Users and Companies.
    A user can belong to multiple companies with different roles.
    """
    __tablename__ = "user_companies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    role = Column(String, default="Member")  # e.g., "Owner", "Member", "Admin"
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
