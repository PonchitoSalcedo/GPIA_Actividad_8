#!/usr/bin/env python
"""
Script para entrenar el modelo y registrar en MLflow
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import mlflow
import mlflow.sklearn

def train_and_track():
    """
    Entrenar modelo y registrar en MLflow
    """
    print("\n" + "="*60)
    print("🚀 INICIANDO ENTRENAMIENTO Y REGISTRO EN MLFLOW")
    print("="*60)
    
    # 1. Cargar datos
    print("\n📊 Cargando dataset...")
    housing = fetch_california_housing()
    X = pd.DataFrame(housing.data, columns=housing.feature_names)
    y = pd.Series(housing.target, name='MedHouseVal')
    
    print(f"   Dataset cargado: {X.shape[0]} muestras, {X.shape[1]} features")
    
    # 2. Dividir datos
    print("\n📊 Dividiendo datos en entrenamiento y prueba...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    print(f"   Entrenamiento: {X_train.shape[0]} muestras")
    print(f"   Prueba: {X_test.shape[0]} muestras")
    
    # 3. Escalar datos
    print("\n🔧 Escalando datos...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✅ Datos escalados correctamente")
    
    # 4. Entrenar modelo
    print("\n🤖 Entrenando modelo Random Forest...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    print("   ✅ Modelo entrenado correctamente")
    
    # 5. Evaluar modelo
    print("\n📈 Evaluando modelo...")
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"\n   📊 Rendimiento del modelo:")
    print(f"   Entrenamiento - RMSE: {train_rmse:.4f}, MAE: {train_mae:.4f}, R²: {train_r2:.4f}")
    print(f"   Prueba       - RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f}, R²: {test_r2:.4f}")
    
    # 6. Guardar modelos localmente
    print("\n💾 Guardando modelos localmente...")
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/model.joblib')
    joblib.dump(scaler, 'models/scaler.joblib')
    print("   ✅ Modelos guardados en: models/")
    
    # 7. Registrar en MLflow
    print("\n📊 Registrando en MLflow...")
    
    # Configurar MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("california_housing_monitoring")
    
    with mlflow.start_run(run_name="random_forest_base_v1"):
        # Registrar parámetros
        mlflow.log_params({
            "model_type": "RandomForestRegressor",
            "n_estimators": 100,
            "max_depth": 10,
            "test_size": 0.3,
            "random_state": 42,
            "dataset": "california_housing"
        })
        
        # Registrar métricas
        mlflow.log_metrics({
            "train_rmse": train_rmse,
            "train_mae": train_mae,
            "train_r2": train_r2,
            "test_rmse": test_rmse,
            "test_mae": test_mae,
            "test_r2": test_r2
        })
        
        # Registrar modelo
        mlflow.sklearn.log_model(model, "random_forest_model")
        
        # Registrar scaler como artifact
        mlflow.log_artifact("models/scaler.joblib")
        
        # Registrar información adicional
        mlflow.set_tag("version", "v1.0")
        mlflow.set_tag("status", "production_ready")
        
        print(f"   ✅ Modelo registrado en MLflow")
        print(f"   Run ID: {mlflow.active_run().info.run_id}")
    
    # 8. Guardar resumen
    print("\n💾 Guardando resumen del entrenamiento...")
    summary = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'RandomForestRegressor',
        'parameters': {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        },
        'performance': {
            'train': {
                'rmse': train_rmse,
                'mae': train_mae,
                'r2': train_r2
            },
            'test': {
                'rmse': test_rmse,
                'mae': test_mae,
                'r2': test_r2
            }
        },
        'dataset': {
            'samples': X.shape[0],
            'features': X.shape[1],
            'train_size': X_train.shape[0],
            'test_size': X_test.shape[0]
        }
    }
    
    os.makedirs('logs', exist_ok=True)
    with open('logs/training_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("   ✅ Resumen guardado en: logs/training_summary.json")
    
    print("\n" + "="*60)
    print("🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("="*60)
    
    return model, scaler, summary

if __name__ == "__main__":
    train_and_track()
