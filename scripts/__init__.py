"""
Scripts ejecutables del proyecto de monitorización

Este paquete contiene los scripts principales para:
- Entrenamiento y registro de modelos (train_and_track.py)
- Monitoreo continuo en producción (run_monitoring.py)
- Simulación de incidentes (simulate_incidents.py)
"""

__version__ = "1.0.0"
__author__ = "Luis Alfonso Salcedo Peña"

# Lista de scripts disponibles
__all__ = [
    'train_and_track',
    'run_monitoring',
    'simulate_incidents'
]
