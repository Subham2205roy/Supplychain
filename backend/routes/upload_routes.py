from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database.database import get_db, SessionLocal # Import SessionLocal for background tasks
from backend.models.sales_model import Sale
from backend.routes.auth_routes import get_current_user
from backend.models.user_model import User
from dateutil import parser

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

# Simple task tracker (In-memory for now, Reset on restart)
UPLOAD_STATUS = {}

def process_csv_background(company_id: int, user_id: int, contents: bytes, mode: str, task_id: str):
    """Heavy CSV processing logic moved to background."""
    db = SessionLocal()
    try:
        if mode == "replace":
            db.query(Sale).filter(Sale.company_id == company_id).delete()
            order_map = {}
        else:
            existing_orders = db.query(Sale).filter(Sale.company_id == company_id).all()
            order_map = {o.order_id: o for o in existing_orders}

        buffer = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.DictReader(buffer)
        
        COLUMN_MAPPING = {
            'order_id': ['order_id', 'id', 'order id', 'order no', 'orderno'],
            'product_name': ['product_name', 'product', 'item', 'item_name', 'product name'],
            'category': ['category', 'type', 'product_category', 'group'],
            'quantity': ['quantity', 'qty', 'amount', 'units'],
            'unit_price': ['unit_price', 'price', 'sell_price', 'unit price'],
            'unit_cost': ['unit_cost', 'cost', 'base_cost', 'unit cost'],
            'order_date': ['order_date', 'date', 'order date'],
            'promised_delivery_date': ['promised_delivery_date', 'due_date', 'promised date', 'expected_delivery'],
            'actual_delivery_date': ['actual_delivery_date', 'delivery_date', 'actual date', 'delivered_at'],
            'delivery_status': ['delivery_status', 'status', 'shipping_status', 'delivery status'],
            'country': ['country', 'location', 'region', 'nation'],
            'region_risk_score': ['region_risk_score', 'risk', 'risk_score', 'region risk']
        }

        def get_value(row, field_name, default=None):
            for alias in COLUMN_MAPPING.get(field_name, [field_name]):
                for key in row.keys():
                    if key.lower().strip() == alias.lower():
                        val = row[key]
                        return val.strip() if val else default
            return default

        def safe_float(val, default=0.0):
            try: return float(val) if val is not None else default
            except: return default

        def safe_int(val, default=0):
            try: return int(float(val)) if val is not None else default
            except: return default

        def safe_date(val, default=None):
            if not val or not val.strip(): return default
            try: return parser.parse(val).date()
            except: return default

        updated_count = 0
        created_count = 0
        
        for row in csv_reader:
            order_id = get_value(row, 'order_id')
            if not order_id:
                order_id = f"UNK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{created_count + updated_count}"

            actual_delivery = safe_date(get_value(row, 'actual_delivery_date'))
            
            if order_id in order_map:
                sale_obj = order_map[order_id]
                sale_obj.product_name = get_value(row, 'product_name', sale_obj.product_name)
                sale_obj.category = get_value(row, 'category', sale_obj.category)
                sale_obj.quantity = safe_int(get_value(row, 'quantity'), sale_obj.quantity)
                sale_obj.unit_price = safe_float(get_value(row, 'unit_price'), sale_obj.unit_price)
                sale_obj.unit_cost = safe_float(get_value(row, 'unit_cost'), sale_obj.unit_cost)
                sale_obj.order_date = safe_date(get_value(row, 'order_date'), sale_obj.order_date)
                sale_obj.promised_delivery_date = safe_date(get_value(row, 'promised_delivery_date'), sale_obj.promised_delivery_date)
                sale_obj.actual_delivery_date = actual_delivery if actual_delivery else sale_obj.actual_delivery_date
                sale_obj.delivery_status = get_value(row, 'delivery_status', sale_obj.delivery_status)
                sale_obj.country = get_value(row, 'country', sale_obj.country)
                sale_obj.region_risk_score = safe_float(get_value(row, 'region_risk_score'), sale_obj.region_risk_score)
                updated_count += 1
            else:
                new_record = Sale(
                    company_id=company_id,
                    owner_id=user_id,
                    order_id=order_id,
                    product_name=get_value(row, 'product_name', 'Unknown Product'),
                    category=get_value(row, 'category', 'General'),
                    quantity=safe_int(get_value(row, 'quantity'), 1),
                    unit_price=safe_float(get_value(row, 'unit_price')),
                    unit_cost=safe_float(get_value(row, 'unit_cost')),
                    order_date=safe_date(get_value(row, 'order_date'), datetime.date.today()),
                    promised_delivery_date=safe_date(get_value(row, 'promised_delivery_date'), datetime.date.today() + datetime.timedelta(days=7)),
                    actual_delivery_date=actual_delivery,
                    delivery_status=get_value(row, 'delivery_status', 'Pending'),
                    country=get_value(row, 'country', 'Global'),
                    region_risk_score=safe_float(get_value(row, 'region_risk_score'), 5.0)
                )
                db.add(new_record)
                created_count += 1
        
        db.commit()
        UPLOAD_STATUS[task_id] = {
            "status": "completed",
            "message": f"Sync Complete: {created_count} new records, {updated_count} updated."
        }
    except Exception as e:
        db.rollback()
        UPLOAD_STATUS[task_id] = {"status": "failed", "message": str(e)}
    finally:
        db.close()

@router.post("/csv")
def upload_unified_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = "upsert",
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    task_id = f"task_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
    UPLOAD_STATUS[task_id] = {"status": "processing", "message": "File reading..."}

    try:
        contents = file.file.read()
        background_tasks.add_task(
            process_csv_background, 
            current_user.company_id, 
            current_user.id, 
            contents, 
            mode, 
            task_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initial read error: {str(e)}")
    finally:
        file.file.close()

    return {
        "message": "File received and processing started in background.",
        "task_id": task_id,
        "status": "processing"
    }

@router.get("/status/{task_id}")
def get_upload_status(task_id: str):
    """Endpoint to check background task status."""
    return UPLOAD_STATUS.get(task_id, {"status": "not_found"})
