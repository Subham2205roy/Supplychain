from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from backend.database.database import Base

class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    sender_email = Column(String, index=True)
    otp_code = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(Date, nullable=True)
    created_at = Column(Date, server_default=func.current_date())
