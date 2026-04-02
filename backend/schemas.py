from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

# ===========================
# 🔐 AUTHENTICATION SCHEMAS
# ===========================

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: int
    company_id: Optional[int] = None
    
    class Config:
        from_attributes = True  # Pydantic V2 replacement for orm_mode

# ===========================
# 📊 SALES SCHEMAS
# ===========================

class SaleBase(BaseModel):
    order_id: str
    product_name: str
    category: str
    quantity: int
    unit_price: float
    unit_cost: float
    order_date: Optional[date] = None
    country: str
    region_risk_score: float

class SaleCreate(SaleBase):
    pass

class SaleUpdate(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    delivery_status: Optional[str] = None

class Sale(SaleBase):
    id: int
    owner_id: Optional[int] = None  # Added this for SaaS feature
    company_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# ===========================
# 📦 INVENTORY SCHEMAS
# ===========================

class InventoryBase(BaseModel):
    product_name: str
    stock_level: int
    reorder_point: int

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    stock_level: Optional[int] = None
    reorder_point: Optional[int] = None

class Inventory(InventoryBase):
    id: int
    company_id: int
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# ===========================
# 🧩 TEAM INVITE SCHEMAS
# ===========================

class TeamInviteCreate(BaseModel):
    invited_email: EmailStr

class TeamInviteAccept(BaseModel):
    token: str

class TeamInviteResponse(BaseModel):
    id: int
    company_id: int
    invited_email: EmailStr
    token: str
    status: str

    class Config:
        from_attributes = True

# ===========================
# 🔄 BULK OPERATIONS SCHEMAS
# ===========================

class BulkStatusUpdate(BaseModel):
    order_ids: List[int]
    new_status: str

# ===========================
# 📦 INVENTORY ADJUSTMENT
# ===========================

class InventoryStockAdjust(BaseModel):
    adjustment: int  # positive = add, negative = remove
    reason: str = "Manual adjustment"

# ===========================
# 🏭 SUPPLIER SCHEMAS
# ===========================

class SupplierBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    lead_time_days: int = 7
    reliability_score: float = 5.0
    notes: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    notes: Optional[str] = None

# ===========================
# 👥 CUSTOMER SCHEMAS
# ===========================

class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    segment: str = "Regular"
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    segment: Optional[str] = None
    notes: Optional[str] = None

# ===========================
# 🤖 AUTOMATION SCHEMAS
# ===========================

class AutomationRequestOTP(BaseModel):
    sender_email: EmailStr

class AutomationVerifyOTP(BaseModel):
    sender_email: EmailStr
    otp_code: str
    duration_days: int = 30  # Default 30 days

class AutomationResponse(BaseModel):
    id: int
    user_id: int
    sender_email: EmailStr
    is_verified: bool
    expires_at: Optional[date] = None
    created_at: date


# ===========================
# 💰 FINANCE SCHEMAS
# ===========================

class InvoiceBase(BaseModel):
    invoice_number: Optional[str] = None
    order_id: str
    customer_name: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: str = "Unpaid"
    due_date: date

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    payment_date: Optional[date] = None

class Invoice(InvoiceBase):
    id: int
    company_id: int
    payment_date: Optional[date] = None

    class Config:
        from_attributes = True

# ===========================
# 🚚 LOGISTICS SCHEMAS
# ===========================

class ShipmentBase(BaseModel):
    order_id: str
    tracking_number: Optional[str] = None
    carrier: str
    shipping_method: Optional[str] = None
    estimated_delivery: date

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentUpdate(BaseModel):
    actual_delivery: Optional[date] = None
    status: Optional[str] = None

class Shipment(ShipmentBase):
    id: int
    company_id: int
    actual_delivery: Optional[date] = None
    status: str

    class Config:
        from_attributes = True

class ReturnBase(BaseModel):
    order_id: str
    reason: str
    condition: str

class ReturnCreate(ReturnBase):
    pass

class ReturnUpdate(BaseModel):
    refund_status: Optional[str] = None

class Return(ReturnBase):
    id: int
    company_id: int
    refund_status: str

    class Config:
        from_attributes = True

# ===========================
# 🔔 ACTIVITY & LOGS SCHEMAS
# ===========================

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str

class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ActivityLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    details: Optional[str] = None

class ActivityLog(ActivityLogBase):
    id: int
    user_id: int
    created_at: date

    class Config:
        from_attributes = True
