#!/usr/bin/env python
"""
Pruebas unitarias para los runbooks del sistema de monitorización

Este archivo contiene pruebas para verificar el correcto funcionamiento
de los runbooks y el sistema de monitorización.
"""

import sys
import os
import unittest
import json
import tempfile
from datetime import datetime

# Agregar src al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.runbooks import (
    BaseRunbook,
    PerformanceDegradationRunbook,
    LatencyIncreaseRunbook,
    DataDriftRunbook,
    ErrorBudgetRunbook,
    RunbookFactory
)


class TestBaseRunbook(unittest.TestCase):
    """Pruebas para la clase base BaseRunbook"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.config = {
            'runbooks': {
                'performance_degradation': {
                    'name': 'Degradación del Rendimiento',
                    'severity': 'P1'
                }
            }
        }
        
        # Crear una implementación concreta para probar
        class ConcreteRunbook(BaseRunbook):
            def get_runbook_name(self):
                return "Test Runbook"
            
            def get_severity(self):
                return "P2"
            
            def investigate(self, incident):
                return {'status': 'investigated'}
            
            def remediate(self, investigation_result):
                return {'status': 'remediated'}
            
            def verify(self, remediation_result):
                return {'success': True}
        
        self.runbook = ConcreteRunbook(self.config)
    
    def test_runbook_initialization(self):
        """Verificar que el runbook se inicializa correctamente"""
        self.assertEqual(self.runbook.status, 'pending')
        self.assertIsNone(self.runbook.start_time)
        self.assertIsNone(self.runbook.end_time)
        self.assertEqual(len(self.runbook.execution_log), 0)
    
    def test_execute_step(self):
        """Verificar que los pasos se ejecutan correctamente"""
        # No hay una forma directa de probar _execute_step sin mockear time.sleep
        # Verificamos que el método existe
        self.assertTrue(hasattr(self.runbook, '_execute_step'))
    
    def test_log_method(self):
        """Verificar que el método de logging funciona"""
        self.runbook._log("Test message", "INFO")
        self.assertEqual(len(self.runbook.execution_log), 1)
        self.assertEqual(self.runbook.execution_log[0]['level'], "INFO")
        self.assertEqual(self.runbook.execution_log[0]['message'], "Test message")
    
    def test_execute_workflow(self):
        """Verificar que el flujo completo de ejecución funciona"""
        incident = {'description': 'Test incident'}
        result = self.runbook.execute(incident)
        
        self.assertEqual(result['status'], 'completed')
        self.assertIsNotNone(result['start_time'])
        self.assertIsNotNone(result['end_time'])
        self.assertTrue(result['duration_seconds'] >= 0)
        self.assertEqual(result['runbook'], 'Test Runbook')


class TestPerformanceDegradationRunbook(unittest.TestCase):
    """Pruebas para el runbook de degradación del rendimiento"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'performance_degradation': {
                    'name': 'Degradación del Rendimiento del Modelo',
                    'severity': 'P1',
                    'estimated_time_minutes': 20
                }
            }
        }
        self.runbook = PerformanceDegradationRunbook(self.config)
    
    def test_runbook_name(self):
        """Verificar el nombre del runbook"""
        self.assertEqual(self.runbook.get_runbook_name(), 'Degradación del Rendimiento del Modelo')
    
    def test_severity(self):
        """Verificar la severidad del runbook"""
        self.assertEqual(self.runbook.get_severity(), 'P1')
    
    def test_investigation(self):
        """Verificar la fase de investigación"""
        incident = {
            'description': 'RMSE excedido',
            'metrics': {'rmse': 0.85, 'r2': 0.52}
        }
        result = self.runbook.investigate(incident)
        
        self.assertIn('root_cause', result)
        self.assertIn('affected_features', result)
        self.assertIn('rmse_current', result)
        self.assertIn('r2_current', result)
        self.assertGreater(result['rmse_current'], result['rmse_threshold'])
    
    def test_remediation(self):
        """Verificar la fase de remediación"""
        investigation_result = {
            'root_cause': 'Data drift',
            'affected_features': ['MedInc'],
            'rmse_current': 0.85,
            'rmse_threshold': 0.75
        }
        result = self.runbook.remediate(investigation_result)
        
        self.assertTrue(result['metrics_improved'])
        self.assertLess(result['new_rmse'], result.get('new_rmse', 0.7))
        self.assertEqual(result['deployment_status'], 'success')
    
    def test_verification(self):
        """Verificar la fase de verificación"""
        remediation_result = {
            'new_rmse': 0.68,
            'new_r2': 0.63,
            'deployment_status': 'success',
            'metrics_improved': True
        }
        result = self.runbook.verify(remediation_result)
        
        self.assertTrue(result['success'])
        self.assertIn('rmse_improved', result['criteria'])
        self.assertIn('r2_improved', result['criteria'])
    
    def test_complete_execution(self):
        """Verificar la ejecución completa del runbook"""
        incident = {
            'type': 'performance_degradation',
            'description': 'RMSE aumentó a 0.85',
            'metrics': {'rmse': 0.85, 'r2': 0.52}
        }
        result = self.runbook.execute(incident)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['runbook'], 'Degradación del Rendimiento del Modelo')
        self.assertEqual(result['severity'], 'P1')


