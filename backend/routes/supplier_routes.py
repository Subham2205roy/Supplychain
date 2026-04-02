from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import csv
import io

from backend.database.database import get_db
from backend.models.supplier_model import Supplier
from backend.models.user_model import User
from backend.routes.auth_routes import get_current_user
from backend import schemas
from backend.models.activity_model import Notification

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/")
def create_supplier(
    payload: schemas.SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = Supplier(
        company_id=current_user.company_id,
        **payload.model_dump(),
    )
    db.add(supplier)
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        company_id=current_user.company_id,
        title="New Supplier Added",
        message=f"Supplier '{supplier.name}' has been added to your network.",
        type="Info"
    )
    db.add(notification)
    
    db.commit()
    db.refresh(supplier)
    return _to_dict(supplier)


@router.get("/")
def list_suppliers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Supplier).filter(Supplier.company_id == current_user.company_id)
    if search:
        q = q.filter(Supplier.name.ilike(f"%{search}%"))
    return [_to_dict(s) for s in q.order_by(Supplier.name).all()]


@router.get("/export/csv")
def export_suppliers_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(Supplier)
        .filter(Supplier.company_id == current_user.company_id)
        .order_by(Supplier.name)
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Contact", "Email", "Phone", "Country", "Lead Time (days)", "Reliability", "Notes"])
    for s in items:
        writer.writerow([s.name, s.contact_name, s.email, s.phone, s.country, s.lead_time_days, s.reliability_score, s.notes])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=suppliers_{date.today()}.csv"},
    )


@router.get("/{supplier_id}")
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_404(db, supplier_id, current_user.company_id)
    return _to_dict(s)


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    payload: schemas.SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_404(db, supplier_id, current_user.company_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _to_dict(s)


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_404(db, supplier_id, current_user.company_id)
    name = s.name
    db.delete(s)
    db.commit()
    return {"message": f"Supplier '{name}' deleted."}


# ---------- helpers ----------

def _get_or_404(db: Session, sid: int, company_id: int) -> Supplier:
    s = db.query(Supplier).filter(Supplier.id == sid, Supplier.company_id == company_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return s


def _to_dict(s: Supplier) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "contact_name": s.contact_name,
        "email": s.email,
        "phone": s.phone,
        "country": s.country,
        "lead_time_days": s.lead_time_days,
        "reliability_score": s.reliability_score,
        "notes": s.notes,
        "created_at": str(s.created_at) if s.created_at else None,
    }
