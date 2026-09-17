---
name: youtube-profile-spec
description: Especificación de la imagen de perfil de YouTube — 1:1 recortada en círculo. Se invoca al generar o revisar la foto de perfil del canal.
---

# Especificación de la imagen de perfil

## CUÁNDO

Cualquier generación o revisión de foto de perfil.

## LA REGLA QUE LO DECIDE TODO

Se sube **cuadrada 1:1**, pero YouTube la **recorta en círculo**. Todo lo que
quede cerca de las esquinas se pierde.

Y se ve pequeña: **32x32 píxeles en los comentarios**. Ese es el tamaño real en
el que hay que reconocerla, no el del escritorio del estudio.

## ORDEN DE EJECUCIÓN

1. **Ver la actual**
   `python3 tools/view_channel_packaging.py --only avatar --md` y abrirla.

2. **Generar**
   ```
   python3 tools/generate_image.py --type profile_image --prompt "..." \
     --ref foto_cara.jpg:likeness --dry-run
   ```
   `--type profile_image` ya pide sujeto centrado, fondo simple, sin texto y
   legibilidad a 32x32.

   Si aparece la cara de la creadora, cargar `likeness-preservation`: en un
   avatar la identidad es todo lo que hay.

3. **Verificar a tamaño real**, que es lo que casi nunca se hace:
   `python3 tools/export_image.py --image RUTA --size 32x32 --out /tmp/avatar32.png`
   y abrir ese fichero de 32x32. Si a ese tamaño no se distingue quién es, no
   sirve, por bien que se vea a 800x800.

4. Exportar el definitivo: `python3 tools/export_image.py --image RUTA --type profile_image`

## COMPOSICIÓN

- Sujeto centrado y grande: el círculo se come las esquinas.
- Fondo simple, de un color, con contraste alto contra el sujeto.
- **Sin texto y sin detalle fino.** A 32x32 es una mancha.
- Coherente en color con el banner.

## FUENTES

`source: generated` la imagen; `derived` el redimensionado.
