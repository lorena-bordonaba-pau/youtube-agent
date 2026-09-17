# Catálogo de herramientas

28 scripts: 20 herramientas de datos, 4 de la rama visual y 4 utilidades. Todas se ejecutan desde la raíz
del proyecto y devuelven JSON por defecto; `--md` da salida legible.

**Cómo leer la columna `source`** — es lo que determina cómo se puede citar cada
cifra. Ver la tabla de la sección 3 de `CLAUDE.md`.

Flags comunes a todas: `--md`, `--no-cache`.
Códigos de salida: `0` OK · `2` credenciales · `3` cuota agotada · `4` sin datos · `64` uso incorrecto.

## Analítica del canal propio

Requieren credenciales. Datos privados del canal autorizado.

| Herramienta | Qué hace | Comando | `source` | Cuota |
|---|---|---|---|---|
| `yt_report` | Informe completo + snapshot al histórico | `python3 tools/yt_report.py [--days 28]` | `youtube_api` | baja |
| `yt_analytics` | Serie diaria: vistas, retención, subs, engagement | `python3 tools/yt_analytics.py [--days 28]` | `youtube_api` | baja |
| `yt_top_videos` | Vídeos por vistas o por retención | `python3 tools/yt_top_videos.py [--days 90] [--limit 25] [--by-retention]` | `youtube_api` | baja |
| `yt_video_analytics` | Evolución diaria de un vídeo | `python3 tools/yt_video_analytics.py --video ID` | `youtube_api` | baja |
| `yt_retention` | **Curva de retención: dónde abandonan** | `python3 tools/yt_retention.py --video ID [--umbral 1.5]` | `youtube_api` | baja |
| `yt_search_terms` | **Términos de búsqueda reales que traen tráfico** | `python3 tools/yt_search_terms.py [--tipo YT_SEARCH\|RELATED_VIDEO]` | `youtube_api` | baja |
| `yt_traffic` | Fuentes de tráfico, etiquetadas en español | `python3 tools/yt_traffic.py [--days 28]` | `youtube_api` | baja |
| `yt_demographics` | Edad y género de la audiencia | `python3 tools/yt_demographics.py [--days 90]` | `youtube_api` | baja |
| `yt_geography` | Audiencia por país | `python3 tools/yt_geography.py [--days 90]` | `youtube_api` | baja |

## Datos públicos (cualquier canal)

| Herramienta | Qué hace | Comando | `source` | Cuota |
|---|---|---|---|---|
| `yt_channel_stats` | Subs, vistas, nº de vídeos de un canal | `python3 tools/yt_channel_stats.py [--channel ID]` | `youtube_api` | baja |
| `yt_recent_videos` | Vídeos recientes, con o sin estadísticas | `python3 tools/yt_recent_videos.py [--channel ID] [--limit 15] [--stats]` | `youtube_api` | baja |
| `yt_video_stats` | Vistas, likes, duración, tags de vídeos | `python3 tools/yt_video_stats.py --video ID[,ID2]` | `youtube_api` | baja |
| `yt_outliers_channels` | Outliers en competencia e inspiración | `python3 tools/yt_outliers_channels.py [--min-ratio 2.0] [--sample 30] [--list competencia]` | `derived` | media |
| `yt_outliers_playlist` | Outliers de la playlist de guardados | `python3 tools/yt_outliers_playlist.py [--days 7]` | `derived` | media |
| `yt_search` | Busca en YouTube y detecta outliers | `python3 tools/yt_search.py --query "..." [--limit 10]` | `derived` | **100 u/consulta** |
| `yt_thumbnails` | Descarga miniaturas + métricas de pixel | `python3 tools/yt_thumbnails.py --video ID` | `derived` | baja |
| `yt_transcript` | Transcripción (subtítulos, o Whisper) | `python3 tools/yt_transcript.py --video ID [--plano]` | `youtube_api` / `derived` | ninguna |

## Heurísticas propias

**Nada de aquí es un dato medido.** Al citar cualquier salida de esta sección
hay que declarar que es estimación propia.

| Herramienta | Qué hace | Comando | `source` |
|---|---|---|---|
| `kw_research` | Keywords por proxy: demanda + competencia | `python3 tools/kw_research.py --kw "a; b" [--profundo] [--sin-competencia]` | `heuristic` |
| `score_titles` | Puntúa títulos 0-100 con la rúbrica del canal | `python3 tools/score_titles.py --title "A \|\| B"` | `heuristic` |
| `score_thumbnail` | Puntúa el 40% automático; el 60% queda a juicio visual | `python3 tools/score_thumbnail.py --video ID \| --image RUTA [--titulo "..."]` | `heuristic` |

Las rúbricas viven en `config/rubricas/*.yaml` y están calibradas con las
memorias de feedback del canal. Cada punto sumado o restado cita la memoria que
lo justifica.

## Rama visual

