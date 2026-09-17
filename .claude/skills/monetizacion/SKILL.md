---
name: monetizacion
description: Umbrales del Programa de Socios, proyección de suscriptores y horas de visualización. Se invoca ante "cuándo monetizo", "cuánto me falta para YPP", "voy a llegar a los requisitos".
---

# Monetización

## ORDEN DE EJECUCIÓN

1. **Estado frente a los umbrales**
   `python3 tools/yt_channel_stats.py`

2. **Tendencia real, no deseo**
   ```
   python3 tools/yt_analytics.py --days 90
   python3 tools/yt_report.py --days 28
   ```
   De ahí salen subs netos y minutos vistos por ventana. La proyección se hace
   sobre la tendencia medida, no sobre la mejor semana.

3. Proyectar. Toda proyección es `derived` y se declara como tal, con el
   supuesto a la vista ("al ritmo de los últimos 90 días").

## FUENTES

`youtube_api` para el estado, `derived` para la proyección.

## LÍMITES DE ESTA SKILL

- **No hay datos de ingresos.** El scope monetario está concedido pero ninguna
  herramienta pide métricas de revenue. No se estiman RPM ni ingresos.
- Los umbrales del Programa de Socios los fija YouTube y cambian por país y por
  tipo de contenido. Si hay duda sobre un requisito concreto, se dice y se
  apunta a la documentación oficial en vez de afirmarlo de memoria.

## SALIDA

Estado actual frente a cada umbral, ritmo medido, proyección con su supuesto
declarado, y la palanca de mayor impacto según los datos del canal.
