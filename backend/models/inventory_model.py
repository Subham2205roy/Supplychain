from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.database.database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    product_name = Column(String, index=True, nullable=False)
    stock_level = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
