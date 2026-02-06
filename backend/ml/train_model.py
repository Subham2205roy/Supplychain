import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(__file__)
# Ensure you renamed your file to this!
CSV_PATH = os.path.join(BASE_DIR, "real_startup_data.csv") 
MODEL_PATH = os.path.join(BASE_DIR, "business_success_model.joblib")
ENCODER_PATH = os.path.join(BASE_DIR, "industry_encoder.joblib")

print("🚀 Loading Production Dataset (investments_VC.csv)...")

if not os.path.exists(CSV_PATH):
    print(f"❌ Error: {CSV_PATH} not found.")
    print("   Please rename your downloaded file to 'real_startup_data.csv' and put it in backend/ml/")
    exit()

# 1. Load Data (Handle encoding issues common with this dataset)
try:
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(CSV_PATH, encoding='ISO-8859-1')

print(f"   Raw Data Loaded: {len(df)} rows")

# --- DATA CLEANING (The "White Glove" Service) ---

# A. Fix Column Names (Your file has spaces like ' market ' and ' funding_total_usd ')
df.columns = df.columns.str.strip() 

# B. Clean 'status' to Target (1 = Success, 0 = Fail)
# Filter: We only learn from companies that definitely won (acquired) or lost (closed)
df = df[df['status'].isin(['acquired', 'closed'])]
df['success'] = df['status'].apply(lambda x: 1 if x == 'acquired' else 0)

# C. Clean 'funding_total_usd' (Remove commas, handle dashes)
# Turn " 1,234,567 " -> 1234567
def clean_money(val):
    try:
        if isinstance(val, str):
            val = val.replace(',', '').replace('-', '').strip()
            return float(val) if val else 0
        return float(val)
    except:
        return 0

df['capital'] = df['funding_total_usd'].apply(clean_money)
# Remove rows with 0 capital (bad data)
df = df[df['capital'] > 0]

# D. Map 'market' to YOUR 5 Industries
# This aligns the 500+ Kaggle markets to your Dashboard's 5 dropdowns
def map_industry(cat):
    cat = str(cat).lower()
    if any(x in cat for x in ['software', 'web', 'mobile', 'app', 'games', 'video', 'biotech', 'network']):
        return 'Technology'
    elif any(x in cat for x in ['ecommerce', 'advertising', 'sales', 'pr', 'search', 'fashion']):
        return 'Retail'
    elif any(x in cat for x in ['clean', 'manufactur', 'hardware', 'semiconductor', 'auto']):
        return 'Manufacturing'
    elif any(x in cat for x in ['consulting', 'enterprise', 'education', 'analytics', 'finance', 'service']):
        return 'Services'
    elif any(x in cat for x in ['hospitality', 'music', 'food', 'beverage', 'restaurant']):
        return 'Food / Restaurant'
    else:
        return 'Other'

df['industry'] = df['market'].apply(map_industry)
df = df[df['industry'] != 'Other'] # Only train on relevant industries

# E. Create 'Competition' Feature
# Logic: Crowded markets in the dataset = High Competition
industry_counts = df['industry'].value_counts()
max_count = industry_counts.max()

def calculate_competition(industry):
    count = industry_counts.get(industry, 0)
    return int((count / max_count) * 10)

df['competition'] = df['industry'].apply(calculate_competition)

# F. Map 'funding_rounds' to 'Experience' (Proxy)
# More rounds = More vetted/experienced
def map_experience(rounds):
    if rounds >= 4: return 5 # Expert
    if rounds >= 2: return 2 # Intermediate
    return 0 # Beginner

df['experience'] = df['funding_rounds'].apply(map_experience)

# G. Simulate 'Market Size' 
# Logic: Higher success rate in the sector = Higher implied demand
success_rates = df.groupby('industry')['success'].mean()
def estimate_market_size(industry):
    rate = success_rates.get(industry, 0.5)
    return int(rate * 100000) 

df['market_size'] = df['industry'].apply(estimate_market_size)

# --- TRAINING ---

print(f"⚙️  Training on {len(df)} Cleaned & Verified Rows...")

# Encode Industry
encoder = LabelEncoder()
df['industry_encoded'] = encoder.fit_transform(df['industry'])

# Define Features (Must match your predict.py!)
X = df[['industry_encoded', 'market_size', 'competition', 'capital', 'experience']]
y = df['success']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
acc = accuracy_score(y_test, y_pred=model.predict(X_test))
print(f"✅ Accuracy on Real Data: {acc*100:.2f}%")

# Save
joblib.dump(model, MODEL_PATH)
joblib.dump(encoder, ENCODER_PATH)
print(f"💾 Saved real-world model to {MODEL_PATH}")