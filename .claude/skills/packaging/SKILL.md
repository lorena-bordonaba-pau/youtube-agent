---
name: packaging
description: Títulos, miniaturas y descripción de un vídeo, puntuados con la rúbrica calibrada del canal. Se invoca ante "dame títulos", "puntúa este título", "revisa mi miniatura", "mejora el packaging".
---

# Packaging: títulos y miniaturas

## CUÁNDO

Generar o evaluar títulos, diagnosticar una miniatura, revisar el conjunto
título+miniatura, escribir descripción y etiquetas.

## ORDEN DE EJECUCIÓN

1. **Puntuar los títulos — obligatorio, nunca se opina antes**
   `python3 tools/score_titles.py --title "A || B || C"`
   Devuelve 0-100 con desglose por eje y la memoria que justifica cada punto.
   Es `heuristic`: **hay que declarar que es rúbrica propia, no predicción de
   CTR**, y que no está validada mientras no se ingiera el CSV de Studio.

1b. **Dos reglas sobre el número, antes de mirarlo**

   **No perseguir el score.** Si un título honesto puntúa 78 y uno que exagera
   puntúa 95, se recomienda el de 78 y se dice por qué. La rúbrica mide
   parecido con lo que funcionó, no si el título es cierto; un clickbait bien
   construido puntúa alto y hace daño al canal.

   **Los scores solo se comparan dentro de la misma llamada.** Se puntúa el
   título actual JUNTO a las candidatas, en una sola ejecución
   (`--title "actual || A || B || C"`). Comparar el número de hoy con el de
   otra sesión no es válido. Y solo se propone una candidata que supere
   **estrictamente** a la actual: empatar no es mejorar.

2. **Respaldo de demanda**
   ```
   python3 tools/yt_search_terms.py --days 90        # demanda REAL, primero
   python3 tools/kw_research.py --kw "candidata 1; candidata 2"
   ```
   El primero manda: son términos con los que la gente ya llegó al canal. El
   segundo es proxy y solo ordena candidatas entre sí.

3. **Referencias reales, no intuición**
   `python3 tools/yt_outliers_channels.py --min-ratio 2.5`
   Se mira cómo titulan los outliers vivos del nicho ahora mismo.

4. **La miniatura**
   ```
   python3 tools/yt_thumbnails.py --video ID
   python3 tools/score_thumbnail.py --video ID --titulo "el título elegido"
   ```
   `score_thumbnail` solo puntúa el 40% automático. **El 60% restante lo
   devuelve como preguntas sin responder, y hay que responderlas abriendo el
   fichero JPG con visión.** Inventar ese 60% es el fallo que la herramienta
   está diseñada para impedir.

5. **Si hay que CREAR la miniatura, no solo juzgarla**
   Esta skill puntúa lo que existe. Para generarla:
   `image-generation-core` (reglas base) + `thumbnail-best-practices` (diseño),
   y `likeness-preservation` si aparece la cara. Si hay una referencia
   concreta que imitar, `thumbnail-inspiration`. Una imagen generada sale con
   `source: generated`: **no se puede puntuar y presentar el score como
   pronóstico de CTR**.

6. **Contraste anti-redundancia — el paso que más se salta**
   Comprobar que título y miniatura no comunican el mismo concepto. Si el número
   duro va en el título, la miniatura muestra el resultado visual.
   Si existe `memoria/sop/niche_bend_sop.md`, sus lecciones mandan sobre
   cualquier regla general.

## FUENTES

Paso 1 y 2b `heuristic` — declararlo siempre. Paso 2a `youtube_api`.
Pasos 3 y 4a `derived`. Paso 4b mixto: `derived` en el pixel, juicio del agente
en el resto.

## SALIDA

1. Los títulos ordenados por score, con el desglose por eje.
2. Una línea por título explicando qué eje lo sube o lo baja, citando la memoria.
3. El diagnóstico de miniatura con los ejes de juicio ya respondidos tras mirar
   la imagen.
4. El contraste título-miniatura: qué ángulo cubre cada uno.

Nunca se dice que un título "va a funcionar". Se dice a qué vídeo real se parece
y por qué.
