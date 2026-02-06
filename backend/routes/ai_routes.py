import re
from datetime import date, timedelta
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.sales_model import Sale
from backend.models.user_model import User
from backend.routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI Chat"])


class ChatQuery(BaseModel):
    query: str


class ChatResponse(BaseModel):
    text: str
    type: str = "text"
    highlight: Optional[str] = None


BEST_SELLER_PHRASES = (
    "best seller",
    "best-selling",
    "best selling",
    "top product",
    "top item",
    "most sold",
    "most popular",
)


YEAR_RE = re.compile(r"\b(20\d{2})\b")


def tokenize(query: str) -> Tuple[str, set]:
    normalized = re.sub(r"[^a-z0-9\s]", " ", query.lower())
    tokens = [t for t in normalized.split() if t]
    return normalized, set(tokens)


def detect_intent(query_lower: str, tokens: set) -> Optional[str]:
    if any(phrase in query_lower for phrase in BEST_SELLER_PHRASES):
        return "best_seller"
    if "delivery" in tokens or "delivered" in tokens or "on time" in query_lower or "on-time" in query_lower:
        return "delivery"
    if "risk" in tokens:
        return "risk"
    if "margin" in tokens:
        return "profit_margin"
    if "profit" in tokens or "profits" in tokens:
        return "profit"
    if "revenue" in tokens or "sales" in tokens or "turnover" in tokens:
        return "revenue"
    if "cost" in tokens or "expense" in tokens or "expenses" in tokens:
        return "cost"
    return None


def get_time_window(query_lower: str) -> Tuple[Optional[date], Optional[date], Optional[str]]:
    today = date.today()

    if "last year" in query_lower or "previous year" in query_lower:
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return start, end, str(today.year - 1)

    year_match = YEAR_RE.search(query_lower)
    if year_match:
        year = int(year_match.group(1))
        return date(year, 1, 1), date(year, 12, 31), str(year)

    if (
        "this year" in query_lower
        or "current year" in query_lower
        or "yearly" in query_lower
        or "annual" in query_lower
        or "year" in query_lower
    ):
        return date(today.year, 1, 1), today, str(today.year)

    if "last month" in query_lower or "previous month" in query_lower:
        first_of_this_month = date(today.year, today.month, 1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start = date(last_month_end.year, last_month_end.month, 1)
        label = last_month_end.strftime("%B %Y")
        return start, last_month_end, label

    if "this month" in query_lower or "current month" in query_lower or "month" in query_lower:
        start = date(today.year, today.month, 1)
        label = today.strftime("%B %Y")
        return start, today, label

    if "last 30 days" in query_lower or "past 30 days" in query_lower:
        return today - timedelta(days=30), today, "last 30 days"

    if "last week" in query_lower or "past week" in query_lower:
        return today - timedelta(days=7), today, "last 7 days"

    return None, None, None


def format_time_context(start: Optional[date], end: Optional[date], label: Optional[str]) -> str:
    if not start or not end:
        return ""
    start_str = start.strftime("%b %d, %Y")
    end_str = end.strftime("%b %d, %Y")
    if label:
        return f" for {label} ({start_str} to {end_str})"
    return f" from {start_str} to {end_str}"


def format_currency(amount: float) -> str:
    if abs(amount - round(amount)) < 0.01:
        return f"₹{amount:,.0f}"
    return f"₹{amount:,.2f}"


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    payload: ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (payload.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    query_lower, tokens = tokenize(query)
    intent = detect_intent(query_lower, tokens)

    if not intent:
        return ChatResponse(
            text=(
                "I can help with profit, revenue, best selling items, delivery performance, or risk score. "
                "Try asking: 'What is my total profit for the year?'"
            )
        )

    start, end, label = get_time_window(query_lower)
    time_context = format_time_context(start, end, label)

    filters = [Sale.owner_id == current_user.id]
    if start and end:
        filters.extend([Sale.order_date >= start, Sale.order_date <= end])

    total_rows = db.query(func.count(Sale.id)).filter(*filters).scalar() or 0
    if total_rows == 0:
        return ChatResponse(
            text=f"I could not find any sales data for your account{time_context}."
        )

    if intent == "profit":
        total_revenue = db.query(func.sum(Sale.unit_price * Sale.quantity)).filter(*filters).scalar() or 0
        total_cost = db.query(func.sum(Sale.unit_cost * Sale.quantity)).filter(*filters).scalar() or 0
        profit = total_revenue - total_cost
        highlight = format_currency(profit)
        return ChatResponse(
            text=f"Your total profit is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "profit_margin":
        total_revenue = db.query(func.sum(Sale.unit_price * Sale.quantity)).filter(*filters).scalar() or 0
        total_cost = db.query(func.sum(Sale.unit_cost * Sale.quantity)).filter(*filters).scalar() or 0
        if total_revenue <= 0:
            return ChatResponse(text=f"Profit margin is 0%{time_context}.")
        profit_margin = ((total_revenue - total_cost) / total_revenue) * 100
        highlight = f"{profit_margin:.1f}%"
        return ChatResponse(
            text=f"Your profit margin is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "revenue":
        total_revenue = db.query(func.sum(Sale.unit_price * Sale.quantity)).filter(*filters).scalar() or 0
        highlight = format_currency(total_revenue)
        return ChatResponse(
            text=f"Your total revenue is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "cost":
        total_cost = db.query(func.sum(Sale.unit_cost * Sale.quantity)).filter(*filters).scalar() or 0
        highlight = format_currency(total_cost)
        return ChatResponse(
            text=f"Your total cost is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "risk":
        avg_risk = db.query(func.avg(Sale.region_risk_score)).filter(*filters).scalar()
        avg_risk = float(avg_risk or 0)
        highlight = f"{avg_risk:.1f}/10"
        return ChatResponse(
            text=f"Your average risk score is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "delivery":
        delivered_filters = filters + [Sale.delivery_status == "Delivered"]
        total_delivered = db.query(func.count(Sale.id)).filter(*delivered_filters).scalar() or 0
        if total_delivered == 0:
            return ChatResponse(
                text=f"There are no delivered orders to calculate delivery performance{time_context}."
            )
        on_time = (
            db.query(func.count(Sale.id))
            .filter(*delivered_filters)
            .filter(Sale.actual_delivery_date <= Sale.promised_delivery_date)
            .scalar()
            or 0
        )
        rate = (on_time / total_delivered) * 100
        highlight = f"{rate:.1f}%"
        return ChatResponse(
            text=f"Your on-time delivery rate is {highlight}{time_context}.",
            highlight=highlight,
        )

    if intent == "best_seller":
        result = (
            db.query(
                Sale.product_name,
                func.count(Sale.id).label("order_count"),
                func.sum(Sale.quantity).label("total_qty"),
            )
            .filter(*filters)
            .group_by(Sale.product_name)
            .order_by(func.count(Sale.id).desc(), func.sum(Sale.quantity).desc())
            .first()
        )
        if not result:
            return ChatResponse(
                text=f"I could not find any sales data to determine a best seller{time_context}."
            )
        highlight = result.product_name
        return ChatResponse(
            text=f"Your best selling item is {highlight} ({result.order_count} orders){time_context}.",
            highlight=highlight,
        )

    return ChatResponse(text="I could not process that request.")
