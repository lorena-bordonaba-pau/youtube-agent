---
name: thumbnail-inspiration
description: Analiza una miniatura de referencia y genera una inspirada en ella, adaptando sus principios de diseño al contenido propio. Se invoca ante "hazme una miniatura como esta", "me gusta esta miniatura", "inspírate en este vídeo".
---

# Miniatura inspirada en una referencia

## CUÁNDO

Hay **una referencia concreta**: una imagen aportada, la miniatura de un vídeo
ajeno, o una generada antes. Si no hay referencia y lo que se quiere es leer el
estilo de un canal entero, es `analyse-thumbnails`.

**Adaptar principios, no copiar.** Copiar la miniatura de un competidor la
pone al lado de la suya en el feed, compitiendo con el original y perdiendo.

## ORDEN DE EJECUCIÓN

1. **Ver la referencia**
   - Es un vídeo de YouTube: `python3 tools/yt_thumbnails.py --video ID` y
     abrir el fichero.
   - Es un fichero local o una imagen aportada: abrirla directamente.

2. **Medirla, si es de YouTube**
   `python3 tools/score_thumbnail.py --video ID`
   Da el contraste y la saturación reales de la referencia, que es lo que la
   hace destacar en el feed y lo que suele perderse al imitarla "a ojo".

3. **Extraer la fórmula de diseño en 5-8 viñetas**: layout, paleta,
   tipografía (tamaño relativo, contorno, nº de palabras), mood, elementos
   humanos (expresión, pose, dirección de la mirada, encuadre), y **qué la hace
   clicable**. Cargar `thumbnail-best-practices` para nombrar los ejes.

4. **Decidir qué se adapta y qué se cambia — el paso que evita el plagio.**
   Se mantiene: composición, jerarquía, contraste, tipo de emoción.
   Se cambia: el tema, el sujeto, la paleta si es marca ajena, el texto.

5. **Comprobar contra la rúbrica propia antes de generar.** Si la referencia
   funciona por un logo grande o por repetir el título, aquí eso resta:
   `no_redundante_con_titulo` pesa 25 puntos y `logos` penaliza más de uno.
   La referencia no sobrescribe la rúbrica del canal.

6. **Generar**, describiendo el tema **nuevo**, no el de la referencia:
   ```
   python3 tools/generate_image.py --type thumbnail \
     --prompt "<tema nuevo>. Usa la composición de Reference Image 1: <fórmula>" \
     --ref REFERENCIA:composition --ref cara.jpg:likeness --dry-run
   ```
   Regla dura sobre la referencia: **si en ella sale otra persona, no se pasa
   como `--ref`**. Su composición se describe en el prompt y punto. Pasar la
   cara de otro es cómo acaba en la imagen.

   Si sale la creadora, o no sale nadie, sí puede ir como referencia.

7. Quitar `--dry-run`, generar, **abrir el resultado** y ofrecer un ajuste
   concreto, no un menú de opciones.

## FUENTES

La imagen generada es `source: generated`: artefacto, no predicción. El score
de la referencia es `heuristic` sin validar contra CTR. Al entregar se nombra
el modelo y se dice en qué se ha inspirado.
