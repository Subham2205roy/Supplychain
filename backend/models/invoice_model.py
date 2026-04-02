from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.database.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    invoice_number = Column(String, unique=True, index=True)
    order_id = Column(String, index=True) # References Sale.order_id
    customer_name = Column(String)
    amount = Column(Float)
    currency = Column(String, default="INR")
    status = Column(String, default="Unpaid") # Unpaid, Paid, Partially Paid, Overdue
    due_date = Column(Date)
    payment_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
