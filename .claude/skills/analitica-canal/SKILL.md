---
name: analitica-canal
description: Auditoría y diagnóstico del canal propio con datos reales — rendimiento, retención, tráfico, audiencia y comparación con snapshots anteriores. Se invoca ante "¿cómo va el canal?", "audita mis vídeos", "por qué ha bajado", "qué está funcionando".
---

# Auditoría del canal

## CUÁNDO

Diagnóstico de rendimiento, informe periódico, "¿por qué cayó este vídeo?",
"¿qué funciona y qué no?", comparación entre periodos.

## ORDEN DE EJECUCIÓN

1. **Línea base e histórico**
   `python3 tools/yt_report.py --days 28`
   Da el estado general, el top de vídeos, tráfico, audiencia y geografía, y
   anexa un snapshot. Si ya hay snapshots previos devuelve
   `cambio_desde_ultimo_snapshot`: **ese delta es el diagnóstico real**, no la
   foto fija.

2. **Ordenar por retención, no solo por vistas**
   `python3 tools/yt_top_videos.py --days 90 --by-retention`
   Un vídeo con pocas vistas y retención alta es una señal de formato; uno con
   muchas vistas y retención baja es un problema de promesa.

3. **De dónde viene la gente**
   `python3 tools/yt_traffic.py --days 28`
   `python3 tools/yt_search_terms.py --days 90`
   El segundo es el que aporta: son los términos **reales** con los que llegan.
   Dependencia de suscriptores por encima del 50% significa que el canal no está
   captando fuera de su base.

4. **Dónde abandonan** — sobre los 3 vídeos más relevantes del paso 2
   `python3 tools/yt_retention.py --video ID`
   Mirar `hitos`: `intro_30s`, `re_hook_min3`, `re_hook_min6`. Si la caída está
   en la intro, el problema es la promesa; si está en un re-hook, el problema es
   la estructura. Si existe `memoria/sop/scripting_sop.md`, se contrasta contra él.

5. **Cruce obligatorio antes de concluir**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.0`
   Sin esto, no se puede distinguir un problema del canal de un movimiento del
   nicho entero.

6. Comparar contra lo que ya se sabía: `memoria/MEMORY.md`, en especial los
   ficheros `outcome_*`, que llevan la predicción hecha antes del vídeo frente
   al resultado real.

**El orden se adapta a los datos.** Si el paso 1 revela una caída brusca, se va
directo al 4 sobre el vídeo afectado. Los datos mandan sobre el manual.

## FUENTES

Pasos 1-4 `youtube_api` (agregados y porcentajes `derived`). Paso 5 `derived`.
Ninguna heurística: esta skill no estima nada.

## SALIDA

1. Titular: qué ha cambiado y desde cuándo, con la fecha del dato.
2. Tabla de estado con el delta contra el snapshot anterior.
3. Diagnóstico: 2-3 causas, cada una respaldada por una cifra concreta.
4. Acción prioritaria: una sola, la de mayor impacto.

Si falta CTR para cerrar el diagnóstico, se dice y se apunta a
`tools/ingest_studio_csv.py`. Ver `LIMITES.md`.