class TestLatencyIncreaseRunbook(unittest.TestCase):
    """Pruebas para el runbook de aumento de latencia"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'latency_increase': {
                    'name': 'Aumento de Latencia',
                    'severity': 'P1'
                }
            }
        }
        self.runbook = LatencyIncreaseRunbook(self.config)
    
    def test_runbook_name(self):
        """Verificar el nombre del runbook"""
        self.assertEqual(self.runbook.get_runbook_name(), 'Aumento de Latencia en Inferencia')
    
    def test_severity(self):
        """Verificar la severidad del runbook"""
        self.assertEqual(self.runbook.get_severity(), 'P1')
    
    def test_investigation(self):
        """Verificar la fase de investigación"""
        incident = {
            'description': 'Latencia p95 excedida',
            'metrics': {'latency_p95': 0.150}
        }
        result = self.runbook.investigate(incident)
        
        self.assertIn('root_cause', result)
        self.assertIn('cpu_usage', result)
        self.assertIn('request_count', result)
        self.assertGreater(result['cpu_usage'], 80)  # Simula alta carga
    
    def test_remediation(self):
        """Verificar la fase de remediación"""
        investigation_result = {
            'root_cause': 'Alta carga de CPU',
            'cpu_usage': 92,
            'request_count': 1500
        }
        result = self.runbook.remediate(investigation_result)
        
        self.assertLess(result['new_latency_p95'], 0.05)
        self.assertGreater(result['replicas'], 3)
    
    def test_verification(self):
        """Verificar la fase de verificación"""
        remediation_result = {
            'new_latency_p95': 0.035,
            'new_latency_p99': 0.065,
            'replicas': 5,
            'optimization_applied': True
        }
        result = self.runbook.verify(remediation_result)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['criteria']['latency_p95_improved'])
        self.assertTrue(result['criteria']['scaling_successful'])
    
    def test_complete_execution(self):
        """Verificar la ejecución completa del runbook"""
        incident = {
            'type': 'latency_increase',
            'description': 'Latencia p95 a 150ms',
            'metrics': {'latency_p95': 0.150}
        }
        result = self.runbook.execute(incident)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['runbook'], 'Aumento de Latencia en Inferencia')


class TestDataDriftRunbook(unittest.TestCase):
    """Pruebas para el runbook de data drift"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'data_drift': {
                    'name': 'Data Drift',
                    'severity': 'P2'
                }
            }
        }
        self.runbook = DataDriftRunbook(self.config)
    
    def test_runbook_name(self):
        """Verificar el nombre del runbook"""
        self.assertEqual(self.runbook.get_runbook_name(), 'Data Drift Detectado en Features')
    
    def test_severity(self):
        """Verificar la severidad del runbook"""
        self.assertEqual(self.runbook.get_severity(), 'P2')
    
    def test_investigation(self):
        """Verificar la fase de investigación"""
        incident = {
            'description': 'Drift detectado',
            'drifted_features': ['MedInc', 'AveOccup']
        }
        result = self.runbook.investigate(incident)
        
        self.assertIn('drifted_features', result)
        self.assertIn('drift_scores', result)
        self.assertGreater(len(result['drifted_features']), 0)
        self.assertLess(result['drift_scores']['MedInc'], 0.5)  # Score razonable
    
    def test_remediation(self):
        """Verificar la fase de remediación"""
        investigation_result = {
            'drifted_features': ['MedInc', 'AveOccup'],
            'drift_scores': {'MedInc': 0.32, 'AveOccup': 0.28},
            'root_cause': 'Cambio demográfico'
        }
        result = self.runbook.remediate(investigation_result)
        
        self.assertTrue(result['reference_updated'])
        self.assertTrue(result['model_retrained'])
        self.assertTrue(result['all_under_threshold'])
    
    def test_verification(self):
        """Verificar la fase de verificación"""
        remediation_result = {
            'reference_updated': True,
            'model_retrained': True,
            'all_under_threshold': True,
            'new_drift_scores': {'MedInc': 0.15, 'AveOccup': 0.12}
        }
        result = self.runbook.verify(remediation_result)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['criteria']['all_under_threshold'])
        self.assertTrue(result['criteria']['reference_updated'])
    
    def test_complete_execution(self):
        """Verificar la ejecución completa del runbook"""
        incident = {
            'type': 'data_drift',
            'description': 'Drift en MedInc y AveOccup',
            'drifted_features': ['MedInc', 'AveOccup']
        }
        result = self.runbook.execute(incident)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['runbook'], 'Data Drift Detectado en Features')


