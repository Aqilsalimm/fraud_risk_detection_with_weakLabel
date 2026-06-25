import os
import pickle
import pandas as pd
import numpy as np
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI App
app = FastAPI(
    title="EWS Fraud Prediction API",
    description="API Pendeteksi Risiko Fraud Emiten berbasis Keuangan & Analisis Laporan Tahunan dengan Penjelasan SHAP.",
    version="1.0.0"
)

# Enable CORS for frontend/Laravel integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File Paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_xgb_b80.pkl")

# Global Variables for model and explainer
model = None
explainer = None
features = [
    "dsri", "gmi", "aqi", "sgi", "lvgi", "tata", "sgai",
    "revenue_growth", "asset_growth", "net_income_growth_assets",
    "cfo_to_net_income", "sentiment", "risk_words", "readability", "text_length",
    "anomaly_score_05"
]

@app.on_event("startup")
def load_model_and_explainer():
    global model, explainer
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            explainer = shap.TreeExplainer(model)
            print("Model and SHAP Explainer loaded successfully!")
        except Exception as e:
            print(f"Error loading model/explainer: {e}")
    else:
        print(f"Model file not found at: {MODEL_PATH}")

# Input Schema
class PredictionInput(BaseModel):
    dsri: float
    gmi: float
    aqi: float
    sgi: float
    lvgi: float
    tata: float
    sgai: float
    revenue_growth: float
    asset_growth: float
    net_income_growth_assets: float
    cfo_to_net_income: float
    sentiment: float
    risk_words: float
    readability: float
    text_length: float
    anomaly_score_05: float

@app.get("/")
def read_root():
    return {"status": "EWS Fraud Prediction API is running", "model_loaded": model is not None}

@app.post("/predict")
def predict_fraud(payload: PredictionInput):
    global model, explainer
    if model is None or explainer is None:
        raise HTTPException(status_code=503, detail="Model/Explainer is not loaded on server.")
    
    try:
        # Convert input payload to dictionary
        input_dict = payload.model_dump()
        
        # Convert to single-row DataFrame
        input_df = pd.DataFrame([input_dict])
        
        # Predict Class & Probability
        prob = float(model.predict_proba(input_df)[0, 1])
        pred = int(model.predict(input_df)[0])
        
        # Compute SHAP value for this instance
        shap_vals = explainer.shap_values(input_df)[0]
        
        # Get top driver features
        local_df = pd.DataFrame({
            "feature": features,
            "shap_value": shap_vals,
            "abs_shap": np.abs(shap_vals)
        }).sort_values("abs_shap", ascending=False)
        
        top_drivers = local_df.head(5).to_dict(orient="records")
        
        return {
            "fraud_prediction": pred,
            "fraud_probability": prob,
            "top_drivers": top_drivers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
