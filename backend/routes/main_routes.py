import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import random
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from backend.database.database import get_db
from backend.models.sales_model import Sale
import datetime
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User

router = APIRouter()

class BusinessIdea(BaseModel):
    idea: str

_BUSINESS_KEYWORDS = {
    "shop", "store", "market", "retail", "wholesale", "logistics", "supply",
    "chain", "inventory", "warehouse", "delivery", "shipping", "transport",
    "manufacturing", "factory", "production", "service", "services", "saas",
    "software", "platform", "b2b", "b2c", "subscription", "restaurant",
    "food", "cafe", "grocery", "pharmacy", "health", "medical", "device",
    "ecommerce", "commerce", "online", "app", "marketplace", "trading",
    "export", "import", "procurement", "sourcing", "logistic"
}

def _validate_business_text(text: str) -> str:
    idea_text = (text or "").strip()
    words = re.findall(r"[A-Za-z]{3,}", idea_text.lower())
    if len(idea_text) < 15 or len(words) < 3:
        raise HTTPException(status_code=400, detail="Please describe the business in a short sentence (at least 3 real words).")
    if not any(k in idea_text.lower() for k in _BUSINESS_KEYWORDS):
        raise HTTPException(status_code=400, detail="Mention a business/commerce term (e.g., logistics, retail, store, platform).")
    return idea_text

