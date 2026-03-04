from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import random
import string

from backend.database.database import get_db
from backend import schemas
from backend.models.invoice_model import Invoice
from backend.models.activity_model import ActivityLog
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User

router = APIRouter(
    prefix="/api/finance",
    tags=["Finance"]
)

@router.get("/invoices", response_model=List[schemas.Invoice])
def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Invoice).filter(Invoice.company_id == current_user.company_id).all()

@router.post("/invoices", response_model=schemas.Invoice)
def create_invoice(
    invoice: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice_data = invoice.model_dump()
    if not invoice_data.get("invoice_number"):
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        invoice_data["invoice_number"] = f"INV-{random_suffix}"
    
    db_invoice = Invoice(**invoice_data)
    db_invoice.company_id = current_user.company_id
    
    db.add(db_invoice)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="Created Invoice",
        entity_type="Invoice",
        entity_id=db_invoice.invoice_number,
        details=f"Invoice for {db_invoice.customer_name} of {db_invoice.amount} {db_invoice.currency}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.patch("/invoices/{invoice_id}", response_model=schemas.Invoice)
def update_invoice(
    invoice_id: int,
    invoice_update: schemas.InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id, 
        Invoice.company_id == current_user.company_id
    ).first()
    
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    update_data = invoice_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_invoice, key, value)
        
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="Updated Invoice",
        entity_type="Invoice",
        entity_id=db_invoice.invoice_number,
        details=f"Status changed to {invoice_update.status or db_invoice.status}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_invoice)
    return db_invoice
