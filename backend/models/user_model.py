from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from backend.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    auth_provider = Column(String, default="local")  # "local" or "google"
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=True)
    
    # Security Fields
    failed_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)