@router.get("/api/kpis")
def get_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_cost_result = db.query(func.sum(Sale.unit_cost * Sale.quantity)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0
    total_revenue_result = db.query(func.sum(Sale.unit_price * Sale.quantity)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0
    profit_margin = ((total_revenue_result - total_cost_result) / total_revenue_result) * 100 if total_revenue_result > 0 else 0
    avg_risk_result = db.query(func.avg(Sale.region_risk_score)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0
    
    delivered_orders = db.query(Sale).filter(
        Sale.delivery_status == 'Delivered',
        Sale.company_id == current_user.company_id
    )
    total_delivered = delivered_orders.count()
    on_time_deliveries = delivered_orders.filter(Sale.actual_delivery_date <= Sale.promised_delivery_date).count()
    delivery_performance = (on_time_deliveries / total_delivered) * 100 if total_delivered > 0 else 0
    
    return {
        "total_cost": round(total_cost_result),
        "profit_margin": round(profit_margin, 1),
        "risk_score": round(avg_risk_result, 1),
        "delivery_performance": round(delivery_performance, 1),
    }

@router.get("/api/profit-trend")
def get_profit_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    six_months_ago = datetime.date.today() - datetime.timedelta(days=180)
    monthly_profit = db.query(
        func.strftime("%Y-%m", Sale.order_date).label("month"),
        func.sum(Sale.unit_price * Sale.quantity).label("total_revenue"),
        func.sum(Sale.unit_cost * Sale.quantity).label("total_cost")
    ).filter(
        Sale.order_date >= six_months_ago,
        Sale.company_id == current_user.company_id
    ).group_by("month").order_by("month").all()
    
    labels = [row.month for row in monthly_profit]
    data = [round(((r.total_revenue - r.total_cost) / r.total_revenue) * 100, 2) if r.total_revenue > 0 else 0 for r in monthly_profit]
    return {"labels": labels, "data": data}

@router.get("/api/delivery-trend")
def get_delivery_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    six_months_ago = datetime.date.today() - datetime.timedelta(days=180)
    delivery_data = db.query(
        func.strftime("%Y-%m", Sale.order_date).label("month"),
        func.count(Sale.id).label("total_delivered"),
        func.sum(case((Sale.actual_delivery_date <= Sale.promised_delivery_date, 1), else_=0)).label("on_time")
    ).filter(
        Sale.order_date >= six_months_ago,
        Sale.delivery_status == 'Delivered',
        Sale.company_id == current_user.company_id
    ).group_by("month").order_by("month").all()
    
    labels = [row.month for row in delivery_data]
    data = [round((row.on_time / row.total_delivered) * 100, 1) if row.total_delivered > 0 else 0 for row in delivery_data]
    return {"labels": labels, "data": data}

@router.get("/api/gdp-comparison")
def get_gdp_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    revenue_by_country = (
        db.query(
            Sale.country.label("country"),
            func.sum(Sale.unit_price * Sale.quantity).label("total_revenue")
        )
        .filter(Sale.company_id == current_user.company_id)
        .group_by(Sale.country)
        .order_by(func.sum(Sale.unit_price * Sale.quantity).desc())
        .all()
    )

    labels = [(row.country or "Unknown") for row in revenue_by_country]
    data = [row.total_revenue for row in revenue_by_country]

    return {"labels": labels, "data": data}


@router.get("/api/revenue-history")
def get_revenue_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return annual revenue (unit_price * quantity) for the last 5 years including current year."""
    five_years_ago = datetime.date.today().year - 4
    results = (
        db.query(
            func.strftime("%Y", Sale.order_date).label("year"),
            func.sum(Sale.unit_price * Sale.quantity).label("total_revenue")
        )
        .filter(Sale.company_id == current_user.company_id)
        .filter(Sale.order_date >= datetime.date(five_years_ago, 1, 1))
        .group_by("year")
        .order_by("year")
        .all()
    )
    labels = [row.year for row in results]
    data = [row.total_revenue for row in results]
    return {"labels": labels, "data": data}

@router.get("/api/orders-overview")
def get_orders_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Pending = anything not delivered
    total_pending = db.query(func.count(Sale.id)).filter(
        Sale.company_id == current_user.company_id,
        Sale.delivery_status != "Delivered"
    ).scalar() or 0

    # Shipped this month = delivered orders with order_date in current month
    today = datetime.date.today()
    shipped_this_month = db.query(func.count(Sale.id)).filter(
        Sale.company_id == current_user.company_id,
        Sale.delivery_status == "Delivered",
        func.strftime("%Y-%m", Sale.order_date) == today.strftime("%Y-%m")
    ).scalar() or 0

    return {"total_pending": int(total_pending), "total_shipped_month": int(shipped_this_month)}

@router.get("/api/success-prediction")
def get_success_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_orders = db.query(func.count(Sale.id)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0

    if total_orders == 0:
        return {
            "prediction_score": 0,
            "confidence_level": 0.0,
            "key_factors": ["Upload sales data to generate predictions"]
        }

    total_cost = db.query(func.sum(Sale.unit_cost * Sale.quantity)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0
    total_revenue = db.query(func.sum(Sale.unit_price * Sale.quantity)).filter(
        Sale.company_id == current_user.company_id
    ).scalar() or 0

    delivered_orders = db.query(Sale).filter(
        Sale.company_id == current_user.company_id,
        Sale.delivery_status == "Delivered"
    )
    total_delivered = delivered_orders.count()
    on_time_deliveries = delivered_orders.filter(
        Sale.actual_delivery_date <= Sale.promised_delivery_date
    ).count()
    delivery_performance = (on_time_deliveries / total_delivered) if total_delivered > 0 else 0.0

    profit_margin = ((total_revenue - total_cost) / total_revenue) if total_revenue > 0 else 0.0

    # Simple heuristic score (0-100) based on margin + delivery performance
    score = int(max(0, min(100, (profit_margin * 100 * 0.6) + (delivery_performance * 100 * 0.4))))
    confidence = max(0.3, min(0.95, 0.4 + (total_orders / 200)))

    key_factors = []
    key_factors.append("Healthy profit margin" if profit_margin >= 0.2 else "Low profit margin")
    key_factors.append("On-time delivery rate strong" if delivery_performance >= 0.9 else "Delivery performance needs improvement")
    key_factors.append("Sufficient order volume" if total_orders >= 50 else "Low order volume")

    return {
        "prediction_score": score,
        "confidence_level": round(float(confidence), 2),
        "key_factors": key_factors
    }

@router.post("/api/analyze")
def analyze_idea(idea_data: BusinessIdea):
    idea_text = _validate_business_text(idea_data.idea)
    idea_name = " ".join(idea_text.split()[:4]) + "..."
    score = random.randint(65, 90)
    return { "idea_name": idea_name, "score": score, "recommendation": "Promising venture with high potential." if score > 75 else "Moderate potential, requires validation.", "top_reasons": ["Strong market demand", "Favorable regulatory environment", "Scalable business model"], "investment": f"${random.randint(5, 8)}0,000 - ${random.randint(9, 15)}0,000", "timeline": f"{random.randint(9, 12)}-{random.randint(13, 18)} Months to MVP", "charts": { "financials": { "labels": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"], "revenue": [5000, 25000, 60000, 110000, 180000, 260000], "cost": [15000, 20000, 22000, 25000, 28000, 32000] }, "market": { "labels": ["Target Audience", "Adjacent Markets", "Niche Segments"], "data": [65, 25, 10] } } }
# Add this missing function to your main_routes.py file

@router.get("/api/sales-trend")
def get_sales_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates and returns the total sales revenue for the last 6 months.
    """
    six_months_ago = datetime.date.today() - datetime.timedelta(days=180)

    monthly_sales = db.query(
        func.strftime("%Y-%m", Sale.order_date).label("month"),
        func.sum(Sale.unit_price * Sale.quantity).label("total_revenue")
    ).filter(
        Sale.order_date >= six_months_ago,
        Sale.company_id == current_user.company_id
    ) \
     .group_by("month").order_by("month").all()

    labels = [row.month for row in monthly_sales]
    data = [row.total_revenue for row in monthly_sales]

    return {"labels": labels, "data": data}
