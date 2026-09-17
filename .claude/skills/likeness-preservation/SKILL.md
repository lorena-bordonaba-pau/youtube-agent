---
name: likeness-preservation
description: Preserva la identidad facial exacta al generar o editar imágenes con la cara de la creadora. Se invoca siempre que una imagen vaya a incluir a una persona real.
---

# Preservación de identidad facial

## CUÁNDO

Cualquier imagen en la que deba aparecer la creadora, o cualquier persona real.
Se carga **antes** de generar, no después de ver que la cara salió mal: una
identidad perdida no se recupera iterando el prompt.

**Si no se ha pedido explícitamente que salga una cara, no se pone una.** Ante
la duda: objetos, texto, gráficos o abstracto. Una persona inventada en la
miniatura de un canal con rostro reconocible rompe la marca.

## ORDEN DE EJECUCIÓN

1. **Conseguir una referencia facial nítida.** Por orden de calidad:
   - Una foto que aporte la creadora en esta conversación.
   - Una imagen generada antes en esta conversación donde la cara salió bien.
   - Una miniatura propia con la cara clara y grande:
     ```
     python3 tools/yt_recent_videos.py --limit 15 --stats
     python3 tools/yt_thumbnails.py --video ID
     ```
     Y **abrirla** para confirmar que la cara se ve. Una cara borrosa, de
     perfil o tapada da un resultado malo garantizado.

2. **No proceder sin referencia confirmada.** Si no la hay, se dice y se pide
   una foto. Generar "algo parecido" es peor que no generar.

3. **Etiquetarla con el rol `likeness`**
   ```
   python3 tools/generate_image.py --prompt "..." --type thumbnail \
     --ref ruta_de_la_cara.jpg:likeness
   ```
   El rol hace dos cosas: coloca la referencia **la primera** y activa la
   cláusula de identidad exacta en el prompt. Sin el rol, ninguna de las dos.

4. **Al refinar**, la imagen a editar va en `--image` y la cara en
   `--ref cara.jpg:likeness`. Nunca al revés.

5. **Verificar abriendo el resultado.** Criterio:

   | Aceptable | No aceptable |
   |---|---|
   | Otra pose, otro ángulo | Otros rasgos faciales |
   | Otra expresión | Alguien que "se le parece" |
   | Otra luz, otra ropa | Una cara claramente generada |

   Si no es reconociblemente la misma persona, se repite con una referencia
   mejor. No se entrega diciendo "ha quedado parecido".

## LO QUE LA TOOL YA HACE

`generate_image.py` antepone al prompt, cuando detecta una referencia con rol
`likeness`, la cláusula de identidad exacta y la prohibición de recortar por el
cuello. No hay que repetirlo en `--prompt`; comprobarlo con `--dry-run`.

## FUENTES

`source: generated`. Una cara bien preservada sigue siendo un artefacto, no una
foto real: si se usa en algo público, decirlo.
