# Actividad 8 — Sistema de Monitorización Proactiva para un Modelo en Producción

Sistema de observabilidad y monitorización proactiva para un modelo de Machine
Learning en producción, aplicado sobre el **California Housing Dataset**
(problema de regresión: predicción del valor medio de vivienda). El sistema
integra métricas, logs y trazas bajo un enfoque de observabilidad moderna,
usando **MLflow** para el seguimiento del desempeño y la detección de anomalías,
incluyendo **data drift**.

## Descripción general

A partir de un conjunto de indicadores definidos sobre el modelo (RMSE, MAE, R²,
latencia y drift), el sistema:

- Registra métricas, logs estructurados y trazas de cada lote de datos procesado.
- Detecta **data drift** en las 8 features de entrada mediante PSI
  (Population Stability Index) y la prueba de Kolmogorov-Smirnov.
- Configura **alertas inteligentes** alineadas a SLOs (Service Level Objectives)
  y error budgets, priorizadas según su severidad e impacto operativo.
- Simula **escenarios de falla** (pico de latencia, data drift, degradación /
  concept drift) y dispara automáticamente **runbooks** de respuesta
  (rollback, reentrenamiento, escalamiento, notificación a guardia).
- Muestra un **dashboard operativo** con la evolución de las métricas clave.

## Estructura del repositorio

```
├── README.md
├── notebooks/
│   └── monitoreo_produccion_ml.ipynb   # Notebook ejecutado (código + resultados)
├── documento_tecnico/
│   └── documento_tecnico.docx          # Documento técnico (diseño e indicadores)
├── evidencias/
│   └── ...                             # Capturas de MLflow, dashboards y alertas
├── incidentes/
│   └── registro_incidentes.md          # Bitácora de incidentes simulados
└── mlflow.db                           # Base de datos SQLite generada por MLflow
```

## Indicadores monitoreados

| Categoría | Indicador | Descripción |
|---|---|---|
| Métricas | RMSE, MAE, R² | Desempeño del modelo de regresión por lote |
| Métricas | Latencia (ms) | Tiempo de respuesta de la predicción |
| Métricas | PSI por feature | Magnitud del cambio de distribución respecto al set de referencia |
| Métricas | Error budget restante (%) | Presupuesto de error disponible según el SLO de tasa de éxito |
| Logs | Eventos estructurados (JSON) | Nivel, mensaje y contexto de cada evento del sistema |
| Trazas | `trace_id` por lote | Duración y metadatos de cada lote procesado |

## SLOs y error budget

Los SLOs se calibran dinámicamente a partir del desempeño del modelo en un
conjunto de *holdout* (no visto durante el entrenamiento), en lugar de fijarse
de forma arbitraria:

- **RMSE máximo aceptable** = 1.3× el RMSE observado en holdout
- **MAE máximo aceptable** = 1.3× el MAE observado en holdout
- **R² mínimo aceptable** = R² de holdout − 0.15
- **Umbral de drift (PSI)** = 2.0

El **error budget** se calcula sobre una ventana móvil de predicciones
individuales: una predicción es "exitosa" si su error absoluto está por debajo
de una tolerancia calibrada (1.5× el MAE de holdout).

## Alertas y priorización por impacto

| Alerta | Severidad | Runbook disparado |
|---|---|---|
| `data_drift` | warning | Reentrenamiento automático + notificación a guardia |
| `latency_spike` | warning | Escalamiento de infraestructura |
| `rmse_degradation` | critical | Rollback a versión anterior |
| `r2_degradation` | critical | Rollback a versión anterior |
| `error_budget_exhausted` | critical | Rollback a versión anterior + notificación a guardia |

Las alertas aplican un mecanismo de *cooldown* para evitar ruido (alert
fatigue): una misma condición no vuelve a disparar una alerta si ya se generó
una reciente para ese mismo tipo de incidente.

## Cómo ejecutar el notebook

1. Abre `notebooks/monitoreo_produccion_ml.ipynb` en Google Colab.
2. Ejecuta las celdas en orden (Entorno de ejecución → Ejecutar todas).
3. La primera celda instala MLflow; el resto de librerías (`numpy`, `pandas`,
   `scikit-learn`, `matplotlib`, `scipy`) ya vienen preinstaladas en Colab.
4. Al final del notebook se genera el dashboard operativo y las tablas de
   alertas / runbooks ejecutados.

### Requisitos
- Python 3.10+
- `mlflow`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `scipy`

## Incidentes simulados

Se simulan al menos dos escenarios de falla sobre el flujo de datos:

1. **Data drift**: se simula la llegada de tráfico de una zona con ingreso
   medio (`MedInc`) y ocupación promedio (`AveOccup`) significativamente más
   altos que los vistos en entrenamiento.
2. **Degradación del modelo (concept drift)**: se simula un cambio en la
   relación real entre las features y el valor de la vivienda (p. ej. una
   corrección de mercado), que el modelo entrenado no puede anticipar.
3. **Incremento de latencia**: se simula una sobrecarga puntual del servicio.

El detalle de cada incidente, la alerta generada, el runbook ejecutado y el
resultado tras la intervención se documentan en
[`incidentes/registro_incidentes.md`](./incidentes/registro_incidentes.md).

## Herramientas utilizadas

- **MLflow** — tracking de métricas, parámetros y artefactos del modelo
  (backend SQLite local).
- **scikit-learn** — modelo `RandomForestRegressor` y dataset California Housing.
- **scipy** — pruebas estadísticas para detección de drift (KS-test).
- **matplotlib** — dashboard operativo.

## Autor
Luis Alfonso Salcedo Peña

Repositorio desarrollado para la Actividad 8 del curso de Producción y
Observabilidad de Modelos de IA.
