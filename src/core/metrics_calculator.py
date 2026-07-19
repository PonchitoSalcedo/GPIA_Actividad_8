"""
Módulo para cálculo de métricas de rendimiento
"""
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, Any, List
import time

class MetricsCalculator:
    """Calculadora de métricas para el sistema de monitoreo"""
    
    @staticmethod
    def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcular métricas para problemas de regresión
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones del modelo
            
        Returns:
            Diccionario con métricas calculadas
        """
        return {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred)
        }
    
    @staticmethod
    def calculate_latency_metrics(predictions_times: List[float]) -> Dict[str, float]:
        """
        Calcular métricas de latencia
        
        Args:
            predictions_times: Lista de tiempos de predicción en segundos
            
        Returns:
            Diccionario con métricas de latencia
        """
        return {
            'p50': np.percentile(predictions_times, 50),
            'p90': np.percentile(predictions_times, 90),
            'p95': np.percentile(predictions_times, 95),
            'p99': np.percentile(predictions_times, 99),
            'mean': np.mean(predictions_times),
            'max': np.max(predictions_times),
            'min': np.min(predictions_times)
        }
    
    @staticmethod
    def calculate_error_budget(slo_target: float, total_requests: int, error_count: int) -> Dict[str, float]:
        """
        Calcular error budget
        
        Args:
            slo_target: Objetivo de SLO (ej. 0.999 para 99.9%)
            total_requests: Total de peticiones
            error_count: Número de errores
            
        Returns:
            Diccionario con métricas de error budget
        """
        error_rate = error_count / total_requests if total_requests > 0 else 0
        budget_consumed = error_rate / (1 - slo_target) if slo_target < 1 else 0
        budget_remaining = max(0, 1 - budget_consumed)
        
        return {
            'error_rate': error_rate,
            'budget_consumed': budget_consumed,
            'budget_remaining': budget_remaining,
            'slo_target': slo_target
        }
