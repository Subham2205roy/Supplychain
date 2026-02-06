from sqlalchemy import Column, Integer, String, ForeignKey
from backend.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=True)
