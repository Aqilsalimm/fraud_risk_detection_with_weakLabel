import pandas as pd
import joblib
import os
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "Final_EWS_Dataset.xlsx")
    
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found!")
        return
        
    print("Loading reference dataset...")
    df = pd.read_excel(dataset_path)
    
    features = [
        'dsri', 'gmi', 'aqi', 'sgi', 'lvgi', 'tata',
        'revenue_growth', 'asset_growth', 'net_income_growth_assets',
        'cfo_to_net_income'
    ]
    
    print("Fitting Imputer...")
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(df[features])
    
    print("Fitting RobustScaler...")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_imputed)
    
    print("Fitting Isolation Forest (contamination=0.05)...")
    iso = IsolationForest(n_estimators=300, contamination=0.05, random_state=42)
    iso.fit(X_scaled)
    
    # Save joblib models
    joblib.dump(imputer, os.path.join(current_dir, 'imputer_anomaly.joblib'))
    joblib.dump(scaler, os.path.join(current_dir, 'scaler_anomaly.joblib'))
    joblib.dump(iso, os.path.join(current_dir, 'model_iso_05.joblib'))
    
    print("Anomaly reference models trained and saved successfully!")

if __name__ == "__main__":
    main()
