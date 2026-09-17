# Límites

Lo que este harness **no** puede hacer. Se declara cuando es relevante, sin
esperar a que pregunten.

## Datos que no existen

**CTR e impresiones.** No están en la API pública de YouTube, solo en Studio.
Es el hueco más citado en los informes del canal: se mide cuántas vistas hay,
pero no por qué no se hace clic. Único camino: exportar el CSV desde
Studio → Estadísticas → Modo avanzado → Vídeos, e ingerirlo con
`tools/ingest_studio_csv.py`.

**Volumen de búsqueda.** YouTube no lo publica gratis. `kw_research.py` combina
autocompletado y competencia del top de resultados para dar una **posición
relativa entre las keywords comparadas en esa misma ejecución**. Comparar dos
ejecuciones distintas no es válido. Para demanda verificada existe
`yt_search_terms.py`, que sí devuelve tráfico real.

**Analítica de canales ajenos.** Solo lo público: vistas, likes, comentarios,
duración, tags. Nunca retención, tráfico ni demografía de otro canal. Cuando un
informe habla de la retención de un competidor, es inferencia, no medición.

**Retención de vídeos con pocas vistas.** YouTube aplica umbrales de privacidad:
`yt_retention.py` devuelve vacío en vídeos nuevos o con poco volumen. Eso sale
como código 4, no como cero.

## Estimaciones que no son medidas

**Los scores de títulos y miniaturas no predicen CTR.** Son listas de
comprobación ponderadas que codifican las lecciones ya aprendidas en vídeos
reales del canal. Dicen cuánto se parece un título a lo que funcionó antes, no
cómo va a rendir.

**Las rúbricas no están validadas.** Mientras `datos/historico/studio_ctr.json`
no exista, `validado_contra_ctr` es `false` en ambos ficheros de
`config/rubricas/`. Hay que decirlo al dar un score.

**El 60% de la rúbrica de miniaturas no es automático.** `score_thumbnail.py`
puntúa contraste, resolución y saturación; los ejes de redundancia con el
título, resultado-vs-interfaz y logos requieren mirar la imagen. La herramienta
devuelve esas preguntas sin responder a propósito, en vez de inventar un número.

**Una imagen generada no es evidencia de nada.** Sale con `source: generated`:
es un artefacto de un modelo externo. No predice CTR, no predice clics y no
demuestra que un diseño funcione. Al entregarla hay que nombrar el modelo que
la produjo, y no se puede puntuar con la rúbrica para después presentar ese
número como pronóstico: la rúbrica sigue sin validar contra CTR real.

**Las transcripciones automáticas tienen errores.** Ni los subtítulos de YouTube
ni Whisper son fiables palabra por palabra. No se cita una frase como textual de
alguien sin verificarla en el vídeo.

## Acciones que no se hacen

- **No se publica ni se modifica nada en YouTube.** Los scopes son de solo
  lectura. Cambiar títulos, miniaturas, descripciones o visibilidad es manual en
  Studio; el harness da el texto y la ruta.
- **No se genera ni se edita vídeo o audio.** Se planifica, se estructura y se
  mide; el render es otra herramienta.
- **No se sube una imagen generada a YouTube.** Los scopes son de solo lectura.
  El harness deja el fichero con las dimensiones correctas; ponerlo como
  miniatura, banner o avatar es manual en Studio.
- **No se contactan canales ni se envían emails.**

## Dependencias externas

- **Credenciales de Google.** Si el token caduca, todas las herramientas de
  analítica salen con código 2. Se arregla con `python3 tools/auth_setup.py`,
  que abre el navegador. Los tokens de una app en modo Testing caducan a los 7
  días.
- **`yt-dlp`** para transcripciones y **`whisper-cli`** como respaldo.
- **fal.ai, funcionando desde el 2026-09-17.** Generación verificada de punta a
  punta con `fal-ai/nano-banana`. Subida de referencias locales en dos pasos
  contra `rest.alpha.fal.ai`, también verificada.
- **`FAL_KEY` está guardada dos veces** en `~/.claude/settings.json` (138
  caracteres en vez de 69). La clave es válida; el problema es el pegado doble,
  invisible porque `set-fal-key.sh` oculta lo que escribes. Las tools lo
  detectan, usan la mitad y avisan, pero conviene arreglarlo pegándola una sola
  vez.
- **Higgsfield está declarado en `.mcp.json` pero sin conectar.** Hace falta una
  sesión nueva y aceptarlo. Mientras tanto, `provider: "mcp"` haría que las
  tools devolvieran la llamada sin ejecutarla.
- **El modelo no respeta la proporción por sí solo.** `fal-ai/nano-banana`
  ignora `image_size` (devolvía 1024x1024) y entrega letterbox con bandas
  negras si no se le prohíbe expresamente. Por eso `generate_image` mide el
  fichero, recorta las bandas y fuerza 16:9 después de generar: la garantía
  está en el pixel, no en el prompt.
- **Cuota diaria de 10.000 unidades**, compartida con cualquier otra cosa que
  use el mismo proyecto de Google Cloud.
