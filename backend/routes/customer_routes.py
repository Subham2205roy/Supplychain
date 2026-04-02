from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import csv
import io

from backend.database.database import get_db
from backend.models.customer_model import Customer
from backend.models.user_model import User
from backend.routes.auth_routes import get_current_user
from backend import schemas
from backend.models.activity_model import Notification

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/")
def create_customer(
    payload: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = Customer(
        company_id=current_user.company_id,
        **payload.model_dump(),
    )
    db.add(customer)
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        company_id=current_user.company_id,
        title="New Customer Onboarded",
        message=f"Customer '{customer.name}' has been added to your portfolio.",
        type="Info"
    )
    db.add(notification)
    
    db.commit()
    db.refresh(customer)
    return _to_dict(customer)


@router.get("/")
def list_customers(
    search: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Customer).filter(Customer.company_id == current_user.company_id)
    if search:
        q = q.filter(Customer.name.ilike(f"%{search}%"))
    if segment:
        q = q.filter(Customer.segment == segment)
    return [_to_dict(c) for c in q.order_by(Customer.name).all()]


@router.get("/export/csv")
def export_customers_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(Customer)
        .filter(Customer.company_id == current_user.company_id)
        .order_by(Customer.name)
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone", "Address", "Segment", "Total Orders", "Total Revenue", "Notes"])
    for c in items:
        writer.writerow([c.name, c.email, c.phone, c.address, c.segment, c.total_orders, c.total_revenue, c.notes])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=customers_{date.today()}.csv"},
    )


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = _get_or_404(db, customer_id, current_user.company_id)
    return _to_dict(c)


@router.put("/{customer_id}")
def update_customer(
    customer_id: int,
    payload: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = _get_or_404(db, customer_id, current_user.company_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return _to_dict(c)


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = _get_or_404(db, customer_id, current_user.company_id)
    name = c.name
    db.delete(c)
    db.commit()
    return {"message": f"Customer '{name}' deleted."}


# ---------- helpers ----------

def _get_or_404(db: Session, cid: int, company_id: int) -> Customer:
    c = db.query(Customer).filter(Customer.id == cid, Customer.company_id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return c


def _to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address,
        "segment": c.segment,
        "total_orders": c.total_orders,
        "total_revenue": c.total_revenue,
        "notes": c.notes,
        "created_at": str(c.created_at) if c.created_at else None,
    }