Generan o transforman imágenes. **Nada de aquí es un dato**: una imagen
generada no mide nada y no predice cómo va a rendir.

El proveedor no se nombra en ninguna skill: vive en
`config/image_providers.json`. Con `provider: "fal"` se llama a fal.ai por REST
(necesita `FAL_KEY`); con `provider: "mcp"` la tool no genera y devuelve la
llamada MCP exacta para que la ejecute el agente.

| Herramienta | Qué hace | Comando | `source` | Coste |
|---|---|---|---|---|
| `generate_image` | Genera una imagen según el formato de destino | `python3 tools/generate_image.py --prompt "..." --type thumbnail\|banner\|profile_image\|general [--ref ORIGEN:ROL] [--dry-run]` | `generated` | **créditos** |
| `refine_image` | Edita una imagen existente sin redibujarla | `python3 tools/refine_image.py --image RUTA --instruction "..." [--ref cara.jpg:likeness] [--dry-run]` | `generated` | **créditos** |
| `export_image` | Dimensiones y peso exactos, local y determinista | `python3 tools/export_image.py --image RUTA --type thumbnail \| --size 1280x720` | `derived` | ninguno |
| `view_channel_packaging` | Descarga avatar y banner de un canal + métricas | `python3 tools/view_channel_packaging.py [--channel ID] [--only avatar\|banner\|both]` | `derived` | baja |

**`--dry-run` antes de gastar.** Devuelve el prompt final compuesto sin llamar
al proveedor. Si el prompt no dice lo que se quería, se corrige ahí.

**Los roles de referencia son obligatorios.** `--ref ORIGEN:ROL` con `ROL` en
`likeness`, `style`, `composition`, `packaging`. La tool rechaza una referencia
sin rol: el rol decide el orden y si se aplica la cláusula de identidad facial.

**Las miniaturas son siempre 16:9.** `thumbnail` lleva `ratio_fijo` en la
configuración y la tool valida la proporción antes de llamar al proveedor. No
hay formato vertical: se retiró de `formatos` y queda documentado en
`_formatos_retirados` por si algún día se restaura.

**El tamaño va como `image_size: {width, height}`**, que es la forma universal
de fal. Qué claves se envían está en `fal.claves_tamano`: si un modelo rechaza
una, se quita de ahí sin tocar código.

**Ningún slug de modelo se inventa.** Un slot a `null` hace fallar la tool con
instrucciones, en vez de adivinar. Los actuales están verificados con llamadas
reales del 2026-09-17: `fal-ai/nano-banana` para generar. Sondear con un payload
inválido **no vale**: la cola devuelve 200 y el error de ruta solo aparece al
llamar de verdad.

**`--image` cierra el ciclo.** `score_thumbnail` acepta un fichero local, no
solo un `video_id`, así que una miniatura recién generada se puntúa con la misma
rúbrica calibrada que una publicada. Puntuarla no la convierte en un dato.

**Toda generación queda anotada** en `datos/imagenes/registro.jsonl`: modelo,
tipo, prompt, fichero y referencias. Sirve para avisar de un prompt repetido
antes de pagarlo otra vez, y para poder cruzar algún día qué miniatura generada
se subió y qué CTR tuvo. El campo `subida_a_youtube` se rellena a mano.

**La proporción se verifica en el fichero, no se confía al modelo.** Tras
descargar, `generate_image` mide la imagen, recorta las bandas negras si el
modelo ha hecho letterbox, y fuerza el tamaño exacto cuando el formato tiene
`ratio_fijo`. Todo eso queda anotado en `notas` del sobre.

## Utilidades

| Herramienta | Qué hace | Comando |
|---|---|---|
| `init` | Estado del harness (lo ejecuta el hook de arranque) | `python3 tools/init.py` |
| `auth_setup` | Re-autoriza con Google. **Abre el navegador** | `python3 tools/auth_setup.py` |
| `ingest_studio_csv` | Ingiere CTR e impresiones del CSV de Studio | `python3 tools/ingest_studio_csv.py --csv ruta.csv` |
| `yt_channels_list` | Lista los canales configurados | `python3 tools/yt_channels_list.py [--list competencia]` |

## Cuota

La cuota diaria de la API de YouTube son 10.000 unidades. Casi todas las
llamadas cuestan 1-3 unidades; **`search.list` cuesta 100**, y lo usan
`yt_search.py` y `kw_research.py` (salvo con `--sin-competencia`).

Todo se cachea en `datos/cache/` con TTL por familia: 6 h para analítica propia,
24 h para canales ajenos y búsquedas, 30 días para transcripciones y miniaturas.
`--no-cache` fuerza la llamada.

## Lo que NO existe aquí

Ver `LIMITES.md`. En resumen: no hay CTR ni impresiones por API, no hay volumen
de búsqueda real, no se publica ni se modifica nada en YouTube —tampoco se sube
una imagen generada: eso es manual en Studio—, y no se genera ni se edita vídeo.
