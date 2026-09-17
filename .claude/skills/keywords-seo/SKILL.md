---
name: keywords-seo
description: Keywords, etiquetas, descripción y hueco de búsqueda. Se invoca ante "qué keywords uso", "optimiza el SEO", "dame las etiquetas", "cómo me encuentran".
---

# Keywords y SEO

## ORDEN DE EJECUCIÓN

1. **La verdad de campo primero**
   ```
   python3 tools/yt_search_terms.py --days 90 --tipo YT_SEARCH
   python3 tools/yt_search_terms.py --days 90 --tipo RELATED_VIDEO
   ```
   Estos son los términos **reales** con los que la gente llega, y los vídeos
   que están sugiriendo los tuyos. No es estimación. Empezar por aquí y no por
   el proxy es lo que separa esta skill de un generador genérico de keywords.

2. **Expandir con el proxy**
   `python3 tools/kw_research.py --kw "semilla 1; semilla 2" --profundo`
   `--profundo` expande con el alfabeto: 26 llamadas más de autocompletado, sin
   coste de cuota de API. `heuristic`.

3. **Hueco competitivo**
   `python3 tools/yt_search.py --query "keyword candidata"`
   **Cuesta 100 unidades de cuota por consulta.** Se cachea 24 h. Mirar la
   antigüedad mediana de los resultados: un top viejo es un hueco de
   actualización.

4. Etiquetas y descripción, cruzando lo real del paso 1 con lo expandido del 2.

## FUENTES

Paso 1 `youtube_api` — es el único dato duro de esta skill. Pasos 2 y 3
`heuristic` y `derived`. Al dar un score hay que decir que es propio.

## SALIDA

- Keyword principal, con la evidencia de por qué (preferiblemente del paso 1).
- 8-12 etiquetas.
- Descripción de 120-180 palabras con las keywords integradas de forma natural.
- Si alguna keyword sale solo del proxy y no del tráfico real, se marca.
