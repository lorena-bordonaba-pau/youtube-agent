---
name: analyse-channel-packaging
description: Extrae el branding de perfil y banner de un canal antes de generar packaging nuevo. Se invoca ante "analiza mi banner", "cómo es la marca visual de este canal", "revisa mi packaging de canal".
---

# Análisis de packaging de canal

## CUÁNDO

Antes de generar un banner o una foto de perfil, propios o inspirados en otro
canal. Sin ver la marca actual, lo que se genere será genérico o romperá una
identidad que ya funciona.

## ORDEN DE EJECUCIÓN

1. **Descargar y medir las dos piezas**
   ```
   python3 tools/view_channel_packaging.py [--channel ID] --md
   ```
   Devuelve avatar y banner descargados, con resolución, contraste y
   saturación de cada uno.

2. **Abrir los dos ficheros** con la herramienta de lectura de imágenes. El
   pixel dice si hay contraste; no dice qué transmite.

3. **Leer el banner por su banda central.** Es el error de lectura más común:
   en móvil se recorta el tercio superior y el inferior por completo. Un banner
   se juzga por lo que sobrevive en esa franja, no por lo que se ve en el
   escritorio. Ver `youtube-banner-spec`.

4. **Analizar los elementos**
   - Esquema de color, y si avatar y banner son coherentes entre sí.
   - Tipografía del banner: tagline, jerarquía, legibilidad reducida.
   - Avatar: ¿se reconoce a 32x32, que es su tamaño en los comentarios?
   - Zonas del banner: qué hay en la banda segura y qué se pierde al recortar.
   - Elementos de identidad: logos, colores firma, motivos repetidos.

5. **Cruzar con el posicionamiento.** Leer `memoria/channel_positioning.md`:
   el packaging o respalda la promesa del canal o la contradice. Ese cruce es
   el análisis; describir colores no lo es.

6. **Si se va a generar**, cargar `youtube-banner-spec` o
   `youtube-profile-spec` según la pieza, y pasar el packaging actual como
   referencia:
   ```
   python3 tools/generate_image.py --type banner --prompt "..." \
     --ref datos/packaging/<channel_id>_banner.jpg:packaging --dry-run
   ```
   Se preservan los elementos de identidad salvo que se haya pedido un
   rebranding completo y explícito.

## SALIDA

Brief en 5-8 viñetas: qué funciona, qué se pierde en móvil, qué contradice el
posicionamiento, y qué se mantendría intacto en un rediseño.

## FUENTES

`view_channel_packaging` es `derived`: métricas de pixel sobre imágenes de la
API. La lectura de marca es juicio del agente sobre ficheros que ha abierto, y
se declara así. `channel_positioning.md` es `config`, con su fecha.
