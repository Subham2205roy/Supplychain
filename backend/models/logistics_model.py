from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.database.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    order_id = Column(String, index=True)
    tracking_number = Column(String, unique=True, index=True)
    carrier = Column(String) # e.g., BlueDart, FedEx, UPS
    shipping_method = Column(String) # Express, Standard, Ground
    estimated_delivery = Column(Date)
    actual_delivery = Column(Date, nullable=True)
    status = Column(String, default="Processing") # Processing, Shipped, In Transit, Delivered, Exception
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Return(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    order_id = Column(String, index=True)
    reason = Column(String)
    condition = Column(String) # Excellent, Good, Fair, Poor
    refund_status = Column(String, default="Pending") # Pending, Approved, Rejected, Refunded
    created_at = Column(DateTime(timezone=True), server_default=func.now())
