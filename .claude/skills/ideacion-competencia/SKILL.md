---
name: ideacion-competencia
description: Ideas de próximos vídeos a partir de outliers reales de competencia e inspiración. Se invoca ante "ideas para la semana", "qué grabo ahora", "qué está petando en mi nicho", "analiza a mi competencia".
---

# Ideación desde competencia

## CUÁNDO

Ideas de próximos vídeos, análisis de competencia, "qué está funcionando en el
nicho", revisión semanal de oportunidades.

## ORDEN DE EJECUCIÓN

1. **Outliers de los canales configurados**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0 --sample 30`
   17 canales de competencia y 7 de inspiración en `config/channels_lists.json`.
   Si salen muy pocos, bajar a `--min-ratio 1.5` antes de dar por hecho que no
   hay nada.

2. **Outliers guardados a mano**
   `python3 tools/yt_outliers_playlist.py --days 7`
   Lo que se ha ido guardando durante la semana. Si la playlist no está
   configurada, la herramienta lo dice con código 4; no es un fallo.

3. **Filtrar por relevancia antes de gastar cuota**
   Descartar por título lo que no encaje con el canal. Solo entonces:
   `python3 tools/yt_transcript.py --video ID --plano`
   sobre los que sí encajan. Transcribir todo es tirar tiempo.

4. **Validar cada idea**
   `python3 tools/kw_research.py --kw "idea 1; idea 2; idea 3"`
   Score `heuristic`: ordena las ideas entre sí, no mide demanda absoluta.

5. **Priorizar contra el canal, no en abstracto**
   Leer `memoria/creator_profile.md` y `memoria/MEMORY.md`. Una idea con buen
   outlier pero que no encaja con el arquetipo del canal se descarta y se dice
   por qué.

**El orden se adapta.** Si el paso 1 devuelve un outlier de 10x, se prioriza y
se profundiza en él aunque el manual dijera transcribir todo primero.

## FUENTES

Pasos 1-2 `derived` (el ratio es un cálculo sobre la media de cada canal).
Paso 3 `youtube_api`. Paso 4 `heuristic` — declararlo.

## SALIDA

Ideas priorizadas. Cada una con:
- El outlier que la respalda: título, canal, ratio y URL **verbatim** de la
  herramienta.
- Por qué funcionó allí y qué cambia al traerla a este canal.
- El ángulo propio, no una copia.

Al final, una recomendación única y el motivo.
