---
name: youtube-banner-spec
description: Especificación técnica del banner de YouTube — 2560x1440 y la zona segura móvil. Se invoca al generar, revisar o diagnosticar un banner de canal.
---

# Especificación del banner

## CUÁNDO

Cualquier generación o revisión de banner. Se carga **antes** de escribir el
prompt: la zona segura no se arregla después.

## LA REGLA QUE LO DECIDE TODO

El banner se sube a **2560x1440**, pero **en móvil solo se ve una franja
horizontal estrecha del centro vertical**. El tercio superior y el inferior se
recortan por completo.

Todo lo que importe —texto, logo, nombre del canal, caras, marca— va **dentro
de esa banda central**. Arriba y abajo solo pueden ir fondos simples:
degradados, desenfoques, patrones, color plano.

Un banner que pone el nombre del canal arriba desaparece en móvil. Es el fallo
más frecuente y el más invisible desde el escritorio.

## ORDEN DE EJECUCIÓN

1. **Ver el banner actual antes de sustituirlo**
   `python3 tools/view_channel_packaging.py --only banner --md`
   y abrir el fichero.

2. **Generar con el tipo correcto**
   ```
   python3 tools/generate_image.py --type banner --prompt "..." --dry-run --md
   ```
   `--type banner` antepone al prompt la regla de composición crítica con la
   banda segura. Comprobarlo en el dry-run: si esa cláusula no aparece en el
   prompt final, algo va mal en la configuración.

3. **Verificar el resultado abriéndolo** y comprobando, en concreto, que
   tapando el tercio de arriba y el de abajo sigue entendiéndose de qué va el
   canal.

4. **Ajustar dimensiones sin regenerar**
   `python3 tools/export_image.py --image RUTA --type banner`
   Deja exactamente 2560x1440. El recorte es centrado, así que si el sujeto no
   está centrado hay que revisarlo.

## ESTILO

- Texto grande y legible; el banner se ve pequeño en móvil.
- Branding centrado, dentro de la banda.
- Paleta del canal, para coherencia con el avatar. Cargar
  `analyse-channel-packaging` si no se conoce.

## FUENTES

La imagen es `source: generated`. Las dimensiones tras `export_image` son
`derived` y verificables en el fichero.
