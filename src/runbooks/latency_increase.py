"""
Runbook para aumento de latencia
"""
from typing import Dict, Any
from .base_runbook import BaseRunbook

class LatencyIncreaseRunbook(BaseRunbook):
    """Runbook para manejar aumento de latencia"""
    
    def get_runbook_name(self) -> str:
        return "Aumento de Latencia en Inferencia"
    
    def get_severity(self) -> str:
        return "P1"
    
    def investigate(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de investigación"""
        print("   🔍 Investigando aumento de latencia...")
        
        # Paso 1: Verificar recursos
        self._execute_step(
            1,
            "Verificar recursos del sistema",
            "Revisar CPU, memoria, red y disco del servidor",
            "kubectl top pods | grep ml-model"
        )
        
        # Paso 2: Analizar logs
        self._execute_step(
            2,
            "Analizar logs del servicio",
            "Buscar errores, timeouts o warnings en el servicio",
            "journalctl -u ml-service -n 200 --since '1 hour ago'"
        )
        
        # Paso 3: Verificar dependencias
        self._execute_step(
            3,
            "Verificar dependencias externas",
            "Chequear conectividad a bases de datos y servicios externos",
            "python scripts/check_dependencies.py"
        )
        
        # Resultados
        investigation_result = {
            'root_cause': 'Aumento de tráfico y saturación de CPU',
            'cpu_usage': 92,
            'memory_usage': 85,
            'request_count': 1500,  # por minuto
            'normal_request_count': 800,
            'bottleneck': 'CPU'
        }
        
        print(f"\n   📊 Resultados de investigación:")
        print(f"      Causa raíz: {investigation_result['root_cause']}")
        print(f"      Uso de CPU: {investigation_result['cpu_usage']}%")
        print(f"      Uso de memoria: {investigation_result['memory_usage']}%")
        print(f"      Peticiones por minuto: {investigation_result['request_count']}")
        
        return investigation_result
    
    def remediate(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de remediación"""
        print("\n   🔧 Aplicando remediación...")
        
        # Paso 4: Escalar recursos
        self._execute_step(
            4,
            "Escalar recursos (Horizontal Pod Autoscaling)",
            "Aumentar número de réplicas del servicio",
            "kubectl scale deployment ml-model --replicas=5",
            "2 minutos"
        )
        
        # Paso 5: Optimizar modelo
        self._execute_step(
            5,
            "Optimizar modelo (quantization)",
            "Aplicar técnicas de optimización al modelo",
            "python scripts/optimize_model.py --quantize int8",
            "10 minutos"
        )
        
        # Paso 6: Rollback si es necesario
        self._execute_step(
            6,
            "Rollback a versión anterior estable",
            "Si el problema comenzó después de un deploy, revertir",
            "kubectl rollout undo deployment/ml-model"
        )
        
        remediation_result = {
            'new_latency_p95': 0.035,
            'new_latency_p99': 0.065,
            'replicas': 5,
            'optimization_applied': True,
            'rollback_executed': False
        }
        
        print(f"\n   📊 Resultados de remediación:")
        print(f"      Nueva latencia p95: {remediation_result['new_latency_p95']:.3f}s")
        print(f"      Nueva latencia p99: {remediation_result['new_latency_p99']:.3f}s")
        print(f"      Réplicas: {remediation_result['replicas']}")
        
        return remediation_result
    
    def verify(self, remediation_result: Dict[str, Any]) -> Dict[str, bool]:
        """Fase de verificación"""
        print("\n   ✅ Verificando criterios de éxito...")
        
        criteria = {
            'latency_p95_improved': remediation_result['new_latency_p95'] < 0.05,
            'latency_p99_improved': remediation_result['new_latency_p99'] < 0.10,
            'scaling_successful': remediation_result['replicas'] >= 3,
            'error_rate_acceptable': True  # Simulado
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
