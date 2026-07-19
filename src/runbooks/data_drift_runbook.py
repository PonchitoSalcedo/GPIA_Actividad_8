"""
Runbook para data drift detectado
"""
from typing import Dict, Any
from .base_runbook import BaseRunbook

class DataDriftRunbook(BaseRunbook):
    """Runbook para manejar data drift"""
    
    def get_runbook_name(self) -> str:
        return "Data Drift Detectado en Features"
    
    def get_severity(self) -> str:
        return "P2"
    
    def investigate(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de investigación"""
        print("   🔍 Investigando data drift...")
        
        # Paso 1: Identificar features con drift
        self._execute_step(
            1,
            "Identificar features con drift",
            "Analizar reporte de Evidently AI y listar features afectados",
            "python scripts/analyze_drift_report.py --html data_drift_report.html"
        )
        
        # Paso 2: Visualizar distribuciones
        self._execute_step(
            2,
            "Visualizar distribuciones",
            "Graficar distribución histórica vs actual de features afectados",
            "python scripts/plot_drift_features.py --features MedInc,AveOccup"
        )
        
        # Paso 3: Determinar causa
        self._execute_step(
            3,
            "Determinar causa del drift",
            "Investigar si es cambio estacional, nuevo comportamiento, error de datos",
            "python scripts/investigate_drift_cause.py --db query"
        )
        
        # Resultados
        investigation_result = {
            'drifted_features': ['MedInc', 'AveOccup', 'Population'],
            'drift_scores': {
                'MedInc': 0.32,
                'AveOccup': 0.28,
                'Population': 0.26
            },
            'root_cause': 'Cambio en la distribución demográfica',
            'seasonal_pattern': False,
            'recommendation': 'Actualizar datos de referencia y reentrenar'
        }
        
        print(f"\n   📊 Resultados de investigación:")
        print(f"      Features con drift: {', '.join(investigation_result['drifted_features'])}")
        print(f"      Causa: {investigation_result['root_cause']}")
        print(f"      Recomendación: {investigation_result['recommendation']}")
        
        return investigation_result
    
    def remediate(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de remediación"""
        print("\n   🔧 Aplicando remediación...")
        
        # Paso 4: Actualizar datos de referencia
        self._execute_step(
            4,
            "Actualizar datos de referencia",
            "Actualizar baseline con datos más recientes (últimos 7 días)",
            "python scripts/update_reference_data.py --days 7",
            "10 minutos"
        )
        
        # Paso 5: Reentrenar modelo
        self._execute_step(
            5,
            "Reentrenar modelo con datos actualizados",
            "Incorporar datos con nueva distribución en el entrenamiento",
            "python scripts/retrain_with_new_data.py --include_drifted_features",
            "30 minutos"
        )
        
        # Paso 6: Actualizar umbrales
        self._execute_step(
            6,
            "Actualizar umbrales de drift",
            "Ajustar umbrales si el drift es estacional",
            "python scripts/update_drift_thresholds.py --new_threshold 0.30"
        )
        
        remediation_result = {
            'reference_updated': True,
            'model_retrained': True,
            'new_drift_scores': {
                'MedInc': 0.15,
                'AveOccup': 0.12,
                'Population': 0.18
            },
            'all_under_threshold': True
        }
        
        print(f"\n   📊 Resultados de remediación:")
        print(f"      Datos de referencia actualizados: {remediation_result['reference_updated']}")
        print(f"      Modelo reentrenado: {remediation_result['model_retrained']}")
        print(f"      Todos los features bajo umbral: {remediation_result['all_under_threshold']}")
        
        return remediation_result
    
    def verify(self, remediation_result: Dict[str, Any]) -> Dict[str, bool]:
        """Fase de verificación"""
        print("\n   ✅ Verificando criterios de éxito...")
        
        criteria = {
            'all_under_threshold': remediation_result['all_under_threshold'],
            'reference_updated': remediation_result['reference_updated'],
            'model_retrained': remediation_result['model_retrained'],
            'no_new_drift_detected': True  # Simulado
        }
        
        success = all(criteria.values())
        
        if success:
            print("   ✅ ¡Todos los criterios de verificación cumplidos!")
        else:
            print("   ❌ Algunos criterios de verificación fallaron:")
            for criterion, passed in criteria.items():
                if not passed:
                    print(f"      - {criterion}")
        
        return {
            'success': success,
            'criteria': criteria,
            'failures': [k for k, v in criteria.items() if not v]
        }
