from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime

# --- IMPORTS ---
from backend.database.database import get_db
from backend import schemas
from backend.models.sales_model import Sale
from sqlalchemy import extract, func

# Import the security dependency to get the User ID
from backend.routes.auth_routes import get_current_user 
from backend.models.user_model import User
# --------------

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)

# 1. CREATE (Stamp the data with owner_id)
@router.post("/", response_model=schemas.Sale)
def create_sale(
    sale: schemas.SaleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- Security Check
):
    # Check if Order ID exists (Global check or User specific? Let's keep it Global for safety)
    db_sale = (
        db.query(Sale)
        .filter(Sale.order_id == sale.order_id, Sale.company_id == current_user.company_id)
        .first()
    )
    if db_sale:
        raise HTTPException(status_code=400, detail=f"Order ID '{sale.order_id}' already exists.")
        
    # Create the sale object
    new_sale = Sale(**sale.model_dump())
    
    # STAMP THE COMPANY + OWNER ID automatically
    new_sale.company_id = current_user.company_id
    new_sale.owner_id = current_user.id
    
    # Handle optional order_date
    if not new_sale.order_date:
        new_sale.order_date = datetime.date.today()

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale

# 2. READ (Filter data by owner_id)
@router.get("/", response_model=List[schemas.Sale])
def get_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- Security Check
):
    # ONLY return sales that belong to the logged-in user
    return db.query(Sale).filter(Sale.company_id == current_user.company_id).all()

# 3. READ SINGLE (Ensure user owns it)
@router.get("/{sale_id}", response_model=schemas.Sale)
def get_sale(
    sale_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.company_id == current_user.company_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found or you don't have permission")
    return sale

# 4. UPDATE (Ensure user owns it)
@router.put("/{sale_id}", response_model=schemas.Sale)
def update_sale(
    sale_id: int, 
    sale_update: schemas.SaleUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_sale = db.query(Sale).filter(Sale.id == sale_id, Sale.company_id == current_user.company_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    update_data = sale_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sale, key, value)
        
    db.commit()
    db.refresh(db_sale)
    return db_sale

# 5. DELETE (Ensure user owns it)
@router.delete("/{sale_id}", response_model=dict)
def delete_sale(
    sale_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.company_id == current_user.company_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    db.delete(sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

# 6. ANALYTICS (Filter by owner_id)
@router.get("/trend/revenue")
def get_sales_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    six_months_ago = datetime.date.today() - datetime.timedelta(days=180)

    results = (
        db.query(
            func.strftime("%Y-%m", Sale.order_date).label('month'),
            func.sum(Sale.unit_price * Sale.quantity).label('total_revenue')
        )
        # CRITICAL FIX: Only calculate revenue for THIS user
        .filter(Sale.order_date >= six_months_ago)
        .filter(Sale.company_id == current_user.company_id) 
        .group_by('month')
        .order_by('month')
        .all()
    )

    labels = [r.month for r in results]
    data = [r.total_revenue for r in results]

    return {"labels": labels, "data": data}
