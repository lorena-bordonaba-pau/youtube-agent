---
name: image-generation-core
description: Reglas base para generar cualquier imagen del canal — miniaturas, banner, perfil, gráficos. Se invoca ante "genera una imagen", "hazme una miniatura", "créame el banner", o antes de cualquier otra skill de la rama visual.
---

# Generación de imagen: reglas base

## CUÁNDO

Cualquier generación. Las demás skills visuales dependen de esta: si se va a
llamar a `generate_image.py`, estas reglas aplican.

Para **editar** una imagen que ya existe, no es esta skill: es
`image-refinement`. Para cambiar solo tamaño o peso, ninguna de las dos:
`export_image.py`, que es local y gratis.

## ORDEN DE EJECUCIÓN

1. **Elegir el formato antes que el prompt**
   `--type` decide qué requisitos técnicos se anteponen al prompt.

   | `--type` | Para qué | Píxeles |
   |---|---|---|
   | `thumbnail` | Miniatura de vídeo | 1280x720 (16:9) |
   | `profile_image` | Foto de perfil | 800x800 |
   | `banner` | Banner del canal | 2560x1440 |
   | `general` | Gráfico, ilustración, cualquier otra cosa | 1920x1080 |

   Aquí **no existe una tool separada para miniaturas de vídeo largo**: es
   `generate_image.py --type thumbnail`. No buscar un `generate_thumbnail`.

   **Las miniaturas son siempre 16:9** y la tool valida la proporción antes
   de llamar al proveedor. Si tu canal publica vertical, restaura el formato
   `vertical_thumbnail` desde `_formatos_retirados` en
   `config/image_providers.json`, y revisa antes `memoria/rules.md` por si
   hay una restricción que lo impida.

2. **Etiquetar cada referencia con su rol — es obligatorio**
   `--ref ORIGEN:ROL`, con `ROL` en `likeness`, `style`, `composition`,
   `packaging`. El origen puede ser una ruta local, una URL o un `video_id`.

   La tool **rechaza una referencia sin rol** a propósito: el rol decide el
   orden en que se le pasan al modelo y si se aplica la cláusula de identidad
   facial. Adivinarlo estropea la cara.

   El orden lo impone la tool: personas primero, estilo después, composición al
   final. Máximo 3 referencias; más diluyen el resultado.

3. **Si aparece una persona, cargar `likeness-preservation` antes de generar.**
   Una cara mal resuelta no se arregla iterando el prompt.

4. **Dry-run antes de gastar**
   `python3 tools/generate_image.py --prompt "..." --type banner --dry-run --md`
   Devuelve el prompt final compuesto sin llamar al proveedor. Si el prompt
   final no dice lo que se quería, se corrige aquí y no después de pagar.

5. **Generar**
   `python3 tools/generate_image.py --prompt "..." --type thumbnail --ref foto.jpg:likeness`

6. **Mirar el resultado.** Abrir el fichero devuelto con la herramienta de
   lectura de imágenes. Entregar una imagen sin haberla visto es el fallo más
   fácil de cometer en esta rama.

7. **Ajustar dimensiones con `export_image.py`, nunca regenerando.**
   `python3 tools/export_image.py --image RUTA --type thumbnail`
   Es determinista, local y sin créditos. YouTube rechaza miniaturas de más de
   2 MB y esta tool las deja por debajo sin repetir la generación.

## REGLAS DE PROMPT

- **Sin texto que no se haya pedido.** La tool ya lo pide; no contradecirlo.
- **Llenar el encuadre.** Sin bordes, sin marcos, sin margen blanco.
- **Sujeto grande**: entre el 50% y el 70% del encuadre.
- **Regla de tercios**: el foco en una intersección, no en el centro muerto.
- **Marcas de agua y logos ajenos fuera.** La tool lo pide en cada prompt.
- **Ante la duda, sin cara.** Objetos, texto, gráficos o abstracto antes que
  una persona genérica inventada.

## PROVEEDOR

No se nombra en ninguna skill. Vive en `config/image_providers.json`:

- `provider: "fal"` — llama a fal.ai por REST. Necesita `FAL_KEY` en el
  entorno (`~/.claude/scripts/set-fal-key.sh`, y sesión nueva).
- `provider: "mcp"` — la tool **no genera**: devuelve la llamada MCP exacta
  para que el agente la ejecute, porque un script no puede invocar una tool MCP
  de la sesión.

Los slots de modelo a `null` en la config hacen fallar la tool con
instrucciones. **Es a propósito**: un slug inventado gasta créditos y devuelve
404, o genera con otro modelo sin avisar.

## FUENTES

`generate_image` devuelve `source: generated`. No es un dato ni una medición:
**no dice nada sobre cómo va a rendir**. Al entregar la imagen hay que nombrar
el modelo que la produjo. `export_image` es `derived`.
