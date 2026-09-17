---
name: identidad-canal
description: Posicionamiento del canal, diferenciación frente al vecindario competitivo y reencuadre de nicho. Se invoca ante "cómo me posiciono", "en qué me diferencio", "hacia dónde llevo el canal", "quién es mi competencia real".
---

# Identidad y posicionamiento

## ORDEN DE EJECUCIÓN

1. **Dónde está el canal hoy**
   `python3 tools/yt_channel_stats.py`

2. **Cuál es el vecindario real**
   `python3 tools/yt_outliers_channels.py --min-ratio 1.5`
   Con umbral bajo, porque aquí interesa el patrón editorial de cada canal, no
   solo sus picos.

3. **Para quién se está produciendo de hecho**
   ```
   python3 tools/yt_demographics.py --days 90
   python3 tools/yt_geography.py --days 90
   ```
   El contraste entre la audiencia que se cree tener y la que se tiene es donde
   suele estar el hallazgo.

4. **Con qué se llega** — señal de posicionamiento percibido
   `python3 tools/yt_search_terms.py --days 180`
   Los términos con los que la gente busca y encuentra el canal dicen cómo se
   le percibe, que no siempre es como se quiere posicionar.

5. Actualizar `memoria/channel_positioning.md` si el análisis cambia algo
   estable. Solo si es estable: un dato de una semana no reposiciona un canal.

## FUENTES

Pasos 1, 3 y 4 `youtube_api`. Paso 2 `derived`.

## SALIDA

- Posición actual, con cifras y fecha.
- Vecindario: qué canales ocupan el mismo espacio y en qué se diferencian.
- El hueco concreto, con la evidencia que lo respalda.
- Qué cambiaría en la línea editorial, y qué NO hay que tocar.
