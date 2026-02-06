import csv
import io
import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.models.sales_model import Sale
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User
from dateutil import parser # Requires: pip install python-dateutil

# Create the router for upload-related endpoints
router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

@router.post("/csv")
def upload_unified_csv(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Processes a unified CSV file to fully update the sales database.
    This function replaces all existing data with the data from the new file.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        # --- 1. Replace Logic: Delete all old records ---
        db.query(Sale).filter(Sale.company_id == current_user.company_id).delete()

        # --- 2. Read and Process the new CSV file ---
        contents = file.file.read()
        buffer = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.DictReader(buffer)
        
        records_to_add = []
        for row in csv_reader:
            # Handle potentially blank actual_delivery_date
            actual_delivery = None
            if row.get('actual_delivery_date') and row['actual_delivery_date'].strip():
                actual_delivery = parser.parse(row['actual_delivery_date']).date()

            new_record = Sale(
                company_id=current_user.company_id,
                owner_id=current_user.id,
                order_id=row['order_id'],
                product_name=row['product_name'],
                category=row['category'],
                quantity=int(row['quantity']),
                unit_price=float(row['unit_price']),
                unit_cost=float(row['unit_cost']),
                order_date=parser.parse(row['order_date']).date(),
                promised_delivery_date=parser.parse(row['promised_delivery_date']).date(),
                actual_delivery_date=actual_delivery,
                delivery_status=row['delivery_status'],
                country=row['country'],
                region_risk_score=float(row['region_risk_score'])
            )
            records_to_add.append(new_record)
        
        # --- 3. Save all new records to the database ---
        db.bulk_save_objects(records_to_add)
        db.commit()
        
    except Exception as e:
        db.rollback()
        # Provide a more detailed error message for easier debugging
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {e}. Check your CSV columns and data formats."
        )
    finally:
        file.file.close()

    return {
        "message": f"Successfully processed {len(records_to_add)} records."
    }
