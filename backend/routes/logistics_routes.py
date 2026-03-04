from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import random
import string

from backend.database.database import get_db
from backend import schemas
from backend.models.logistics_model import Shipment, Return
from backend.models.activity_model import ActivityLog
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User

router = APIRouter(
    prefix="/api/logistics",
    tags=["Logistics"]
)

# --- SHIPMENTS ---

@router.get("/shipments", response_model=List[schemas.Shipment])
def get_shipments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Shipment).filter(Shipment.company_id == current_user.company_id).all()

@router.post("/shipments", response_model=schemas.Shipment)
def create_shipment(
    shipment: schemas.ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment_data = shipment.model_dump()
    if not shipment_data.get("tracking_number"):
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        shipment_data["tracking_number"] = f"TN-{random_suffix}"
    
    db_shipment = Shipment(**shipment_data)
    db_shipment.company_id = current_user.company_id
    
    db.add(db_shipment)
    
    log = ActivityLog(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="Created Shipment",
        entity_type="Shipment",
        entity_id=db_shipment.tracking_number,
        details=f"Shipment for Order {shipment.order_id} via {shipment.carrier}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@router.patch("/shipments/{shipment_id}", response_model=schemas.Shipment)
def update_shipment(
    shipment_id: int,
    shipment_update: schemas.ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.company_id == current_user.company_id
    ).first()
    
    if not db_shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
        
    update_data = shipment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_shipment, key, value)
        
    log = ActivityLog(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="Updated Shipment",
        entity_type="Shipment",
        entity_id=db_shipment.tracking_number,
        details=f"Status: {db_shipment.status}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

# --- RETURNS ---

@router.get("/returns", response_model=List[schemas.Return])
def get_returns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Return).filter(Return.company_id == current_user.company_id).all()

@router.post("/returns", response_model=schemas.Return)
def create_return(
    ret: schemas.ReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_return = Return(**ret.model_dump())
    db_return.company_id = current_user.company_id
    
    db.add(db_return)
    
    log = ActivityLog(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="Processed Return",
        entity_type="Return",
        entity_id=ret.order_id,
        details=f"Reason: {ret.reason}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(db_return)
    return db_return
