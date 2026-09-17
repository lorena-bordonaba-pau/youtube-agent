---
name: thumbnail-best-practices
description: Reglas de diseño de miniaturas — composición, texto, legibilidad móvil. Se invoca al generar o al juzgar una miniatura, sea propia o ajena.
---

# Reglas de diseño de miniaturas

## CUÁNDO

Al generar una miniatura, al diagnosticar una, o al extraer el estilo de un
canal. Son reglas de diseño: aplican al margen del proveedor que genere.

## RELACIÓN CON LA RÚBRICA DEL CANAL

Estas reglas son **generales**. `config/rubricas/miniaturas.yaml` es la rúbrica
**calibrada con las memorias de este canal** y es la que manda cuando hay
conflicto. Sus ejes de juicio pesan 60 de 100 puntos:

- `no_redundante_con_titulo` (25) — si el número duro va en el título, la
  miniatura muestra el **resultado visual**, no repite el precio.
- `resultado_no_ui` (18) — un timeline o una interfaz densa es ruido gris a
  tamaño feed.
- `logos` (9) — **máximo uno**, y solo si es ancla reconocible para marketers.
- `texto_breve` (8) — cuatro palabras o menos.

En una instalación nueva esos cuatro ejes son **ejemplos sin calibrar**: el
campo `memoria` de cada uno está a `null`. Adáptalos a tu canal y, cuando
aprendas algo de tus propias miniaturas, escríbelo en `memoria/` y apunta el
eje a ese fichero. Al generar, los ejes vigentes van al prompt.

## REGLAS GENERALES

**Legibilidad móvil** — el listón real. La miniatura se ve a unos 160 px de
ancho.
- El texto debe ocupar **un tercio del ancho o más**. Si no, es ilegible.
- Sans-serif bold pesado, contorno grueso o sombra dura.
- Zona de fondo simple detrás del texto, para contraste máximo.
- Máximo 3-5 palabras. En este canal, 4.

**Composición**
- Regla de tercios: el foco en una intersección.
- Espacio negativo reservado para el texto, preferiblemente arriba.
- Líneas guía (brazos, flechas, arquitectura) apuntando al sujeto.
- Esquina inferior derecha libre: ahí va el sello de duración.
- Una sola idea focal. Paleta limitada. Alto contraste sujeto/fondo.

**Autenticidad**
- Solo lo que sale de verdad en el vídeo. Un escenario que no existe es
  clickbait y penaliza el crecimiento aunque suba el clic.
- Estética realista antes que el plástico sobreprocesado.
- La expresión debe coincidir con la emoción real del vídeo.
- Mostrar la **acción**, no una pose estática.

**Elementos humanos**
- Una cara ayuda pero no es obligatoria: manos, POV o un objeto funcionan.
- Ropa y pose distintas en cada vídeo, para señalar contenido fresco.

**Qué evitar**
- Composición atestada, texto pequeño, estética de banco de imágenes,
  bordes gruesos, mezcla de temperaturas de color (naranja cálido con luz día).

## VERIFICACIÓN

Lo objetivo se mide, no se opina:
```
python3 tools/yt_thumbnails.py --video ID          # contraste, saturación, resolución
python3 tools/score_thumbnail.py --video ID --titulo "..."
```
`score_thumbnail` puntúa el 40% automático y **devuelve el 60% como preguntas
sin responder**. Hay que responderlas abriendo el JPG. Inventar ese 60% es el
fallo que la herramienta está diseñada para impedir.

## FUENTES

La rúbrica es `heuristic` y **no está validada contra CTR** mientras
`datos/historico/studio_ctr.json` no exista. Un score nunca se presenta como
predicción de clics. Las métricas de pixel de `yt_thumbnails` son `derived`.
