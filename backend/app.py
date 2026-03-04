import os
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from backend.limiter import limiter

# 1. Imports
from backend.routes.auth_routes import router as auth_router
from backend.routes import main_routes, sales_routes, upload_routes
from backend.routes import team_routes, ai_routes
from backend.routes import inventory_routes
from backend.routes import supplier_routes, customer_routes
from backend.routes.google_auth_routes import router as google_auth_router
from backend.routes import forecasting_routes, alert_routes, automation_routes, finance_routes, logistics_routes, activity_routes
load_dotenv()



# Business idea validation keywords
_BUSINESS_KEYWORDS = {
    "shop", "store", "market", "retail", "wholesale", "logistics", "supply",
    "chain", "inventory", "warehouse", "delivery", "shipping", "transport",
    "manufacturing", "factory", "production", "service", "services", "saas",
    "software", "platform", "b2b", "b2c", "subscription", "restaurant",
    "food", "cafe", "grocery", "pharmacy", "health", "medical", "device",
    "ecommerce", "commerce", "online", "app", "marketplace", "trading",
    "export", "import", "procurement", "sourcing", "logistic"
}


def _validate_business_text(text: str) -> str:
    idea_text = (text or "").strip()
    words = re.findall(r"[A-Za-z]{3,}", idea_text.lower())
    if len(idea_text) < 15 or len(words) < 3:
        raise HTTPException(status_code=400, detail="Please describe the business in a short sentence (at least 3 real words).")
    if not any(k in idea_text.lower() for k in _BUSINESS_KEYWORDS):
        raise HTTPException(status_code=400, detail="Mention a business/commerce term (e.g., logistics, retail, store, platform).")
    return idea_text

# 2. CREATE THE APP
app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down and try again later.", "error": "Rate limit exceeded"}
    )

# 3. ATTACH ROUTERS
app.include_router(auth_router)
app.include_router(main_routes.router)
app.include_router(sales_routes.router)
app.include_router(upload_routes.router)
app.include_router(team_routes.router)
app.include_router(ai_routes.router)
app.include_router(inventory_routes.router)
app.include_router(supplier_routes.router)
app.include_router(customer_routes.router)
app.include_router(google_auth_router)
app.include_router(forecasting_routes.router)
app.include_router(alert_routes.router)
app.include_router(automation_routes.router)
app.include_router(finance_routes.router)
app.include_router(logistics_routes.router)
app.include_router(activity_routes.router)

# --- ML LOGIC IMPORT ---
try:
    from backend.ml.predict import predict_business_success
    model_available = True
except ImportError:
    print("⚠️ Warning: Could not import ML model. Running in logic-fallback mode.")
    model_available = False

# --- Middleware ---
ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
from slowapi.middleware import SlowAPIMiddleware

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files Setup ---
# This makes sure the server knows where your HTML/CSS/JS files are
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ==========================================
# 👇 UPDATED ROUTING LOGIC STARTS HERE 👇
# ==========================================

# 1. Root Endpoint -> SHOW LOGIN PAGE
@app.get("/")
def read_root():
    # When user visits http://127.0.0.1:8000/, show Login
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))

# 2. Dashboard Endpoint -> SHOW MAIN APP
@app.get("/dashboard")
def read_dashboard():
    # When user is redirected to http://127.0.0.1:8000/dashboard, show App
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# ==========================================
# 👆 UPDATED ROUTING LOGIC ENDS HERE 👆
# ==========================================

# --- DATA MODEL ---
class BusinessInput(BaseModel):
    industry: str
    market_demand: int
    competition: int
    capital_range: str
    experience: int
    idea: str

# --- AI ENDPOINT ---
@app.post("/ai/business-viability")
def business_viability(data: BusinessInput):
    idea_text = _validate_business_text(data.idea)
    
    # 1. Convert Capital Range -> Real Money
    if data.capital_range == "High":
        real_capital = 100000
        est_cost = "$80,000 - $150,000"
    elif data.capital_range == "Medium":
        real_capital = 50000
        est_cost = "$30,000 - $60,000"
    else:
        real_capital = 10000
        est_cost = "$5,000 - $15,000"

    # 2. Convert Market Demand -> Estimated Market Size
    real_market_size = data.market_demand * 10000

    # 3. ML Prediction Logic
    viability_score = 50

    if model_available:
        try:
            probability = predict_business_success(
                industry=data.industry,
                market_size=real_market_size,
                competition=data.competition,
                capital=real_capital,
                experience=data.experience
            )
            viability_score = int(probability * 100)
            model_used = "Random Forest Classifier"
        except Exception as e:
            print(f"❌ Model Error: {e}")
            model_used = "Rule-Based Logic (Fallback)"
            viability_score = 60 + (data.market_demand * 3) - (data.competition * 2)
    else:
        model_used = "Rule-Based Logic"
        viability_score = 60 + (data.market_demand * 3) - (data.competition * 2)

    viability_score = max(10, min(99, viability_score))

    # 4. Generate Report
    if viability_score >= 75:
        risk = "Low"
        breakdown = f"Excellent Potential. Our {model_used} predicts high success ({viability_score}%) driven by strong market demand in the {data.industry} sector."
    elif viability_score >= 50:
        risk = "Medium"
        breakdown = f"Moderate Viability. The {model_used} suggests a {viability_score}% success rate. Competition is the main risk factor here."
    else:
        risk = "High"
        breakdown = f"High Risk Detected. Our model predicts only {viability_score}% success. The capital provided ({data.capital_range}) may be insufficient for this competition level."

    # 5. Financial Projections
    growth_rate = 1.15 + (viability_score / 400)
    base_revenue = real_capital * 0.5

    revenue_curve = [
        int(base_revenue * (growth_rate ** i)) for i in range(1, 6)
    ]

    return {
        "viability_score": viability_score,
        "risk_level": risk,
        "breakdown": breakdown,
        "projections": {
            "estimated_cost": est_cost,
            "revenue_curve": revenue_curve
        },
        "competition": data.competition,
        "market_demand": data.market_demand,
        "experience": data.experience,
        "model_used": model_used
    }
