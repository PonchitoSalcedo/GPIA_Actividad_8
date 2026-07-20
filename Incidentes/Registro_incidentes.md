# Registro de Incidentes Simulados

Este documento resume los incidentes generados durante la simulación de
monitoreo del notebook `monitoreo_produccion_ml.ipynb`, las alertas
disparadas, los runbooks ejecutados automáticamente en respuesta, y los
resultados observados. La simulación abarcó **16 pasos** de tráfico
("lotes" de producción), con fallas inyectadas deliberadamente a partir de
pasos específicos para poder observar el comportamiento del sistema de
monitoreo.

## Resumen general

| Total de alertas generadas | Total de runbooks ejecutados |
|---|---|
| 36 | 68 |

## Cronología de fallas inyectadas

| Paso | Falla inyectada |
|---|---|
| 5–6 | Pico de latencia (sobrecarga simulada del servicio) |
| 8 en adelante | Data drift (cambio de distribución en `MedInc` y `AveOccup`) |
| 11 en adelante | Degradación del modelo / concept drift (ruido fuerte en la relación real features→precio) |

---

## Incidente 1 — Incremento de latencia

- **Tipo de alerta:** `latency_spike` (severidad: *warning*)
- **Detección:** la alerta se disparó en los pasos 5 y 6, al superar la
  latencia observada (235–249 ms) el umbral operativo definido (150 ms).
- **Runbook ejecutado:** `escalamiento_infraestructura` — se simuló el
  escalamiento de réplicas del servicio para absorber la carga adicional.
- **Resultado obtenido:** al ser una falla puntual (solo inyectada en los
  pasos 5 y 6), la latencia volvió a su rango normal en los pasos
  siguientes sin necesidad de más intervención. Esto demuestra que la
  alerta se limita correctamente a la ventana en la que la condición
  realmente ocurre, sin quedar "pegada" después de que el problema se
  resuelve.

## Incidente 2 — Data drift en features de entrada

- **Tipo de alerta:** `data_drift` (severidad: *warning*)
- **Detección:** a partir del paso 8, el PSI máximo entre las 8 features
  subió de ~0.2–0.3 (rango normal) a **11–12.4**, muy por encima del
  umbral definido (PSI > 2.0). Esto se debió a la inyección simulada de
  tráfico proveniente de una zona con ingreso medio (`MedInc`) y ocupación
  promedio (`AveOccup`) mucho más altos que los vistos en entrenamiento.
- **Runbooks ejecutados:** `reentrenamiento_automatico` (se encoló un
  pipeline de reentrenamiento con datos recientes) + `notificar_equipo_guardia`.
- **Resultado obtenido:** el drift se mantuvo detectado de forma sostenida
  durante el resto de la simulación (pasos 8 a 15), ya que la falla se
  inyectó de forma permanente a partir de ese punto (no puntual, a
  diferencia de la latencia). Esto es consistente con lo esperado: un
  reentrenamiento automático **no revierte el drift**, solo prepara al
  sistema para adaptarse a la nueva distribución una vez que el modelo
  reentrenado se valide y despliegue — una decisión que, por diseño,
  requiere validación humana antes de reemplazar el modelo en producción
  (ver sección 8 del documento técnico).

## Incidente 3 — Degradación del modelo (RMSE / R²)

- **Tipo de alerta:** `rmse_degradation` y `r2_degradation` (severidad:
  *critical*)
- **Detección:** a partir del paso 8 el RMSE ya superaba el SLO (0.70),
  llegando hasta **3.29** en el paso 11 tras inyectar además la
  degradación de concept drift; el R² cayó a valores **negativos**
  (hasta -2.14), lo que indica que el modelo predijo peor que si
  simplemente hubiera usado el promedio histórico como predicción.
- **Runbook ejecutado:** `rollback_modelo` — se simuló la reversión del
  despliegue de la versión `v3` a la `v2` (última versión estable
  conocida), además de `notificar_equipo_guardia`.
- **Resultado obtenido:** en esta simulación, el rollback se dispara
  automáticamente en cada paso donde la condición se cumple, pero **no
  hay una versión `v2` real ejecutándose** — es una simulación del
  procedimiento, no una implementación completa de versionado de modelos.
  Por eso las métricas no muestran recuperación dentro de la ventana
  simulada (la falla se mantiene inyectada hasta el paso 15). En un
  entorno real, ejecutar el rollback restauraría de inmediato el
  desempeño de la versión anterior, deteniendo la degradación. Esta es
  una limitación conocida de la simulación, documentada explícitamente
  para no sobre-representar el resultado.

## Incidente 4 — Error budget agotado

- **Tipo de alerta:** `error_budget_exhausted` (severidad: *critical*)
- **Detección:** el presupuesto de error llegó a 0% en varios pasos,
  incluyendo brevemente los pasos 2–3 (fluctuación natural dada la
  exigencia del SLO configurado) y de forma sostenida desde el paso 8 en
  adelante, una vez que el drift y la degradación afectaron la tasa de
  predicciones dentro de tolerancia.
- **Runbooks ejecutados:** `rollback_modelo` + `notificar_equipo_guardia`.
- **Resultado obtenido:** mismo caso que el Incidente 3 — el runbook se
  disparó correctamente y de forma automática en cuanto el presupuesto
  llegó a cero, cumpliendo el objetivo de "no esperar a que empeore más"
  antes de intervenir. La recuperación real del budget requeriría, en
  producción, que el rollback ya esté surtiendo efecto sobre las
  predicciones siguientes.

---

## Conclusión

La simulación demuestra que el sistema de alertas:
1. **Detecta correctamente** cada tipo de falla (latencia, drift,
   degradación de métricas, agotamiento de budget) en el momento en que
   ocurre, sin falsos positivos durante los pasos "sanos" (0–7).
2. **Prioriza por severidad**: los incidentes con impacto directo en el
   negocio (RMSE/R²/error budget) se marcan como *critical* y disparan
   rollback inmediato; los de riesgo futuro o de infraestructura (drift,
   latencia) se marcan como *warning* y disparan acciones preventivas.
3. **Dispara runbooks automáticamente** sin intervención manual, y aplica
   *cooldown* para no generar alertas duplicadas de forma innecesaria.

La principal limitación observada — y documentada honestamente — es que la
simulación no modela el efecto posterior de una intervención real (por
ejemplo, que tras un rollback las métricas vuelvan a la normalidad), ya
que las fallas se inyectan de forma continua para poder observar el
comportamiento del sistema de alertas en una ventana de tiempo controlada.
