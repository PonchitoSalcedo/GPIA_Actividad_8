"""
Módulo de runbooks - Gestión de incidentes y respuesta automatizada
"""
from .base_runbook import BaseRunbook
from .performance_degradation import PerformanceDegradationRunbook
from .latency_increase import LatencyIncreaseRunbook
from .data_drift_runbook import DataDriftRunbook
from .error_budget_runbook import ErrorBudgetRunbook

__all__ = [
    'BaseRunbook',
    'PerformanceDegradationRunbook',
    'LatencyIncreaseRunbook',
    'DataDriftRunbook',
    'ErrorBudgetRunbook'
]

class RunbookFactory:
    """Fábrica para crear runbooks según el tipo de incidente"""
    
    @staticmethod
    def create_runbook(incident_type: str, config: dict):
        """Crear un runbook específico según el tipo de incidente"""
        runbooks = {
            'performance_degradation': PerformanceDegradationRunbook,
            'latency_increase': LatencyIncreaseRunbook,
            'data_drift': DataDriftRunbook,
            'error_budget': ErrorBudgetRunbook
        }
        
        runbook_class = runbooks.get(incident_type)
        if runbook_class:
            return runbook_class(config)
        else:
            raise ValueError(f"Tipo de runbook no soportado: {incident_type}")
