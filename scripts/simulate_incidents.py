#!/usr/bin/env python
"""
Script para simular incidentes y ejecutar runbooks
"""
import sys
import os
import json
from datetime import datetime

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.runbooks import RunbookFactory

def load_config():
    """Cargar configuración desde archivo YAML"""
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'alert_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def simulate_performance_degradation():
    """Simular degradación del modelo"""
    print("\n" + "🔥"*30)
    print("SIMULANDO INCIDENTE: DEGRADACIÓN DEL MODELO")
    print("🔥"*30)
    
    incident = {
        'type': 'performance_degradation',
        'description': 'RMSE ha aumentado a 0.85, excediendo el umbral de 0.75',
        'metrics': {
            'rmse': 0.85,
            'r2': 0.52,
            'error_rate': 0.08
        },
        'timestamp': datetime.now().isoformat()
    }
    
    config = load_config()
    runbook = RunbookFactory.create_runbook('performance_degradation', config)
    result = runbook.execute(incident)
    
    return result

def simulate_latency_increase():
    """Simular aumento de latencia"""
    print("\n" + "🔥"*30)
    print("SIMULANDO INCIDENTE: AUMENTO DE LATENCIA")
    print("🔥"*30)
    
    incident = {
        'type': 'latency_increase',
        'description': 'Latencia p95 ha aumentado a 150ms, excediendo el umbral de 50ms',
        'metrics': {
            'latency_p95': 0.150,
            'latency_p99': 0.200,
            'throughput': 850
        },
        'timestamp': datetime.now().isoformat()
    }
    
    config = load_config()
    runbook = RunbookFactory.create_runbook('latency_increase', config)
    result = runbook.execute(incident)
    
    return result

def simulate_data_drift():
    """Simular data drift"""
    print("\n" + "🔥"*30)
    print("SIMULANDO INCIDENTE: DATA DRIFT DETECTADO")
    print("🔥"*30)
    
    incident = {
        'type': 'data_drift',
        'description': 'Drift detectado en features: MedInc (0.32), AveOccup (0.28)',
        'drifted_features': ['MedInc', 'AveOccup'],
        'drift_scores': {
            'MedInc': 0.32,
            'AveOccup': 0.28
        },
        'timestamp': datetime.now().isoformat()
    }
    
    config = load_config()
    runbook = RunbookFactory.create_runbook('data_drift', config)
    result = runbook.execute(incident)
    
    return result

def simulate_error_budget():
    """Simular error budget agotado"""
    print("\n" + "🔥"*30)
    print("SIMULANDO INCIDENTE: ERROR BUDGET AGOTADO")
    print("🔥"*30)
    
    incident = {
        'type': 'error_budget',
        'description': 'Error budget consumido al 102%, superando el límite del 100%',
        'metrics': {
            'budget_consumed': 1.02,
            'budget_limit': 1.0,
            'incidents_this_month': 8
        },
        'timestamp': datetime.now().isoformat()
    }
    
    config = load_config()
    runbook = RunbookFactory.create_runbook('error_budget', config)
    result = runbook.execute(incident)
    
    return result

def main():
    """Ejecutar todas las simulaciones"""
    print("\n" + "="*60)
    print("🚀 INICIANDO SIMULACIÓN DE INCIDENTES")
    print("="*60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'simulations': []
    }
    
    # Simular incidentes
    try:
        result = simulate_performance_degradation()
        results['simulations'].append({
            'type': 'performance_degradation', 
            'result': result
        })
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
    
    try:
        result = simulate_latency_increase()
        results['simulations'].append({
            'type': 'latency_increase', 
            'result': result
        })
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
    
    try:
        result = simulate_data_drift()
        results['simulations'].append({
            'type': 'data_drift', 
            'result': result
        })
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
    
    try:
        result = simulate_error_budget()
        results['simulations'].append({
            'type': 'error_budget', 
            'result': result
        })
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
    
    # Guardar resultados
    os.makedirs('evidence/logs', exist_ok=True)
    output_path = 'evidence/logs/runbook_executions.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE SIMULACIONES")
    print("="*60)
    
    for sim in results['simulations']:
        status = '✅' if sim['result']['status'] == 'completed' else '❌'
        print(f"{status} {sim['type']}: {sim['result']['status']}")
    
    print(f"\n📁 Resultados guardados en: {output_path}")
    print("="*60)

if __name__ == "__main__":
    main()
