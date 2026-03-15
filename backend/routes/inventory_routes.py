from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime
import csv
import io

from backend.database.database import get_db
from backend.models.inventory_model import Inventory
from backend.models.sales_model import Sale
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.routes.auth_routes import get_current_user
from backend import schemas
from backend.models.activity_model import Notification

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# 1. CREATE
@router.post("/", response_model=schemas.Inventory)
def create_inventory_item(
    item: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Inventory)
        .filter(
            Inventory.company_id == current_user.company_id,
            func.lower(Inventory.product_name) == item.product_name.lower(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product '{item.product_name}' already exists in inventory.",
        )

    new_item = Inventory(
        company_id=current_user.company_id,
        product_name=item.product_name,
        stock_level=item.stock_level,
        reorder_point=item.reorder_point,
    )
    db.add(new_item)
    
    # Create notification
    notification = Notification(
        user_id=current_user.id,
        company_id=current_user.company_id,
        title="New Inventory Item",
        message=f"Product '{new_item.product_name}' has been added to inventory.",
        type="Info"
    )
    db.add(notification)
    
    db.commit()
    db.refresh(new_item)
    return new_item


# 2. READ ALL (with optional search)
@router.get("/")
def get_inventory(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Inventory).filter(Inventory.company_id == current_user.company_id)

    if search:
        query = query.filter(Inventory.product_name.ilike(f"%{search}%"))

    items = query.order_by(Inventory.product_name).all()

    return [
        {
            "id": item.id,
            "product_name": item.product_name,
            "stock_level": item.stock_level,
            "reorder_point": item.reorder_point,
            "last_updated": item.last_updated,
        }
        for item in items
    ]


# 3. READ SINGLE
@router.get("/{item_id}")
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.id == item_id, Inventory.company_id == current_user.company_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")
    return {
        "id": item.id,
        "product_name": item.product_name,
        "stock_level": item.stock_level,
        "reorder_point": item.reorder_point,
        "last_updated": item.last_updated,
    }


# 4. UPDATE
@router.put("/{item_id}")
def update_inventory_item(
    item_id: int,
    update: schemas.InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.id == item_id, Inventory.company_id == current_user.company_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "product_name": item.product_name,
        "stock_level": item.stock_level,
        "reorder_point": item.reorder_point,
        "last_updated": item.last_updated,
    }


# 5. DELETE
@router.delete("/{item_id}")
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.id == item_id, Inventory.company_id == current_user.company_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    db.delete(item)
    db.commit()
    return {"message": f"'{item.product_name}' deleted from inventory."}


# 6. STOCK ADJUSTMENT
@router.post("/{item_id}/adjust")
def adjust_stock(
    item_id: int,
    payload: schemas.InventoryStockAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.id == item_id, Inventory.company_id == current_user.company_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found.")

    new_level = item.stock_level + payload.adjustment
    if new_level < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce stock below 0. Current: {item.stock_level}, Adjustment: {payload.adjustment}",
        )

    item.stock_level = new_level
    
    # Check for low stock notification
    if new_level <= item.reorder_point:
        notification = Notification(
            user_id=current_user.id,
            company_id=current_user.company_id,
            title="Low Stock Alert",
            message=f"Stock for '{item.product_name}' is at or below reorder point ({new_level}).",
            type="Warning"
        )
        db.add(notification)
        
    db.commit()
    db.refresh(item)

    return {
        "message": f"Stock adjusted by {payload.adjustment:+d}. New level: {new_level}",
        "product_name": item.product_name,
        "old_level": new_level - payload.adjustment,
        "new_level": new_level,
        "reason": payload.reason,
    }


# 7. EXPORT CSV
@router.get("/export/csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(Inventory)
        .filter(Inventory.company_id == current_user.company_id)
        .order_by(Inventory.product_name)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product Name", "Stock Level", "Reorder Point", "Last Updated"])

    for item in items:
        writer.writerow([
            item.product_name,
            item.stock_level,
            item.reorder_point,
            item.last_updated,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_{date.today()}.csv"},
    )
