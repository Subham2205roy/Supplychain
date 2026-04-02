from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from backend.database.database import Base

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("company_id", "order_id", name="uq_sales_company_order"),
    )
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(String, index=True)
    product_name = Column(String, index=True)
    category = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    unit_cost = Column(Float)
    order_date = Column(Date)
    promised_delivery_date = Column(Date)
    actual_delivery_date = Column(Date, nullable=True)
    delivery_status = Column(String)
    country = Column(String)
    region_risk_score = Column(Float)