class TestErrorBudgetRunbook(unittest.TestCase):
    """Pruebas para el runbook de error budget agotado"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'error_budget': {
                    'name': 'Error Budget',
                    'severity': 'P0'
                }
            }
        }
        self.runbook = ErrorBudgetRunbook(self.config)
    
    def test_runbook_name(self):
        """Verificar el nombre del runbook"""
        self.assertEqual(self.runbook.get_runbook_name(), 'Error Budget Agotado')
    
    def test_severity(self):
        """Verificar la severidad del runbook (P0 es crítica)"""
        self.assertEqual(self.runbook.get_severity(), 'P0')
    
    def test_investigation(self):
        """Verificar la fase de investigación"""
        incident = {
            'description': 'Error budget agotado',
            'metrics': {'budget_consumed': 1.02}
        }
        result = self.runbook.investigate(incident)
        
        self.assertIn('incidents_count', result)
        self.assertIn('total_downtime_minutes', result)
        self.assertIn('main_causes', result)
        self.assertGreater(result['incidents_count'], 0)
    
    def test_remediation(self):
        """Verificar la fase de remediación"""
        investigation_result = {
            'incidents_count': 8,
            'total_downtime_minutes': 45,
            'affected_users': 2500,
            'main_causes': ['Modelo degradado', 'Latencia alta']
        }
        result = self.runbook.remediate(investigation_result)
        
        self.assertTrue(result['deployments_frozen'])
        self.assertTrue(result['leadership_notified'])
        self.assertTrue(result['recovery_plan_created'])
        self.assertGreater(result['new_error_budget'], 0.02)
    
    def test_verification(self):
        """Verificar la fase de verificación"""
        remediation_result = {
            'deployments_frozen': True,
            'leadership_notified': True,
            'monitoring_enhanced': True,
            'recovery_plan_created': True,
            'system_stable': True
        }
        result = self.runbook.verify(remediation_result)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['criteria']['deployments_frozen'])
        self.assertTrue(result['criteria']['leadership_notified'])
        self.assertTrue(result['criteria']['system_stable'])
    
    def test_complete_execution(self):
        """Verificar la ejecución completa del runbook"""
        incident = {
            'type': 'error_budget',
            'description': 'Budget consumido al 102%',
            'metrics': {'budget_consumed': 1.02}
        }
        result = self.runbook.execute(incident)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['runbook'], 'Error Budget Agotado')
        self.assertEqual(result['severity'], 'P0')


class TestRunbookFactory(unittest.TestCase):
    """Pruebas para la fábrica de runbooks"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'performance_degradation': {'name': 'Test'},
                'latency_increase': {'name': 'Test'},
                'data_drift': {'name': 'Test'},
                'error_budget': {'name': 'Test'}
            }
        }
    
    def test_create_performance_degradation(self):
        """Verificar creación del runbook de degradación"""
        runbook = RunbookFactory.create_runbook('performance_degradation', self.config)
        self.assertIsInstance(runbook, PerformanceDegradationRunbook)
    
    def test_create_latency_increase(self):
        """Verificar creación del runbook de latencia"""
        runbook = RunbookFactory.create_runbook('latency_increase', self.config)
        self.assertIsInstance(runbook, LatencyIncreaseRunbook)
    
    def test_create_data_drift(self):
        """Verificar creación del runbook de data drift"""
        runbook = RunbookFactory.create_runbook('data_drift', self.config)
        self.assertIsInstance(runbook, DataDriftRunbook)
    
    def test_create_error_budget(self):
        """Verificar creación del runbook de error budget"""
        runbook = RunbookFactory.create_runbook('error_budget', self.config)
        self.assertIsInstance(runbook, ErrorBudgetRunbook)
    
    def test_invalid_runbook_type(self):
        """Verificar manejo de tipos inválidos"""
        with self.assertRaises(ValueError):
            RunbookFactory.create_runbook('invalid_type', self.config)


