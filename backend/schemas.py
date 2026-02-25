from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

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
    last_updated: Optional[date] = None

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
