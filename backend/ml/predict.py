import os
import joblib
import pandas as pd
import datetime
import logging

# Set up simple logging for ML events
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ML-Core")

# Define paths
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "business_success_model.joblib")
ENCODER_PATH = os.path.join(BASE_DIR, "industry_encoder.joblib")

# Model Metadata (Versioning)
MODEL_METADATA = {
    "version": "1.0.4-prod",
    "name": "SuccessPrediction-RF",
    "last_updated": "2026-02-23",
    "accuracy_baseline": 0.82
}

# Load assets only once when the file is imported
try:
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    logger.info(f"✅ ML Model [{MODEL_METADATA['name']} v{MODEL_METADATA['version']}] Loaded Successfully")
except Exception as e:
    logger.warning(f"⚠️ Error loading ML assets: {e}")
    model = None
    encoder = None

def predict_business_success(industry, market_size, competition, capital, experience):
    if model is None or encoder is None:
        return 0.5 

    logger.info(f"Prediction requested: industry={industry}, cap={capital}")

    # 1. Encode the Industry string (e.g., "Technology" -> 1)
    try:
        industry_encoded_val = encoder.transform([industry])[0]
    except ValueError:
        # Handle unseen labels (e.g., if user sends "Crypto" but model only knows "Tech")
        # We default to the first known class to prevent crashing
        industry_encoded_val = 0 
        logger.warning(f"Unseen industry '{industry}'. Defaulting to index 0.")

    # 2. Create DataFrame with EXACT feature names used in training
    # CRITICAL FIX: The key must be 'industry_encoded', NOT 'industry'
    input_data = pd.DataFrame([{
        'industry_encoded': industry_encoded_val,  # <--- THIS WAS THE CAUSE OF YOUR ERROR
        'market_size': market_size,
        'competition': competition,
        'capital': capital,
        'experience': experience
    }])

    # 3. Predict
    probability = model.predict_proba(input_data)[0][1]
    
    # Audit log the result
    logger.info(f"Result: {probability:.2f} using v{MODEL_METADATA['version']}")

    return round(float(probability), 2)