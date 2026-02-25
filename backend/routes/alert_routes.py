from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List

from backend.database.database import get_db
from backend.models.sales_model import Sale
from backend.models.inventory_model import Inventory
from backend.models.user_model import User
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/active")
def get_active_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alerts = []
    
    # 1. Low Stock Alerts
    low_stock_items = db.query(Inventory).filter(
        Inventory.company_id == current_user.company_id,
        Inventory.stock_level <= Inventory.reorder_point
    ).all()
    
    for item in low_stock_items:
        alerts.append({
            "type": "Low Stock",
            "severity": "High" if item.stock_level == 0 else "Medium",
            "message": f"Product '{item.product_name}' is below reorder point ({item.stock_level} left).",
            "product_name": item.product_name
        })
        
    # 2. Late Shipment Alerts
    today = date.today()
    late_shipments = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.delivery_status != "Delivered",
        Sale.promised_delivery_date < today
    ).all()
    
    for sale in late_shipments:
        alerts.append({
            "type": "Late Shipment",
            "severity": "High",
            "message": f"Order {sale.order_id} is overdue (Promised: {sale.promised_delivery_date}).",
            "order_id": sale.order_id
        })
        
    # 3. Regional Risk Alerts (Simple threshold for this MVP)
    high_risk_shipments = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.region_risk_score >= 8.0
    ).all()
    
    for sale in high_risk_shipments:
        alerts.append({
            "type": "High Regional Risk",
            "severity": "Medium",
            "message": f"Order {sale.order_id} is in a high-risk region ({sale.country}). Score: {sale.region_risk_score}",
            "order_id": sale.order_id
        })

    return alerts
