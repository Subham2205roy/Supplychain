from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from backend.database.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    title = Column(String)
    message = Column(String)
    type = Column(String) # Info, Warning, Error, Alert
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    action = Column(String) # e.g., "Generated Invoice", "Updated Shipment"
    entity_type = Column(String) # e.g., "Invoice", "Shipment"
    entity_id = Column(String) # The ID of the affected entity
    details = Column(String) # JSON or descriptive string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
