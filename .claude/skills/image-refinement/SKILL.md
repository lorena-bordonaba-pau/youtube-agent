---
name: image-refinement
description: Edita una imagen que ya existe sin regenerarla desde cero. Se invoca ante "cámbiale el fondo", "quítale el logo", "hazlo más oscuro", "igual pero sin el texto".
---

# Refinado de imagen

## CUÁNDO

Hay una imagen que ya está mayormente bien y hay que cambiar una parte.

**El error que esta skill existe para evitar**: pasar la imagen casi buena como
*referencia* a `generate_image`. El modelo entonces dibuja otra imagen parecida
y se pierde justo lo que funcionaba. La imagen a editar va como **origen**,
nunca como referencia.

## ANTES DE GASTAR UN CRÉDITO

Si el cambio es de **tamaño, recorte, formato o peso**, esto no es una edición:
`python3 tools/export_image.py --image RUTA --type thumbnail`
Es local, determinista y gratis. No redibuja nada.

## ORDEN DE EJECUCIÓN

1. **Abrir la imagen actual** con la herramienta de lectura de imágenes y
   nombrar exactamente qué falla. Sin eso, la instrucción sale vaga y el
   resultado también.

2. **Una instrucción, en imperativo, solo el cambio**
   ```
   python3 tools/refine_image.py --image RUTA \
     --instruction "cambia el fondo a azul cobalto liso" --type thumbnail
   ```
   La tool ya añade *"keep everything else exactly as it is"*. Describir la
   imagen entera en la instrucción es lo que provoca que la redibuje.

3. **Si hay una cara**, pasarla como referencia aparte:
   `--ref foto_cara.jpg:likeness`. La cara **no** va en `--instruction`.

4. **Comparar origen y resultado abriendo los dos.** Un modelo de edición
   cambia cosas que no se le pidieron con más frecuencia de la que parece.

5. Iterar de una en una. Dos cambios en la misma instrucción se pisan.

## FUENTES

`source: generated`. Artefacto, no medición. Nombrar el modelo al entregar.

## SALIDA

La ruta del fichero, el modelo que lo hizo, y **qué ha cambiado respecto al
origen tras haber mirado ambos** — no la suposición de lo que debería haber
cambiado.
