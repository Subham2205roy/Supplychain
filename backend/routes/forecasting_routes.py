from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List

from backend.database.database import get_db
from backend.models.sales_model import Sale
from backend.models.inventory_model import Inventory
from backend.models.user_model import User
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/forecasting", tags=["Forecasting"])

@router.get("/inventory-health")
def get_inventory_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates Burn Rate and Days of Cover for all products in inventory.
    """
    inventory_items = db.query(Inventory).filter(Inventory.company_id == current_user.company_id).all()
    
    health_reports = []
    # Use last 30 days for velocity / burn rate calculation
    thirty_days_ago = date.today() - timedelta(days=30)
    
    for item in inventory_items:
        # Calculate daily velocity (avg sales per day)
        total_sold = db.query(func.sum(Sale.quantity)).filter(
            Sale.company_id == current_user.company_id,
            Sale.product_name == item.product_name,
            Sale.order_date >= thirty_days_ago
        ).scalar() or 0
        
        daily_burn_rate = total_sold / 30.0
        
        days_left = 999 # Default for items with no sales
        if daily_burn_rate > 0:
            days_left = int(item.stock_level / daily_burn_rate)
            
        stock_out_date = None
        if daily_burn_rate > 0:
            stock_out_date = date.today() + timedelta(days=days_left)

        health_reports.append({
            "product_name": item.product_name,
            "stock_level": item.stock_level,
            "burn_rate": round(daily_burn_rate, 2),
            "days_left": days_left,
            "stock_out_date": stock_out_date,
            "status": "Healthy" if days_left > 14 else "At Risk" if days_left > 7 else "Critical"
        })
        
    return health_reports
