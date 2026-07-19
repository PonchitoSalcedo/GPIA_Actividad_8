#!/usr/bin/env python
"""
Script para ejecutar el sistema de monitoreo continuo
"""
import os
import sys
import json
import time
import numpy as np
import pandas as pd
import joblib
import warnings
from datetime import datetime
import matplotlib.pyplot as plt

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sklearn.datasets import fetch_california_housing
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

import mlflow
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, RegressionPreset
from evidently import ColumnMapping

warnings.filterwarnings('ignore')

class MonitoringSystem:
    """Sistema de monitoreo para modelos en producción"""
    
    def __init__(self, model, scaler, reference_data, feature_names, slo_config):
        self.model = model
        self.scaler = scaler
        self.reference_data = reference_data
        self.feature_names = feature_names
        self.slo_config = slo_config
        
        self.metrics_history = []
        self.alerts_history = []
        self.budget_consumed = 0.0
        self.error_budget = slo_config.get('error_budget', 0.02)
        self.total_requests = 0
        self.error_requests = 0
        
    def predict(self, X_batch):
        """Realizar predicciones con medición de latencia"""
        start_time = time.time()
        X_scaled = self.scaler.transform(X_batch)
        predictions = self.model.predict(X_scaled)
        latency = time.time() - start_time
        return predictions, latency
    
    def evaluate_batch(self, X_batch, y_batch, batch_id):
        """Evaluar un lote de datos"""
        predictions, latency = self.predict(X_batch)
        
        # Calcular métricas
        rmse = np.sqrt(mean_squared_error(y_batch, predictions))
        mae = mean_absolute_error(y_batch, predictions)
        r2 = r2_score(y_batch, predictions)
        
        # Actualizar contadores
        self.total_requests += len(X_batch)
        
        metrics = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'latency': latency,
            'sample_size': len(X_batch)
        }
        
        self.metrics_history.append(metrics)
        return metrics, predictions
    
    def check_alerts(self, metrics):
        """Verificar violaciones de SLOs"""
        alerts = []
        
        # Verificar RMSE
        if metrics['rmse'] > self.slo_config.get('rmse_max', 0.75):
            alerts.append({
                'type': 'performance_degradation',
                'severity': 'P1',
                'metric': 'rmse',
                'value': metrics['rmse'],
                'threshold': self.slo_config['rmse_max'],
                'message': f"RMSE excede el umbral: {metrics['rmse']:.4f} > {self.slo_config['rmse_max']}",
                'timestamp': datetime.now().isoformat()
            })
            self.budget_consumed += 0.01
        
        # Verificar R²
        if metrics['r2'] < self.slo_config.get('r2_min', 0.55):
            alerts.append({
                'type': 'performance_degradation',
                'severity': 'P1',
                'metric': 'r2',
                'value': metrics['r2'],
                'threshold': self.slo_config['r2_min'],
                'message': f"R² por debajo del umbral: {metrics['r2']:.4f} < {self.slo_config['r2_min']}",
                'timestamp': datetime.now().isoformat()
            })
            self.budget_consumed += 0.01
        
        # Verificar latencia
        if metrics['latency'] > self.slo_config.get('latency_max', 0.05):
            alerts.append({
                'type': 'latency_increase',
                'severity': 'P1',
                'metric': 'latency',
                'value': metrics['latency'],
                'threshold': self.slo_config['latency_max'],
                'message': f"Latencia excede el umbral: {metrics['latency']:.4f}s > {self.slo_config['latency_max']}s",
                'timestamp': datetime.now().isoformat()
            })
            self.budget_consumed += 0.005
        
        # Verificar error budget
        if self.budget_consumed > self.error_budget:
            alerts.append({
                'type': 'error_budget_exceeded',
                'severity': 'P0',
                'metric': 'error_budget',
                'value': self.budget_consumed,
                'threshold': self.error_budget,
                'message': f"Error budget consumido: {self.budget_consumed*100:.2f}% > {self.error_budget*100:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if alerts:
            self.alerts_history.extend(alerts)
        
        return alerts
    
    def get_status(self):
        """Obtener estado actual del sistema"""
        return {
            'total_batches': len(self.metrics_history),
            'total_alerts': len(self.alerts_history),
            'budget_consumed': self.budget_consumed,
            'budget_remaining': max(0, self.error_budget - self.budget_consumed),
            'total_requests': self.total_requests,
            'current_metrics': self.metrics_history[-1] if self.metrics_history else None
        }

def load_models():
    """Cargar modelos guardados"""
    print("📂 Cargando modelos...")
    
    model_path = 'models/model.joblib'
    scaler_path = 'models/scaler.joblib'
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        print("⚠️ Modelos no encontrados. Ejecutando entrenamiento...")
        from train_and_track import train_and_track
        model, scaler, _ = train_and_track()
    else:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print(f"   ✅ Modelo cargado desde: {model_path}")
        print(f"   ✅ Scaler cargado desde: {scaler_path}")
    
    return model, scaler

def load_data():
    """Cargar y preparar datos"""
    print("\n📊 Cargando datos...")
    
    housing = fetch_california_housing()
    X = pd.DataFrame(housing.data, columns=housing.feature_names)
    y = pd.Series(housing.target, name='MedHouseVal')
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    
    reference_data = X_train.copy()
    reference_data['target'] = y_train.values
    
    current_data = X_test.copy()
    current_data['target'] = y_test.values
    
    print(f"   Datos de referencia: {reference_data.shape[0]} muestras")
    print(f"   Datos actuales: {current_data.shape[0]} muestras")
    
    return X_test, y_test, reference_data, housing.feature_names

def detect_drift(reference_data, current_data, feature_names):
    """Detectar data drift usando Evidently AI"""
    print("\n🔍 Detectando data drift...")
    
    column_mapping = ColumnMapping()
    column_mapping.target = 'target'
    column_mapping.numerical_features = feature_names
    
    drift_report = Report(metrics=[DataDriftPreset()])
    drift_report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=column_mapping
    )
    
    os.makedirs('logs', exist_ok=True)
    drift_report.save_html('logs/data_drift_report.html')
    print("   ✅ Reporte de drift guardado en: logs/data_drift_report.html")
    
    return drift_report

def generate_dashboard(monitoring_system, slo_config):
    """Generar dashboard operativo"""
    print("\n📊 Generando dashboard operativo...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Dashboard Operativo - Monitorización Continua', fontsize=16, fontweight='bold')
    
    if monitoring_system.metrics_history:
        df_metrics = pd.DataFrame(monitoring_system.metrics_history)
        
        # RMSE
        axes[0, 0].plot(df_metrics['batch_id'], df_metrics['rmse'], 'bo-', linewidth=2, markersize=8)
        axes[0, 0].axhline(y=slo_config['rmse_max'], color='r', linestyle='--', 
                           label=f"SLO: {slo_config['rmse_max']}")
        axes[0, 0].set_title('Evolución del RMSE', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('Lote')
        axes[0, 0].set_ylabel('RMSE')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # R²
        axes[0, 1].plot(df_metrics['batch_id'], df_metrics['r2'], 'go-', linewidth=2, markersize=8)
        axes[0, 1].axhline(y=slo_config['r2_min'], color='r', linestyle='--', 
                           label=f"SLO: {slo_config['r2_min']}")
        axes[0, 1].set_title('Evolución del R²', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Lote')
        axes[0, 1].set_ylabel('R²')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Latencia
        axes[1, 0].plot(df_metrics['batch_id'], df_metrics['latency'], 'ro-', linewidth=2, markersize=8)
        axes[1, 0].axhline(y=slo_config['latency_max'], color='r', linestyle='--', 
                           label=f"SLO: {slo_config['latency_max']}s")
        axes[1, 0].set_title('Evolución de la Latencia', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Lote')
        axes[1, 0].set_ylabel('Latencia (segundos)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Tamaño de muestra
        axes[1, 1].bar(df_metrics['batch_id'], df_metrics['sample_size'], color='purple', alpha=0.7)
        axes[1, 1].set_title('Tamaño de Muestra por Lote', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Lote')
        axes[1, 1].set_ylabel('Número de muestras')
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    os.makedirs('logs', exist_ok=True)
    plt.savefig('logs/operational_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✅ Dashboard guardado en: logs/operational_dashboard.png")

def run_monitoring():
    """
    Ejecutar sistema de monitoreo continuo
    """
    print("\n" + "="*60)
    print("🚀 INICIANDO SISTEMA DE MONITOREO CONTINUO")
    print("="*60)
    
    # 1. Cargar modelos
    model, scaler = load_models()
    
    # 2. Cargar datos
    X_test, y_test, reference_data, feature_names = load_data()
    
    # 3. Definir SLOs
    slo_config = {
        'rmse_max': 0.75,
        'r2_min': 0.55,
        'latency_max': 0.05,
        'error_budget': 0.02,
        'availability': 99.9
    }
    
    # 4. Inicializar sistema de monitoreo
    print("\n🔧 Inicializando sistema de monitoreo...")
    monitoring_system = MonitoringSystem(
        model=model,
        scaler=scaler,
        reference_data=reference_data,
        feature_names=feature_names,
        slo_config=slo_config
    )
    print("   ✅ Sistema de monitoreo inicializado")
    
    # 5. Detectar data drift
    drift_report = detect_drift(reference_data, X_test.assign(target=y_test.values), feature_names)
    
    # 6. Monitoreo continuo
    print("\n🔄 Ejecutando monitoreo continuo...")
    batch_size = 100
    total_batches = min(20, len(X_test) // batch_size)
    
    print(f"   Monitoreando {total_batches} lotes de {batch_size} muestras cada uno...\n")
    
    all_alerts = []
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(X_test))
        
        if start_idx >= len(X_test):
            break
        
        X_batch = X_test[start_idx:end_idx]
        y_batch = y_test[start_idx:end_idx]
        
        # Evaluar lote
        metrics, predictions = monitoring_system.evaluate_batch(X_batch, y_batch, batch_idx + 1)
        
        # Verificar alertas
        alerts = monitoring_system.check_alerts(metrics)
        
        if alerts:
            all_alerts.extend(alerts)
            print(f"⚠️ Lote {batch_idx + 1}: {len(alerts)} alertas generadas")
            for alert in alerts:
                print(f"   - {alert['severity']}: {alert['message'][:60]}...")
        else:
            print(f"✅ Lote {batch_idx + 1}: Sin alertas - Sistema saludable")
        
        time.sleep(0.1)
    
    # 7. Generar dashboard
    generate_dashboard(monitoring_system, slo_config)
    
    # 8. Guardar resultados
    print("\n💾 Guardando resultados...")
    os.makedirs('logs', exist_ok=True)
    
    # Guardar métricas
    metrics_df = pd.DataFrame(monitoring_system.metrics_history)
    metrics_df.to_csv('logs/metrics_history.csv', index=False)
    print("   ✅ Métricas guardadas en: logs/metrics_history.csv")
    
    # Guardar alertas
    alerts_df = pd.DataFrame(monitoring_system.alerts_history)
    if not alerts_df.empty:
        alerts_df.to_csv('logs/alerts_log.csv', index=False)
        print("   ✅ Alertas guardadas en: logs/alerts_log.csv")
    
    # Guardar resumen
    status = monitoring_system.get_status()
    summary = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'slo_config': slo_config,
        'total_alerts': len(monitoring_system.alerts_history),
        'health_status': '🟢 SALUDABLE' if status['budget_consumed'] < slo_config['error_budget'] else '🔴 CRÍTICO'
    }
    
    with open('logs/monitoring_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("   ✅ Resumen guardado en: logs/monitoring_summary.json")
    
    # 9. Mostrar resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL DEL MONITOREO")
    print("="*60)
    print(f"   Total lotes procesados: {status['total_batches']}")
    print(f"   Total predicciones: {status['total_requests']}")
    print(f"   Total alertas generadas: {status['total_alerts']}")
    print(f"   Error budget consumido: {status['budget_consumed']*100:.2f}%")
    print(f"   Estado del sistema: {summary['health_status']}")
    print("="*60)
    print("🎉 MONITOREO COMPLETADO EXITOSAMENTE")
    print("="*60)
    
    return monitoring_system

if __name__ == "__main__":
    run_monitoring()
