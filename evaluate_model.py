import joblib
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR / "backend" / "ml"
DATA_PATH = ML_DIR / "real_startup_data.csv"
MODEL_PATH = ML_DIR / "business_success_model.joblib"
ENCODER_PATH = ML_DIR / "industry_encoder.joblib"

# Helpers (mirror train_model.py)
def clean_money(val):
    try:
        if isinstance(val, str):
            val = val.replace(",", "").replace("-", "").strip()
            return float(val) if val else 0
        return float(val)
    except Exception:
        return 0


def map_industry(cat: str) -> str:
    cat = str(cat).lower()
    if any(x in cat for x in ["software", "web", "mobile", "app", "games", "video", "biotech", "network"]):
        return "Technology"
    if any(x in cat for x in ["ecommerce", "advertising", "sales", "pr", "search", "fashion"]):
        return "Retail"
    if any(x in cat for x in ["clean", "manufactur", "hardware", "semiconductor", "auto"]):
        return "Manufacturing"
    if any(x in cat for x in ["consulting", "enterprise", "education", "analytics", "finance", "service"]):
        return "Services"
    if any(x in cat for x in ["hospitality", "music", "food", "beverage", "restaurant"]):
        return "Food / Restaurant"
    return "Other"


print("Loading dataset...")
try:
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
except UnicodeDecodeError:
    df = pd.read_csv(DATA_PATH, encoding="ISO-8859-1")

# Basic cleaning to match training pipeline
df.columns = df.columns.str.strip()
df = df[df["status"].isin(["acquired", "closed"])].copy()
df["success"] = df["status"].apply(lambda x: 1 if x == "acquired" else 0)
df["capital"] = df["funding_total_usd"].apply(clean_money)
df = df[df["capital"] > 0]
df["industry"] = df["market"].apply(map_industry)
df = df[df["industry"] != "Other"]

industry_counts = df["industry"].value_counts()
max_count = industry_counts.max()
df["competition"] = df["industry"].apply(
    lambda ind: int((industry_counts.get(ind, 0) / max_count) * 10) if max_count else 0
)
funding_rounds = pd.to_numeric(df["funding_rounds"], errors="coerce").fillna(0)
df["experience"] = funding_rounds.apply(lambda r: 5 if r >= 4 else (2 if r >= 2 else 0))
success_rates = df.groupby("industry")["success"].mean()
df["market_size"] = df["industry"].apply(lambda ind: int(success_rates.get(ind, 0.5) * 100000))

print("Loading encoder & model...")
encoder = joblib.load(ENCODER_PATH)
df["industry_encoded"] = encoder.transform(df["industry"])
model = joblib.load(MODEL_PATH)

# Features/target
X = df[["industry_encoded", "market_size", "competition", "capital", "experience"]]
y = df["success"]

print("Predicting...")
pred = model.predict(X)

print("\nClassification Metrics:\n")
print(f"Accuracy : {accuracy_score(y, pred):.4f}")
print(f"Precision: {precision_score(y, pred, average='weighted', zero_division=0):.4f}")
print(f"Recall   : {recall_score(y, pred, average='weighted', zero_division=0):.4f}")
print(f"F1 Score : {f1_score(y, pred, average='weighted', zero_division=0):.4f}")
print("\nConfusion Matrix [[TN, FP], [FN, TP]]:")
print(confusion_matrix(y, pred))

print("\nEvaluation completed successfully.")
