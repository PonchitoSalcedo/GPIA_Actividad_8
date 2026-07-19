"""
Clase base para todos los runbooks del sistema
"""
from abc import ABC, abstractmethod
from datetime import datetime
import json
import time
from typing import Dict, List, Any, Optional

class BaseRunbook(ABC):
    """Clase abstracta base para runbooks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.execution_log = []
        self.start_time = None
        self.end_time = None
        self.status = 'pending'
        
    @abstractmethod
    def get_runbook_name(self) -> str:
        """Obtener el nombre del runbook"""
        pass
    
    @abstractmethod
    def get_severity(self) -> str:
        """Obtener la severidad del runbook"""
        pass
    
    @abstractmethod
    def investigate(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de investigación del incidente"""
        pass
    
    @abstractmethod
    def remediate(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fase de remediación del incidente"""
        pass
    
    @abstractmethod
    def verify(self, remediation_result: Dict[str, Any]) -> Dict[str, bool]:
        """Fase de verificación de la solución"""
        pass
    
    def execute(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar el runbook completo"""
        self.start_time = datetime.now()
        self.status = 'in_progress'
        
        print(f"\n{'='*60}")
        print(f"📋 EJECUTANDO RUNBOOK: {self.get_runbook_name()}")
        print(f"   Severidad: {self.get_severity()}")
        print(f"   Incidente: {incident.get('description', 'No description')}")
        print(f"{'='*60}")
        
        # Fase 1: Investigación
        print("\n🔍 FASE 1: INVESTIGACIÓN")
        print("-" * 40)
        investigation = self.investigate(incident)
        
        # Fase 2: Remedición
        print("\n🔧 FASE 2: REMEDIACIÓN")
        print("-" * 40)
        remediation = self.remediate(investigation)
        
        # Fase 3: Verificación
        print("\n✅ FASE 3: VERIFICACIÓN")
        print("-" * 40)
        verification = self.verify(remediation)
        
        # Finalizar
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.status = 'completed' if verification.get('success', False) else 'failed'
        
        # Resumen
        result = {
            'runbook': self.get_runbook_name(),
            'severity': self.get_severity(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': duration,
            'status': self.status,
            'investigation': investigation,
            'remediation': remediation,
            'verification': verification
        }
        
        self.execution_log.append(result)
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN DE EJECUCIÓN")
        print(f"   Runbook: {self.get_runbook_name()}")
        print(f"   Duración: {duration:.1f} segundos")
        print(f"   Estado: {'✅ COMPLETADO' if verification.get('success', False) else '❌ FALLIDO'}")
        print(f"{'='*60}")
        
        return result
    
    def _execute_step(self, step_num: int, action: str, details: str, command: str = "N/A", estimated_time: str = "N/A") -> None:
        """Ejecutar un paso individual del runbook"""
        print(f"\n   📌 Paso {step_num}: {action}")
        print(f"      Detalles: {details}")
        print(f"      Comando: {command}")
        print(f"      Tiempo estimado: {estimated_time}")
        time.sleep(0.3)  # Simular ejecución
        print(f"      ✅ Paso {step_num} completado")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Registrar mensaje en el log"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.execution_log.append(log_entry)
        print(f"[{timestamp}] {level}: {message}")
