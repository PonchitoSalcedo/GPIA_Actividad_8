"""
Sistema de monitoreo principal
"""
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import numpy as np

from .metrics_calculator import MetricsCalculator
from .drift_detector import DriftDetector

class MonitoringSystem:
    """Sistema de monitoreo para modelos en producción"""
    
    def __init__(self, model, scaler, reference_data, feature_names, slo_config: Dict[str, Any]):
        """
        Inicializar sistema de monitoreo
        
        Args:
            model: Modelo de ML
            scaler: Scaler para normalizar datos
            reference_data: Datos de referencia
            feature_names: Nombres de las features
            slo_config: Configuración de SLOs
        """
        self.model = model
        self.scaler = scaler
        self.reference_data = reference_data
        self.feature_names = feature_names
        self.slo_config = slo_config
        
        self.metrics_calculator = MetricsCalculator()
        self.drift_detector = DriftDetector(reference_data, feature_names)
        
        self.metrics_history = []
        self.alerts_history = []
        self.budget_consumed = 0.0
        self.error_budget = slo_config.get('error_budget', 0.02)
        
    def predict(self, X_batch: np.ndarray) -> tuple:
        """
        Realizar predicciones con medición de latencia
        
        Args:
            X_batch: Batch de datos
            
        Returns:
            Tupla (predicciones, latencia)
        """
        start_time = time.time()
        X_scaled = self.scaler.transform(X_batch)
        predictions = self.model.predict(X_scaled)
        latency = time.time() - start_time
        return predictions, latency
    
    def evaluate_batch(self, X_batch: np.ndarray, y_batch: np.ndarray, batch_id: int) -> Dict[str, Any]:
        """
        Evaluar un lote de datos
        
        Args:
            X_batch: Features del batch
            y_batch: Targets del batch
            batch_id: ID del batch
            
        Returns:
            Diccionario con métricas del batch
        """
        predictions, latency = self.predict(X_batch)
        
        # Calcular métricas
        regression_metrics = self.metrics_calculator.calculate_regression_metrics(y_batch, predictions)
        
        metrics = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            **regression_metrics,
            'latency': latency,
            'sample_size': len(X_batch)
        }
        
        self.metrics_history.append(metrics)
        return metrics, predictions
    
    def check_slo_violations(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Verificar si las métricas violan los SLOs
        
        Args:
            metrics: Métricas actuales
            
        Returns:
            Lista de alertas generadas
        """
        alerts = []
        
        # Verificar RMSE
        if metrics.get('rmse', 0) > self.slo_config.get('rmse_max', 0.75):
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
        if metrics.get('r2', 0) < self.slo_config.get('r2_min', 0.55):
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
        if metrics.get('latency', 0) > self.slo_config.get('latency_p95_max', 0.05):
            alerts.append({
                'type': 'latency_increase',
                'severity': 'P1',
                'metric': 'latency',
                'value': metrics['latency'],
                'threshold': self.slo_config['latency_p95_max'],
                'message': f"Latencia excede el umbral: {metrics['latency']:.4f}s > {self.slo_config['latency_p95_max']}s",
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
        
        return alerts
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema"""
        return {
            'total_batches': len(self.metrics_history),
            'total_alerts': len(self.alerts_history),
            'budget_consumed': self.budget_consumed,
            'budget_remaining': max(0, self.error_budget - self.budget_consumed),
            'current_metrics': self.metrics_history[-1] if self.metrics_history else None
        }
