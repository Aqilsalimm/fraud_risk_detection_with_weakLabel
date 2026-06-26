import os
import joblib
import pandas as pd
import numpy as np
import shap
import fitz  # PyMuPDF
import re
import tempfile
import requests
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    import io
    # Try common Tesseract paths for local Windows
    tess_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    for p in tess_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break
except ImportError:
    pytesseract = None

# Initialize FastAPI App
app = FastAPI(
    title="EWS Fraud Prediction API",
    description="API Pendeteksi Risiko Fraud Emiten berbasis Keuangan & Analisis Laporan Tahunan dengan Penjelasan SHAP (Menggunakan Model A & B).",
    version="1.1.0"
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
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_B_PATH = os.path.join(CURRENT_DIR, "model_xgb_b80.joblib")
MODEL_A_PATH = os.path.join(CURRENT_DIR, "model_xgb_a70.joblib")
DATASET_PATH = os.path.join(CURRENT_DIR, "Final_EWS_Dataset.xlsx")

# Global Variables for models, scalers and reference limits
model_b = None
model_a = None
explainer_b = None
explainer_a = None
imputer_anomaly = None
scaler_anomaly = None
model_iso_05 = None

# Reference Scaling Limits (calculated from Final_EWS_Dataset)
m_min, m_max = -5.0, 5.0
a_min, a_max = 0.2, 0.8
sentiment_min, sentiment_max = -1.0, 1.0
risk_words_min, risk_words_max = 0, 1500
readability_min, readability_max = 0, 100
rev_growth_p95 = 1.0

features = [
    "dsri", "gmi", "aqi", "sgi", "lvgi", "tata", "sgai",
    "revenue_growth", "asset_growth", "net_income_growth_assets",
    "cfo_to_net_income", "sentiment", "risk_words", "readability", "text_length",
    "anomaly_score_05"
]

positive_words = {"untung", "laba", "naik", "positif", "tumbuh", "meningkat", "optimis", "baik", "sukses", "ekspansi", "efisiensi", "membaik", "penguatan"}
negative_words = {"rugi", "turun", "negatif", "menurun", "pesimis", "buruk", "gagal", "risiko", "tantangan", "tekanan", "lambat", "ketidakpastian", "kerugian", "penurunan", "melemah"}
target_kws = ["risiko", "tantangan", "ketidakpastian", "pertumbuhan", "restrukturisasi", "kerugian"]

focused_patterns = {
    "total_assets": [
        r"(?:jumlah\s+aset|total\s+assets|jumlah\s+aktiva|total\s+aktiva)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)(?!\s*lancar|\s*tidak\s+lancar)",
        r"jumlah\s+aset\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "total_liabilities": [
        r"(?:jumlah\s+liabilitas|total\s+liabilities|jumlah\s+kewajiban)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "total_equity": [
        r"(?:jumlah\s+ekuitas|total\s+equity|jumlah\s+modal)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "current_assets": [
        r"(?:jumlah\s+aset\s+lancar|total\s+current\s+assets|jumlah\s+aktiva\s+lancar)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "ppe": [
        r"(?:aset\s+tetap|property,\s+plant\s+and\s+equipment|property,\s+plant,\s+and\s+equipment|aktiva\s+tetap)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "depreciation": [
        r"(?:penyusutan\s+aset\s+tetap|penyusutan\s+dan\s+amortisasi|depreciation\s+of\s+property|depreciation\s+and\s+amortization)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "revenue": [
        r"(?:penjualan\s+dan\s+pendapatan\s+usaha|pendapatan\s+usaha|pendapatan\s+neto|net\s+revenue|revenues|penjualan\s+bersih|net\s+sales|sales\s+and\s+revenue|pendapatan\s+dari\s+kontrak\s+dengan\s+pelanggan)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "receivables": [
        r"(?:jumlah\s+piutang\s+usaha|piutang\s+usaha|trade\s+receivable|accounts\s+receivable)[^0-9]*?(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "gross_profit": [
        r"(?:jumlah\s+laba\s+bruto|laba\s+bruto|laba\s+kotor|gross\s+profit|total\s+gross\s+profit)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "selling_expense": [
        r"(?:beban\s+penjualan|selling\s+expenses|selling\s+expense)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "ga_expense": [
        r"(?:beban\s+umum\s+dan\s+administrasi|general\s+and\s+administrative\s+expenses|general\s+and\s+administrative\s+expense)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "net_income": [
        r"(?:laba\s+(?:neto|bersih)\s+tahun\s+berjalan|laba\s+neto\s+yang\s+dapat\s+diatribusikan|laba\s+tahun\s+berjalan|net\s+income|laba\s+bersih|laba\s+\(?rugi\)?\s+tahun\s+berjalan|jumlah\s+laba\s+\(?rugi\)?|laba\s+neto)\s+(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ],
    "cfo": [
        r"(?:arus\s+kas\s+bersih[^0-9]*?aktivitas\s+operasi|net\s+cash\s+flow[^0-9]*?operating\s+activit|kas\s+bersih[^0-9]*?aktivitas\s+operasi|net\s+cash\s+provided[^0-9]*?operating\s+activit)[^0-9]*?(\(?[ \t]*[-\d.,]+[ \t]*\)?)"
    ]
}

def clean_numeric(val_str):
    if not val_str:
        return 0.0
    val_str = val_str.strip()
    is_negative = False
    if val_str.startswith('(') and val_str.endswith(')'):
        is_negative = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith('-'):
        is_negative = True
        val_str = val_str[1:].strip()
    cleaned = "".join([c for c in val_str if c.isdigit()])
    if not cleaned:
        return 0.0
    val = float(cleaned)
    if is_negative:
        val = -val
    return val

def merge_split_brackets(text):
    lines = text.split('\n')
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '(' or line == ')' or line == '( )':
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                if any(c.isdigit() for c in next_line):
                    if not next_line.startswith('-'):
                        lines[j] = '-' + lines[j]
            i += 1
            continue
        cleaned_lines.append(lines[i])
        i += 1
    return '\n'.join(cleaned_lines)

def extract_text_from_pdf(pdf_path, max_pages=40, max_ocr_pages=15):
    doc = fitz.open(pdf_path)
    text = ""
    pages_to_scan = min(len(doc), max_pages)
    for i in range(pages_to_scan):
        text += doc[i].get_text()
    if len(text.strip()) < 200 and pytesseract is not None:
        text = ""
        ocr_pages = min(len(doc), max_ocr_pages)
        for i in range(ocr_pages):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            try:
                page_text = pytesseract.image_to_string(img, lang="ind+eng")
            except:
                try:
                    page_text = pytesseract.image_to_string(img, lang="eng")
                except:
                    page_text = ""
            text += page_text + "\n"
    doc.close()
    return text

def parse_focused_metrics(text):
    text_clean = merge_split_brackets(text)
    text_clean = text_clean.lower().replace('|', ' ')
    result = {}
    for key, regex_list in focused_patterns.items():
        result[key] = None
        for pattern in regex_list:
            match = re.search(pattern, text_clean, re.MULTILINE)
            if match:
                val_str = match.group(1)
                result[key] = clean_numeric(val_str)
                break
        if result[key] is None:
            result[key] = 0.0
    return result

def clean_extracted_text(text):
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', ' ', text)
    text = re.sub(r'\b\d+[\d.,%/-]*\b', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_sentiment(text):
    words = text.split()
    if not words:
        return 0.0
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total

def calculate_readability_lix(raw_text):
    raw_text = re.sub(r'\s+', ' ', raw_text)
    words = [w.strip(',.()[]{}":;') for w in raw_text.split() if w.strip()]
    if not words:
        return 0.0
    word_count = len(words)
    sentences = [s for s in re.split(r'[.!?]+', raw_text) if s.strip()]
    sentence_count = max(1, len(sentences))
    long_words = sum(1 for w in words if len(w) > 6)
    return (word_count / sentence_count) + (long_words * 100 / word_count)

def safe_divide(num, denom):
    if denom == 0 or pd.isna(denom) or pd.isna(num):
        return 1.0
    return float(num / denom)

class PredictPayload(BaseModel):
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
    
    nama_perusahaan: Optional[str] = None
    kode: Optional[str] = None
    year: Optional[int] = None
    sektor: Optional[str] = None

def generate_gemini_commentary(
    nama_perusahaan: str,
    kode: str,
    year: int,
    sektor: str,
    metrics: dict,
    scores: dict,
    model_b: dict,
    model_a: dict
) -> str:
    GEMINI_API_KEY = "[GCP_API_KEY]"
    
    # Build list of top drivers for prompt
    feature_labels = {
        'dsri': 'DSRI (Days Sales in Receivables Index)',
        'gmi': 'GMI (Gross Margin Index)',
        'aqi': 'AQI (Asset Quality Index)',
        'sgi': 'SGI (Sales Growth Index)',
        'lvgi': 'LVGI (Leverage Index)',
        'tata': 'TATA (Total Accruals to Total Assets)',
        'sgai': 'SGAI (Sales General & Admin Index)',
        'revenue_growth': 'Revenue Growth Rate',
        'asset_growth': 'Asset Growth Rate',
        'net_income_growth_assets': 'Net Income Growth / Assets',
        'cfo_to_net_income': 'CFO to Net Income Ratio',
        'sentiment': 'Narrative Sentiment',
        'risk_words': 'Risk Words Frequency',
        'readability': 'Readability Index',
        'text_length': 'Text Length',
        'anomaly_score_05': 'Anomaly Score (Isolation Forest)',
    }
    
    drivers_b_desc = ", ".join([f"{feature_labels.get(d['feature'], d['feature'])} ({'Mendorong Risiko Naik' if d['shap_value'] > 0 else 'Mendorong Risiko Turun'})" for d in model_b.get("top_drivers", [])])
    drivers_a_desc = ", ".join([f"{feature_labels.get(d['feature'], d['feature'])} ({'Mendorong Risiko Naik' if d['shap_value'] > 0 else 'Mendorong Risiko Turun'})" for d in model_a.get("top_drivers", [])])
    
    prompt = f"""Anda adalah sistem Early Warning System (EWS) pendeteksi risiko fraud laporan keuangan emiten di Indonesia yang ahli dan profesional.
Tugas Anda adalah menulis ulasan/komentar analisis risiko (AI Commentary) dalam bahasa Indonesia yang berwibawa, objektif, dan bernilai audit tinggi berdasarkan data berikut:

Emiten: {nama_perusahaan or 'Tidak Diketahui'} ({kode or 'N/A'})
Tahun Buku: {year or 'N/A'}
Sektor: {sektor or 'N/A'}

1. Parameter Keuangan & Anomali:
- M-Score: {metrics.get('m_score', 0):.4f} (Threshold: -2.22, di atas itu menunjukkan potensi manipulasi)
- Rasio TATA (Total Accruals to Total Assets): {metrics.get('tata', 0):.4f}
- Pertumbuhan Penjualan (SGI): {metrics.get('sgi', 0):.4f}
- Pertumbuhan Pendapatan Riil: {metrics.get('revenue_growth', 0)*100:.2f}%
- Rasio Arus Kas Operasional (CFO) terhadap Laba Bersih: {metrics.get('cfo_to_net_income', 0):.4f} (Flag CFO Quality: {metrics.get('cfo_quality_flag', 'Normal')})
- Anomaly Score (Isolation Forest): {scores.get('anomaly_score_05', 0):.4f}

2. Analisis Naratif Teks Laporan Tahunan (NLP):
- Sentimen Teks: {scores.get('sentiment_scaled', 0):.2f}/100 (Semakin tinggi nilai menunjukkan sentimen semakin negatif)
- Kerapatan Kata Risiko: {scores.get('risk_words_scaled', 0):.2f}/100
- Kompleksitas Bahasa (LIX Readability): {scores.get('readability_scaled', 0):.2f}/100 (Nilai tinggi berarti bahasa berbelit-belit/obfuscation)

3. Hasil Prediksi Model Machine Learning XGBoost:
- Model B (t2 - threshold lemah >= 2): Probabilitas {model_b.get('fraud_probability', 0)*100:.2f}% ({'🔴 RISIKO TINGGI / OUTLIER' if model_b.get('fraud_prediction', 0) == 1 else '🟢 RISIKO RENDAH / NORMAL'})
- Model A (t3 - threshold kuat >= 3): Probabilitas {model_a.get('fraud_probability', 0)*100:.2f}% ({'🔴 RISIKO TINGGI / OUTLIER' if model_a.get('fraud_prediction', 0) == 1 else '🟢 RISIKO RENDAH / NORMAL'})

4. Faktor Pemicu Utama (SHAP Local Drivers):
- Pemicu Model B: {drivers_b_desc}
- Pemicu Model A: {drivers_a_desc}

Tuliskan komentar analisis Anda dalam 3 paragraf pendek dengan pembagian sebagai berikut:
Paragraf 1: Ringkasan tingkat risiko emiten berdasarkan kesimpulan model XGBoost A & B serta keselarasan tingkat risiko gabungan (Combined Fraud Score).
Paragraf 2: Soroti anomali keuangan paling signifikan dan/atau metrik teks laporan tahunan yang menjadi pendorong utama (SHAP drivers) risiko tersebut.
Paragraf 3: Berikan rekomendasi langkah audit atau investigasi spesifik yang perlu dilakukan oleh analis atau auditor eksternal.

Penting: Tulis secara profesional, padat, tanpa basa-basi pembuka/penutup, dan langsung berfokus pada substansi analisis laporan keuangan dalam bahasa Indonesia yang baik dan benar."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            commentary = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            return commentary
        else:
            print("Gemini API Error Response:", response.text)
            return f"Gagal menghasilkan komentar otomatis dari AI (Status Code: {response.status_code})."
    except Exception as e:
        print("Exception during Gemini Commentary generation:", e)
        return f"Terjadi kesalahan koneksi saat menghubungi AI Gemini: {str(e)}"

@app.on_event("startup")
def load_all_models():
    global model_b, model_a, explainer_b, explainer_a, imputer_anomaly, scaler_anomaly, model_iso_05
    global m_min, m_max, a_min, a_max, sentiment_min, sentiment_max, risk_words_min, risk_words_max, readability_min, readability_max, rev_growth_p95
    
    # Load XGBoost Model B (80% split)
    if os.path.exists(MODEL_B_PATH):
        try:
            model_b = joblib.load(MODEL_B_PATH)
            explainer_b = shap.TreeExplainer(model_b)
            print("XGBoost Model B (80%) loaded.")
        except Exception as e:
            print(f"Error loading Model B: {e}")
            
    # Load XGBoost Model A (70% split)
    if os.path.exists(MODEL_A_PATH):
        try:
            model_a = joblib.load(MODEL_A_PATH)
            explainer_a = shap.TreeExplainer(model_a)
            print("XGBoost Model A (70%) loaded.")
        except Exception as e:
            print(f"Error loading Model A: {e}")
            
    # Load Anomaly detection components
    try:
        imputer_anomaly = joblib.load(os.path.join(CURRENT_DIR, "imputer_anomaly.joblib"))
        scaler_anomaly = joblib.load(os.path.join(CURRENT_DIR, "scaler_anomaly.joblib"))
        model_iso_05 = joblib.load(os.path.join(CURRENT_DIR, "model_iso_05.joblib"))
        print("Anomaly models loaded.")
    except Exception as e:
        print(f"Error loading Anomaly models: {e}")

    # Load Reference dataset limits
    if os.path.exists(DATASET_PATH):
        try:
            df_ref = pd.read_excel(DATASET_PATH)
            m_min, m_max = float(df_ref['m_score'].min()), float(df_ref['m_score'].max())
            a_min, a_max = float(df_ref['anomaly_score_05'].min()), float(df_ref['anomaly_score_05'].max())
            sentiment_min, sentiment_max = float(df_ref['sentiment'].min()), float(df_ref['sentiment'].max())
            risk_words_min, risk_words_max = float(df_ref['risk_words'].min()), float(df_ref['risk_words'].max())
            readability_min, readability_max = float(df_ref['readability'].min()), float(df_ref['readability'].max())
            rev_growth_p95 = float(df_ref['revenue_growth'].quantile(0.95))
            print("Reference dataset scaling limits initialized.")
        except Exception as e:
            print(f"Error reading dataset reference limits: {e}")

@app.get("/")
def read_root():
    return {
        "status": "EWS Fraud Prediction API is running",
        "model_b_loaded": model_b is not None,
        "model_a_loaded": model_a is not None,
        "anomaly_loaded": model_iso_05 is not None
    }

@app.post("/predict")
def predict(payload: PredictPayload):
    global model_b, model_a, explainer_b, explainer_a
    if model_b is None or model_a is None:
        raise HTTPException(status_code=553, detail="Models are not fully loaded on server.")
        
    try:
        # Convert payload to dataframe, excluding metadata
        payload_dict = payload.dict()
        xgb_data = {k: v for k, v in payload_dict.items() if k not in ["nama_perusahaan", "kode", "year", "sektor"]}
        xgb_input = pd.DataFrame([xgb_data])
        
        # Model B (t2) predictions
        prob_b = float(model_b.predict_proba(xgb_input)[0, 1])
        pred_b = int(model_b.predict(xgb_input)[0])
        
        # Model A (t3) predictions
        prob_a = float(model_a.predict_proba(xgb_input)[0, 1])
        pred_a = int(model_a.predict(xgb_input)[0])
        
        # Compute SHAP for Model B
        shap_vals_b = explainer_b.shap_values(xgb_input)[0]
        local_df_b = pd.DataFrame({
            "feature": features,
            "shap_value": shap_vals_b,
            "abs_shap": np.abs(shap_vals_b)
        }).sort_values("abs_shap", ascending=False)
        top_drivers_b = local_df_b.head(5).to_dict(orient="records")
        
        # Compute SHAP for Model A
        shap_vals_a = explainer_a.shap_values(xgb_input)[0]
        local_df_a = pd.DataFrame({
            "feature": features,
            "shap_value": shap_vals_a,
            "abs_shap": np.abs(shap_vals_a)
        }).sort_values("abs_shap", ascending=False)
        top_drivers_a = local_df_a.head(5).to_dict(orient="records")

        # Generate AI commentary if requested
        ai_commentary = None
        if payload.nama_perusahaan:
            m_score = (
                -4.84
                + 0.920 * payload.dsri
                + 0.528 * payload.gmi
                + 0.404 * payload.aqi
                + 0.892 * payload.sgi
                - 0.172 * payload.sgai
                + 4.679 * payload.tata
                - 0.327 * payload.lvgi
            )
            metrics = {
                "m_score": m_score,
                "tata": payload.tata,
                "sgi": payload.sgi,
                "revenue_growth": payload.revenue_growth,
                "cfo_to_net_income": payload.cfo_to_net_income,
                "cfo_quality_flag": "Low Quality" if (payload.cfo_to_net_income <= 0) else "Normal"
            }
            
            s_min = sentiment_min if 'sentiment_min' in globals() else -0.5
            s_max = sentiment_max if 'sentiment_max' in globals() else 0.5
            rw_min = risk_words_min if 'risk_words_min' in globals() else 0.0
            rw_max = risk_words_max if 'risk_words_max' in globals() else 100.0
            r_min = readability_min if 'readability_min' in globals() else 20.0
            r_max = readability_max if 'readability_max' in globals() else 80.0
            
            sentiment_scaled = float((s_max - payload.sentiment) / (s_max - s_min) * 100) if (s_max - s_min) > 0 else 0.0
            risk_words_scaled = float((payload.risk_words - rw_min) / (rw_max - rw_min) * 100) if (rw_max - rw_min) > 0 else 0.0
            readability_scaled = float((payload.readability - r_min) / (r_max - r_min) * 100) if (r_max - r_min) > 0 else 0.0
            
            scores = {
                "anomaly_score_05": payload.anomaly_score_05,
                "sentiment_scaled": sentiment_scaled,
                "risk_words_scaled": risk_words_scaled,
                "readability_scaled": readability_scaled
            }
            
            ai_commentary = generate_gemini_commentary(
                nama_perusahaan=payload.nama_perusahaan,
                kode=payload.kode,
                year=payload.year,
                sektor=payload.sektor,
                metrics=metrics,
                scores=scores,
                model_b={"fraud_probability": prob_b, "fraud_prediction": pred_b, "top_drivers": top_drivers_b},
                model_a={"fraud_probability": prob_a, "fraud_prediction": pred_a, "top_drivers": top_drivers_a}
            )
        
        # Return composite payload keeping backward compatibility with single model structure
        return {
            "success": True,
            "fraud_probability": prob_b,
            "fraud_prediction": pred_b,
            "top_drivers": top_drivers_b,
            "ai_commentary": ai_commentary,
            "model_b": {
                "fraud_probability": prob_b,
                "fraud_prediction": pred_b,
                "top_drivers": top_drivers_b
            },
            "model_a": {
                "fraud_probability": prob_a,
                "fraud_prediction": pred_a,
                "top_drivers": top_drivers_a
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=550, detail=f"Prediction error: {str(e)}")

@app.post("/upload-predict")
async def upload_predict(
    kode: str = Form(...),
    year: int = Form(...),
    sektor: str = Form(...),
    nama_perusahaan: str = Form(...),
    financial_statement: UploadFile = File(...),
    annual_report: Optional[UploadFile] = File(None),
    
    # Lag financial inputs (passed from Laravel DB or manual input)
    total_assets_lag: float = Form(0.0),
    revenue_lag: float = Form(0.0),
    receivables_lag: float = Form(0.0),
    net_income_lag: float = Form(0.0),
    total_liabilities_lag: float = Form(0.0),
    current_assets_lag: float = Form(0.0),
    ppe_lag: float = Form(0.0),
    depreciation_lag: float = Form(0.0),
    selling_expense_lag: float = Form(0.0),
    ga_expense_lag: float = Form(0.0),
    gross_profit_lag: float = Form(0.0)
):
    global model_b, model_a, explainer_b, explainer_a, imputer_anomaly, scaler_anomaly, model_iso_05
    if model_b is None or model_a is None or model_iso_05 is None:
        raise HTTPException(status_code=503, detail="Models are not fully loaded on server.")
        
    try:
        # 1. Process Financial Statement PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_fs:
            tmp_fs.write(await financial_statement.read())
            fs_path = tmp_fs.name
            
        fs_text = extract_text_from_pdf(fs_path, max_pages=40, max_ocr_pages=15)
        fin_metrics = parse_focused_metrics(fs_text)
        
        try: os.remove(fs_path)
        except: pass
        
        # Extract variables from fin_metrics
        ta = fin_metrics.get("total_assets", 0.0)
        tl = fin_metrics.get("total_liabilities", 0.0)
        te = fin_metrics.get("total_equity", 0.0)
        ca = fin_metrics.get("current_assets", 0.0)
        ppe = fin_metrics.get("ppe", 0.0)
        dep = fin_metrics.get("depreciation", 0.0)
        rev = fin_metrics.get("revenue", 0.0)
        rec = fin_metrics.get("receivables", 0.0)
        gp = fin_metrics.get("gross_profit", 0.0)
        se = fin_metrics.get("selling_expense", 0.0)
        gae = fin_metrics.get("ga_expense", 0.0)
        ni = fin_metrics.get("net_income", 0.0)
        cfo = fin_metrics.get("cfo", 0.0)
        
        # 2. Process Annual Report PDF (optional)
        sentiment = 0.0
        risk_words = 0.0
        readability = 0.0
        text_length = 0.0
        
        has_narrative = False
        if annual_report is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_ar:
                tmp_ar.write(await annual_report.read())
                ar_path = tmp_ar.name
                
            ar_text = extract_text_from_pdf(ar_path, max_pages=40, max_ocr_pages=15)
            try: os.remove(ar_path)
            except: pass
            
            ar_text_clean = clean_extracted_text(ar_text)
            text_length = float(len(ar_text_clean))
            
            if text_length > 100:
                has_narrative = True
                sentiment = float(calculate_sentiment(ar_text_clean))
                readability = float(calculate_readability_lix(ar_text))
                
                # Count keyword frequencies
                counts = {kw: ar_text_clean.count(kw) for kw in target_kws}
                risk_words = float(counts["risiko"] + counts["tantangan"] + counts["ketidakpastian"] + counts["restrukturisasi"] + counts["kerugian"])
                
        # 3. Calculate Beneish Indices
        # DSRI
        ratio_rec_t = safe_divide(rec, rev)
        ratio_rec_lag = safe_divide(receivables_lag, revenue_lag)
        dsri = safe_divide(ratio_rec_t, ratio_rec_lag)
        
        # GMI
        ratio_gp_t = safe_divide(gp, rev)
        ratio_gp_lag = safe_divide(gross_profit_lag, revenue_lag)
        gmi = safe_divide(ratio_gp_lag, ratio_gp_t)
        
        # AQI
        ratio_aq_t = 1.0 - safe_divide(ca + ppe, ta)
        ratio_aq_lag = 1.0 - safe_divide(current_assets_lag + ppe_lag, total_assets_lag)
        aqi = safe_divide(ratio_aq_t, ratio_aq_lag)
        
        # SGI
        sgi = safe_divide(rev, revenue_lag)
        
        # LVGI
        ratio_lv_t = safe_divide(tl, ta)
        ratio_lv_lag = safe_divide(total_liabilities_lag, total_assets_lag)
        lvgi = safe_divide(ratio_lv_t, ratio_lv_lag)
        
        # DEPI
        dep_rate_t = safe_divide(abs(dep), abs(ppe) + abs(dep))
        dep_rate_lag = safe_divide(abs(depreciation_lag), abs(ppe_lag) + abs(depreciation_lag))
        depi = safe_divide(dep_rate_lag, dep_rate_t)
        
        # SGAI
        sga_t = abs(se) + abs(gae)
        sga_lag = abs(selling_expense_lag) + abs(ga_expense_lag)
        ratio_sga_t = safe_divide(sga_t, rev)
        ratio_sga_lag = safe_divide(sga_lag, revenue_lag)
        sgai = safe_divide(ratio_sga_t, ratio_sga_lag)
        
        # TATA
        tata = safe_divide(ni - cfo, ta)
        # Clip TATA
        tata = max(-1.0, min(1.0, tata))
        
        # Clip ratios
        dsri = max(0.1, min(10.0, dsri))
        gmi = max(0.1, min(10.0, gmi))
        aqi = max(0.1, min(10.0, aqi))
        sgi = max(0.1, min(10.0, sgi))
        lvgi = max(0.1, min(10.0, lvgi))
        depi = max(0.1, min(10.0, depi))
        sgai = max(0.1, min(10.0, sgai))
        
        # 4. Calculate M-Score
        m_score = (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )
        fraud_flag = "High Risk" if m_score > -1.78 else "Low Risk"
        
        # 5. Calculate growth rate and CFO Quality
        revenue_growth = safe_divide(rev - revenue_lag, revenue_lag)
        asset_growth = safe_divide(ta - total_assets_lag, total_assets_lag)
        net_income_growth_assets = safe_divide(ni - net_income_lag, total_assets_lag)
        cfo_to_net_income = safe_divide(cfo, ni)
        
        # Winsorize / clip growth based on standard bounds
        revenue_growth = max(-2.0, min(5.0, revenue_growth))
        asset_growth = max(-2.0, min(5.0, asset_growth))
        net_income_growth_assets = max(-2.0, min(5.0, net_income_growth_assets))
        cfo_to_net_income = max(-10.0, min(10.0, cfo_to_net_income))
        
        cfo_quality_flag = "Low Quality" if (ni > 0 and cfo <= 0) else "Normal"
        
        # 6. Anomaly Detection via Isolation Forest
        anomaly_features = [
            dsri, gmi, aqi, sgi, lvgi, tata,
            revenue_growth, asset_growth, net_income_growth_assets,
            cfo_to_net_income
        ]
        
        # Run scaler and forest
        imputed_feat = imputer_anomaly.transform([anomaly_features])
        scaled_feat = scaler_anomaly.transform(imputed_feat)
        
        anomaly_label_05 = int(model_iso_05.predict(scaled_feat)[0]) # -1 outlier, 1 normal
        anomaly_score_05 = float(-model_iso_05.score_samples(scaled_feat)[0])
        
        # 7. Scaling and Fraud Scoring
        m_score_scaled = float(100 * (m_score - m_min) / (m_max - m_min))
        m_score_scaled = max(0.0, min(100.0, m_score_scaled))
        
        anomaly_score_scaled = float(100 * (anomaly_score_05 - a_min) / (a_max - a_min))
        anomaly_score_scaled = max(0.0, min(100.0, anomaly_score_scaled))
        
        financial_risk_score = 0.4 * m_score_scaled + 0.6 * anomaly_score_scaled
        
        # Scaling narrative metrics
        if has_narrative:
            sentiment_scaled = float((sentiment_max - sentiment) / (sentiment_max - sentiment_min) * 100)
            sentiment_scaled = max(0.0, min(100.0, sentiment_scaled))
            
            risk_words_scaled = float((risk_words - risk_words_min) / (risk_words_max - risk_words_min) * 100)
            risk_words_scaled = max(0.0, min(100.0, risk_words_scaled))
            
            readability_scaled = float((readability - readability_min) / (readability_max - readability_min) * 100)
            readability_scaled = max(0.0, min(100.0, readability_scaled))
            
            narrative_risk_score = 0.40 * sentiment_scaled + 0.30 * risk_words_scaled + 0.30 * readability_scaled
        else:
            sentiment_scaled = 0.0
            risk_words_scaled = 0.0
            readability_scaled = 0.0
            narrative_risk_score = financial_risk_score
            
        combined_fraud_score = 0.70 * financial_risk_score + 0.30 * narrative_risk_score
        
        if combined_fraud_score <= 30:
            combined_fraud_status = "Low"
        elif combined_fraud_score <= 60:
            combined_fraud_status = "Medium"
        elif combined_fraud_score <= 80:
            combined_fraud_status = "High"
        else:
            combined_fraud_status = "Critical"
            
        # 8. Weak Labeling Rules
        rule1 = 1 if m_score > -2.22 else 0
        rule2 = 1 if anomaly_label_05 == -1 else 0
        rule3 = 1 if (has_narrative and narrative_risk_score > 60) else 0
        rule4 = 1 if cfo_quality_flag == "Low Quality" else 0
        rule5 = 1 if revenue_growth > rev_growth_p95 else 0
        
        weak_score = rule1 + rule2 + rule3 + rule4 + rule5
        weak_label_t3 = 1 if weak_score >= 3 else 0
        weak_label_t2 = 1 if weak_score >= 2 else 0
        
        # 9. Predict XGBoost Class & Probabilities (Both Models B and A)
        xgb_input = pd.DataFrame([{
            "dsri": dsri,
            "gmi": gmi,
            "aqi": aqi,
            "sgi": sgi,
            "lvgi": lvgi,
            "tata": tata,
            "sgai": sgai,
            "revenue_growth": revenue_growth,
            "asset_growth": asset_growth,
            "net_income_growth_assets": net_income_growth_assets,
            "cfo_to_net_income": cfo_to_net_income,
            "sentiment": sentiment,
            "risk_words": risk_words,
            "readability": readability,
            "text_length": text_length,
            "anomaly_score_05": anomaly_score_05
        }])
        
        # Model B
        prob_b = float(model_b.predict_proba(xgb_input)[0, 1])
        pred_b = int(model_b.predict(xgb_input)[0])
        shap_vals_b = explainer_b.shap_values(xgb_input)[0]
        local_df_b = pd.DataFrame({
            "feature": features,
            "shap_value": shap_vals_b,
            "abs_shap": np.abs(shap_vals_b)
        }).sort_values("abs_shap", ascending=False)
        top_drivers_b = local_df_b.head(5).to_dict(orient="records")

        # Model A
        prob_a = float(model_a.predict_proba(xgb_input)[0, 1])
        pred_a = int(model_a.predict(xgb_input)[0])
        shap_vals_a = explainer_a.shap_values(xgb_input)[0]
        local_df_a = pd.DataFrame({
            "feature": features,
            "shap_value": shap_vals_a,
            "abs_shap": np.abs(shap_vals_a)
        }).sort_values("abs_shap", ascending=False)
        top_drivers_a = local_df_a.head(5).to_dict(orient="records")
        
        # Generate AI Commentary using Gemini
        metrics_dict = {
            "m_score": m_score,
            "tata": tata,
            "sgi": sgi,
            "revenue_growth": revenue_growth,
            "cfo_to_net_income": cfo_to_net_income,
            "cfo_quality_flag": cfo_quality_flag
        }
        scores_dict = {
            "anomaly_score_05": anomaly_score_05,
            "sentiment_scaled": sentiment_scaled,
            "risk_words_scaled": risk_words_scaled,
            "readability_scaled": readability_scaled
        }
        ai_commentary = generate_gemini_commentary(
            nama_perusahaan=nama_perusahaan,
            kode=kode,
            year=year,
            sektor=sektor,
            metrics=metrics_dict,
            scores=scores_dict,
            model_b={"fraud_probability": prob_b, "fraud_prediction": pred_b, "top_drivers": top_drivers_b},
            model_a={"fraud_probability": prob_a, "fraud_prediction": pred_a, "top_drivers": top_drivers_a}
        )

        return {
            "success": True,
            "ai_commentary": ai_commentary,
            "kode": kode,
            "year": year,
            "sektor": sektor,
            "nama_perusahaan": nama_perusahaan,
            "extracted_financials": {
                "total_assets": ta,
                "total_liabilities": tl,
                "total_equity": te,
                "current_assets": ca,
                "ppe": ppe,
                "depreciation": dep,
                "revenue": rev,
                "receivables": rec,
                "gross_profit": gp,
                "selling_expense": se,
                "ga_expense": gae,
                "net_income": ni,
                "cfo": cfo
            },
            "extracted_narratives": {
                "sentiment": sentiment,
                "risk_words": risk_words,
                "readability": readability,
                "text_length": text_length
            },
            "calculated_ratios": {
                "dsri": dsri,
                "gmi": gmi,
                "aqi": aqi,
                "sgi": sgi,
                "lvgi": lvgi,
                "depi": depi,
                "sgai": sgai,
                "tata": tata,
                "m_score": m_score,
                "fraud_flag": fraud_flag,
                "revenue_growth": revenue_growth,
                "asset_growth": asset_growth,
                "net_income_growth_assets": net_income_growth_assets,
                "cfo_to_net_income": cfo_to_net_income,
                "cfo_quality_flag": cfo_quality_flag
            },
            "scores": {
                "anomaly_score_05": anomaly_score_05,
                "anomaly_label_05": anomaly_label_05,
                "m_score_scaled": m_score_scaled,
                "anomaly_score_scaled": anomaly_score_scaled,
                "financial_risk_score": financial_risk_score,
                "sentiment_scaled": sentiment_scaled,
                "risk_words_scaled": risk_words_scaled,
                "readability_scaled": readability_scaled,
                "narrative_risk_score": narrative_risk_score,
                "combined_fraud_score": combined_fraud_score,
                "combined_fraud_status": combined_fraud_status
            },
            "weak_labeling": {
                "rule1": rule1,
                "rule2": rule2,
                "rule3": rule3,
                "rule4": rule4,
                "rule5": rule5,
                "weak_score": weak_score,
                "weak_label_t3": weak_label_t3,
                "weak_label_t2": weak_label_t2
            },
            # Return prediction for both models (keeping top-level backwards compatible with B)
            "prediction": {
                "fraud_prediction": pred_b,
                "fraud_probability": prob_b,
                "top_drivers": top_drivers_b
            },
            "model_b": {
                "fraud_prediction": pred_b,
                "fraud_probability": prob_b,
                "top_drivers": top_drivers_b
            },
            "model_a": {
                "fraud_prediction": pred_a,
                "fraud_probability": prob_a,
                "top_drivers": top_drivers_a
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