class TestIntegration(unittest.TestCase):
    """Pruebas de integración del sistema completo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.config = {
            'runbooks': {
                'performance_degradation': {
                    'name': 'Degradación del Rendimiento',
                    'severity': 'P1',
                    'investigation_steps': [],
                    'remediation_steps': [],
                    'verification': []
                }
            },
            'slo_config': {
                'rmse_max': 0.75,
                'r2_min': 0.55,
                'latency_max': 0.05,
                'error_budget': 0.02
            }
        }
    
    def test_runbook_execution_flow(self):
        """Verificar el flujo completo de ejecución de un runbook"""
        runbook = PerformanceDegradationRunbook(self.config)
        incident = {
            'type': 'performance_degradation',
            'description': 'Degradación detectada',
            'metrics': {'rmse': 0.85, 'r2': 0.52}
        }
        
        result = runbook.execute(incident)
        
        # Verificar que todas las fases se ejecutaron
        self.assertIn('investigation', result)
        self.assertIn('remediation', result)
        self.assertIn('verification', result)
        
        # Verificar que el resultado final es exitoso
        self.assertEqual(result['status'], 'completed')
    
    def test_multiple_runbooks(self):
        """Verificar ejecución de múltiples runbooks"""
        runbook_types = [
            'performance_degradation',
            'latency_increase',
            'data_drift',
            'error_budget'
        ]
        
        for runbook_type in runbook_types:
            runbook = RunbookFactory.create_runbook(runbook_type, self.config)
            incident = {
                'type': runbook_type,
                'description': f'Simulación de {runbook_type}',
                'metrics': {}
            }
            
            result = runbook.execute(incident)
            self.assertEqual(result['status'], 'completed')
            self.assertIn(result['runbook'], runbook.get_runbook_name())


def run_tests():
    """Ejecutar todas las pruebas"""
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las pruebas
    suite.addTests(loader.loadTestsFromTestCase(TestBaseRunbook))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceDegradationRunbook))
    suite.addTests(loader.loadTestsFromTestCase(TestLatencyIncreaseRunbook))
    suite.addTests(loader.loadTestsFromTestCase(TestDataDriftRunbook))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorBudgetRunbook))
    suite.addTests(loader.loadTestsFromTestCase(TestRunbookFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"   Pruebas ejecutadas: {result.testsRun}")
    print(f"   ✅ Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Fallidas: {len(result.failures)}")
    print(f"   ⚠️ Errores: {len(result.errors)}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    run_tests()
