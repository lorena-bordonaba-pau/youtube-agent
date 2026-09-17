---
name: analyse-thumbnails
description: Extrae el estilo de miniaturas de un canal, propio o ajeno, antes de generar una nueva. Se invoca ante "cómo son mis miniaturas", "analiza el estilo de este canal", "qué patrón visual sigue mi competencia".
---

# Análisis de estilo de miniaturas

## CUÁNDO

Estudio proactivo del estilo de un canal, **sin que nadie haya aportado una
referencia concreta**. Si la creadora trae una miniatura suelta que le gusta,
eso es `thumbnail-inspiration`, no esta skill.

Sirve para dos cosas: conocer la propia marca antes de generar algo que la
rompa, y leer el patrón visual de un competidor.

## ORDEN DE EJECUCIÓN

1. **Elegir de 3 a 5 vídeos representativos**
   ```
   python3 tools/yt_recent_videos.py [--channel ID] --limit 15 --stats
   ```
   Representativos del estilo **actual**: se saltan colaboraciones y
   experimentos fuera de línea. Si el canal cambió de estilo, solo lo posterior
   al cambio.

2. **Descargar y medir el pixel**
   `python3 tools/yt_thumbnails.py --video ID1,ID2,ID3`
   Da contraste, luminancia, saturación y resolución. Objetivo, no opinable.

3. **Mirarlas.** Abrir cada fichero de `fichero` con la herramienta de lectura
   de imágenes. **Este paso no es opcional**: el pixel no dice qué se ve.

4. **Puntuar una o dos** para tener el contraste cuantitativo:
   `python3 tools/score_thumbnail.py --video ID --titulo "..."`

5. **Extraer el patrón**, anotando en cuántas de las N aparece cada rasgo:
   - Paleta de color y temperatura dominante.
   - Tipografía: tamaño relativo al ancho, contorno, número de palabras.
     Marcar si el texto ocupa menos de un tercio del ancho.
   - Layout: dónde cae el sujeto, dónde el texto, qué espacio queda libre.
   - Uso de rostro: si aparece, **anotar el `video_id` donde mejor se ve**,
     que es la referencia de likeness para generar después.
   - Motivos recurrentes: flechas, marcos, pantalla partida, logos, emoji.

   Un rasgo que aparece en 1 de 5 no es el estilo del canal, es una excepción.

6. **Cruzar con rendimiento.** El patrón solo importa si se contrasta con lo
   que funcionó: `python3 tools/yt_outliers_channels.py --min-ratio 2.0`.
   Un estilo consistente que rinde mal es un estilo consistente que rinde mal.

## SALIDA

1. **Brief de estilo en 5-8 viñetas**, cada una con su frecuencia ("4 de 5").
2. **Los 1-2 `video_id` más representativos** y por qué lo son.
3. Si hay rostro, el `video_id` de la mejor referencia de likeness.
4. Qué hay que **mantener** para no romper la marca y qué está **flojo**
   medido contra la rúbrica.

## FUENTES

Métricas de pixel `derived`. Vistas y outliers `derived` sobre `youtube_api`.
La lectura de estilo es juicio del agente sobre imágenes que ha abierto: se
declara como tal. La rúbrica es `heuristic` sin validar contra CTR.
