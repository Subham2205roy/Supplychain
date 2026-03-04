from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import csv
import io

# --- IMPORTS ---
from backend.database.database import get_db
from backend import schemas
from backend.models.sales_model import Sale
from sqlalchemy import extract, func, or_

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
    current_user: User = Depends(get_current_user)
):
    db_sale = (
        db.query(Sale)
        .filter(Sale.order_id == sale.order_id, Sale.company_id == current_user.company_id)
        .first()
    )
    if db_sale:
        raise HTTPException(status_code=400, detail=f"Order ID '{sale.order_id}' already exists.")
        
    new_sale = Sale(**sale.model_dump())
    new_sale.company_id = current_user.company_id
    new_sale.owner_id = current_user.id
    
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
    current_user: User = Depends(get_current_user)
):
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
        .filter(Sale.order_date >= six_months_ago)
        .filter(Sale.company_id == current_user.company_id) 
        .group_by('month')
        .order_by('month')
        .all()
    )

    labels = [r.month for r in results]
    data = [r.total_revenue for r in results]

    return {"labels": labels, "data": data}


# =============================================
# 7. SEARCH / FILTER / PAGINATE (Phase 1 New)
# =============================================
@router.get("/search/orders")
def search_orders(
    search: Optional[str] = Query(None, description="Search by product name or order ID"),
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    sort_by: Optional[str] = Query("order_date", description="Sort field"),
    sort_dir: Optional[str] = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Sale).filter(Sale.company_id == current_user.company_id)

    # Search filter
    if search:
        query = query.filter(
            or_(
                Sale.product_name.ilike(f"%{search}%"),
                Sale.order_id.ilike(f"%{search}%"),
                Sale.category.ilike(f"%{search}%"),
            )
        )

    # Status filter
    if status:
        query = query.filter(Sale.delivery_status == status)

    # Date range filter
    if date_from:
        try:
            d_from = datetime.date.fromisoformat(date_from)
            query = query.filter(Sale.order_date >= d_from)
        except ValueError:
            pass
    if date_to:
        try:
            d_to = datetime.date.fromisoformat(date_to)
            query = query.filter(Sale.order_date <= d_to)
        except ValueError:
            pass

    # Total count before pagination
    total = query.count()

    # Sorting
    sort_column = getattr(Sale, sort_by, Sale.order_date)
    if sort_dir == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    offset = (page - 1) * page_size
    orders = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "orders": [
            {
                "id": o.id,
                "order_id": o.order_id,
                "product_name": o.product_name,
                "category": o.category,
                "quantity": o.quantity,
                "unit_price": o.unit_price,
                "unit_cost": o.unit_cost,
                "order_date": str(o.order_date) if o.order_date else None,
                "promised_delivery_date": str(o.promised_delivery_date) if o.promised_delivery_date else None,
                "actual_delivery_date": str(o.actual_delivery_date) if o.actual_delivery_date else None,
                "delivery_status": o.delivery_status,
                "country": o.country,
                "region_risk_score": o.region_risk_score,
            }
            for o in orders
        ],
    }


# =============================================
# 8. BULK STATUS UPDATE (Phase 1 New)
# =============================================
@router.put("/bulk-status")
def bulk_update_status(
    payload: schemas.BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_statuses = {"Pending", "Shipped", "Delivered", "Cancelled"}
    if payload.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    updated = (
        db.query(Sale)
        .filter(Sale.id.in_(payload.order_ids), Sale.company_id == current_user.company_id)
        .update({Sale.delivery_status: payload.new_status}, synchronize_session="fetch")
    )
    db.commit()

    return {"message": f"{updated} order(s) updated to '{payload.new_status}'."}


# =============================================
# 9. EXPORT CSV (Phase 1 New)
# =============================================
@router.get("/export/csv")
def export_sales_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sales = (
        db.query(Sale)
        .filter(Sale.company_id == current_user.company_id)
        .order_by(Sale.order_date.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "Product Name", "Category", "Quantity",
        "Unit Price", "Unit Cost", "Order Date", "Promised Delivery",
        "Actual Delivery", "Status", "Country", "Risk Score",
    ])

    for s in sales:
        writer.writerow([
            s.order_id, s.product_name, s.category, s.quantity,
            s.unit_price, s.unit_cost, s.order_date,
            s.promised_delivery_date, s.actual_delivery_date,
            s.delivery_status, s.country, s.region_risk_score,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=orders_{datetime.date.today()}.csv"
        },
    )
