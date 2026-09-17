"""Adaptador de generación de imagen, agnóstico al proveedor.

Ninguna skill nombra un proveedor. Piden una imagen; este módulo decide si la
pide a fal.ai por REST o si devuelve una directiva para que el agente llame a
un MCP. Cambiar de proveedor se hace en `config/image_providers.json`.

Dos reglas duras:

1. **No se inventa un slug de modelo.** Si el modelo pedido está a `null` en la
   configuración, la tool falla con instrucciones en vez de adivinar. Un slug
   inventado gasta créditos y devuelve 404, o peor, genera con otro modelo.
2. **Una imagen generada nunca es un dato.** Todo lo que sale de aquí viaja con
   `source: generated`, que el contrato traduce a "artefacto, no medición".
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import base  # noqa: F401 — al importarlo se carga el .env
from .contrato import (CONFIG_DIR, DATOS_DIR, EXIT_AUTH, EXIT_NO_DATA, ToolError)

CONFIG = CONFIG_DIR / "image_providers.json"
SALIDA = DATOS_DIR / "imagenes"

# Reglas de formato que se anteponen al prompt. No son estilo: son requisitos
# técnicos del sitio donde va la imagen, y si no van en el prompt el modelo los
# ignora. La zona segura del banner es la que más se olvida.
SPEC = {
    "thumbnail": (
        "Wide 16:9 horizontal image for a YouTube video thumbnail. "
        "Fill the ENTIRE frame edge to edge. Absolutely no letterboxing, no "
        "black bars at the top or bottom, no cinematic bars, no borders, no "
        "frames, no padding: the photographed content must reach all four "
        "edges of the image. "
        "Must stay legible when scaled down to roughly 160 pixels wide."
    ),
    "profile_image": (
        "Square 1:1 image for a channel profile picture. Centre the main "
        "subject: the platform crops it to a circle, so anything near the "
        "corners is lost. Simple background. Must stay recognisable at 32x32 "
        "pixels, so no text and no fine detail."
    ),
    "banner": (
        "Exactly 2560x1440 pixels, YouTube channel banner. "
        "CRITICAL COMPOSITION RULE: only a narrow horizontal band across the "
        "vertical centre is visible on mobile; the upper and lower thirds are "
        "cropped away entirely. Place ALL important content (text, logos, "
        "channel name, faces, key branding) strictly within that narrow middle "
        "band. Upper and lower portions must contain ONLY simple backgrounds "
        "(gradients, blurs, patterns, solid colours)."
    ),
    # `preserve` no impone forma: se usa al EDITAR, donde cambiar la proporción
    # del original nunca es lo que se ha pedido salvo que se diga.
    "preserve": (
        "Keep the exact same dimensions and aspect ratio as the source image. "
        "Do not reframe, do not crop, do not letterbox."
    ),
    "general": (
        "Wide 16:9 horizontal image. Fill the ENTIRE frame edge to edge, with "
        "no letterboxing, no black bars and no borders."
    ),
}

# Se antepone a cualquier prompt que lleve una referencia de likeness. Es la
# frase que evita que el modelo devuelva "alguien que se parece".
LIKENESS = (
    "Use the EXACT facial identity and likeness of the person in "
    "{etiqueta} — this must be recognisably the same individual, not merely "
    "someone who looks similar and not an AI-generated lookalike. Do not alter "
    "their facial features. Never crop at the neck: include the upper body."
)


def cargar() -> dict:
    if not CONFIG.exists():
        raise ToolError(f"Falta {CONFIG}", EXIT_NO_DATA)
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def proveedor(cfg: dict, pedido: str | None = None) -> str:
    p = pedido or cfg.get("provider", "fal")
    if p not in ("fal", "mcp"):
        raise ToolError(f"Proveedor desconocido: {p}", EXIT_NO_DATA,
                        "Validos: fal, mcp. Se configura en image_providers.json")
    return p


def modelo(cfg: dict, accion: str, pedido: str | None = None) -> str:
    """Resuelve el slug del modelo. Falla en vez de inventarlo."""
    if pedido:
        return pedido
    modelos = cfg["fal"]["modelos"]
    slug = modelos.get(accion)
    if slug:
        return slug
    alt = modelos.get(f"{accion}_gpt")
    if alt:
        return alt
    raise ToolError(
        f"No hay slug de modelo para la accion '{accion}'.",
        EXIT_NO_DATA,
        "Busca el modelo en https://fal.ai/explore/models y escribe su slug en "
        f"config/image_providers.json (fal.modelos.{accion}), o pasa --model. "
        "Esta tool no adivina slugs a proposito: uno inventado gasta creditos.",
    )


# Avisos que la tool acumula para que viajen dentro del sobre, no a un log.
AVISOS: list[str] = []


def clave_fal(cfg: dict) -> str:
    """Devuelve la clave de fal, corrigiendo el pegado doble.

    `set-fal-key.sh` pide la clave con `read -rs`, que oculta lo escrito: un
    doble pegado no se ve y deja la clave escrita dos veces, lo que da 401. Se
    detecta solo el caso exacto —longitud par y las dos mitades idénticas— y se
    usa la mitad, dejando un aviso visible. No se corrige nada más: una clave
    simplemente mal no se adivina.
    """
    env = cfg["fal"].get("key_env", "FAL_KEY")
    key = os.environ.get(env, "").strip()
    if not key:
        raise ToolError(
            f"No hay {env} en el entorno.",
            EXIT_AUTH,
            "Ejecuta ~/.claude/scripts/set-fal-key.sh y abre una sesion nueva. "
            "Comprobar con ~/.claude/scripts/check-fal-key.sh",
        )
    mitad = len(key) // 2
    if len(key) % 2 == 0 and mitad > 8 and key[:mitad] == key[mitad:]:
        AVISOS.append(
            f"{env} esta guardada DOS VECES ({len(key)} caracteres en vez de "
            f"{mitad}). Se ha usado la mitad para que la llamada funcione, pero "
            "conviene arreglarla: ejecuta ~/.claude/scripts/set-fal-key.sh y "
            "pega la clave UNA sola vez (el campo esta oculto, por eso el doble "
            "pegado no se ve).")
        return key[:mitad]
    return key


def _peticion(url: str, key: str, datos: bytes | None = None,
              content_type: str = "application/json", metodo: str | None = None):
    req = urllib.request.Request(url, data=datos, method=metodo)
    req.add_header("Authorization", f"Key {key}")
    if datos is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            cuerpo = r.read()
            if r.headers.get("Content-Type", "").startswith("application/json"):
                return json.loads(cuerpo)
            return cuerpo
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:500]
        raise ToolError(f"fal.ai devolvio {e.code}: {detalle}", EXIT_NO_DATA,
                        "Si es 404, el slug del modelo no existe: verificalo en "
                        "https://fal.ai/explore/models") from e


def subir(ruta: Path, cfg: dict, key: str) -> str:
    """Sube un fichero local a fal storage y devuelve su URL pública.

    Son **dos pasos**, no uno: se pide una URL firmada a `/storage/upload/initiate`
    y luego se hace `PUT` de los bytes contra ella. Verificado el 2026-09-17; la
    versión anterior hacía un POST directo a `rest.fal.run`, un host que ni
    siquiera resuelve por DNS.
    """
    tipo = mimetypes.guess_type(str(ruta))[0] or "application/octet-stream"
    inicio = _peticion(
        cfg["fal"]["upload_initiate_url"], key,
        json.dumps({"content_type": tipo, "file_name": ruta.name}).encode("utf-8"))
    if not isinstance(inicio, dict) or not inicio.get("upload_url"):
        raise ToolError(f"fal storage no devolvio upload_url para {ruta}",
                        EXIT_NO_DATA)

    req = urllib.request.Request(inicio["upload_url"], data=ruta.read_bytes(),
                                 method="PUT")
    req.add_header("Content-Type", tipo)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            if r.status not in (200, 201, 204):
                raise ToolError(f"La subida devolvio {r.status}", EXIT_NO_DATA)
    except urllib.error.HTTPError as e:
        raise ToolError(f"Fallo al subir {ruta.name}: {e.code}", EXIT_NO_DATA) from e

    return inicio["file_url"]


def referencia_url(ref: str, cfg: dict, key: str) -> str:
    """Una referencia puede ser URL, fichero local o video_id de YouTube."""
    if ref.startswith(("http://", "https://")):
        return ref
    p = Path(ref)
    if p.exists():
        return subir(p, cfg, key)
    if len(ref) == 11 and "/" not in ref:   # parece un video_id
        return f"https://i.ytimg.com/vi/{ref}/maxresdefault.jpg"
    raise ToolError(f"Referencia no resoluble: {ref}", EXIT_NO_DATA,
                    "Usa una ruta local existente, una URL, o un video_id.")


def encolar(slug: str, payload: dict, cfg: dict, key: str) -> dict:
    """Encola el trabajo, espera a que termine y devuelve la respuesta."""
    base = cfg["fal"]["queue_base"].rstrip("/")
    envio = _peticion(f"{base}/{slug}", key,
                      json.dumps(payload).encode("utf-8"))
    rid = envio.get("request_id")
    if not rid:
        raise ToolError(f"fal.ai no devolvio request_id: {envio}", EXIT_NO_DATA)

    estado_url = envio.get("status_url") or f"{base}/{slug}/requests/{rid}/status"
    resp_url = envio.get("response_url") or f"{base}/{slug}/requests/{rid}"

    limite = time.time() + cfg["fal"].get("timeout_s", 300)
    espera = cfg["fal"].get("poll_s", 3)
    while time.time() < limite:
        est = _peticion(estado_url, key)
        situacion = est.get("status") if isinstance(est, dict) else None
        if situacion == "COMPLETED":
            return _peticion(resp_url, key)
        if situacion in ("FAILED", "CANCELLED"):
            raise ToolError(f"El trabajo de fal.ai termino en {situacion}: {est}",
                            EXIT_NO_DATA)
        time.sleep(espera)
    raise ToolError(f"Timeout esperando a fal.ai ({rid})", EXIT_NO_DATA,
                    f"El trabajo puede seguir vivo. Consulta {estado_url}")


def urls_de(respuesta: dict) -> list[str]:
    """Extrae las URLs de imagen de una respuesta de fal, tolerando esquemas."""
    salida = []
    for clave in ("images", "image", "output", "outputs", "data"):
        val = respuesta.get(clave) if isinstance(respuesta, dict) else None
        if isinstance(val, dict):
            val = [val]
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and item.get("url"):
                    salida.append(item["url"])
                elif isinstance(item, str) and item.startswith("http"):
                    salida.append(item)
        elif isinstance(val, str) and val.startswith("http"):
            salida.append(val)
    return salida


def descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        destino.write_bytes(r.read())
    return destino


def recortar_bandas(ruta: Path, umbral: int = 18) -> tuple[int, int]:
    """Quita las bandas negras uniformes de arriba y abajo, si las hay.

    `fal-ai/nano-banana` entrega el contenido con letterbox: en la prueba del
    2026-09-17 devolvio 1344x768 con 80px de banda negra arriba y abajo. Como
    las bandas son pixeles de la imagen, recortar al ratio no las elimina: hay
    que detectarlas y quitarlas antes.

    Devuelve (px recortados arriba, px recortados abajo).
    """
    from PIL import Image

    with Image.open(ruta) as original:
        gris = original.convert("L")
        w, h = gris.size
        px = gris.load()

        def uniforme(y: int) -> bool:
            muestras = [px[x, y] for x in range(0, w, max(1, w // 80))]
            return max(muestras) <= umbral

        arriba = next((y for y in range(h) if not uniforme(y)), 0)
        abajo = next((y for y in range(h - 1, -1, -1) if not uniforme(y)), h - 1)
        if arriba == 0 and abajo == h - 1:
            return 0, 0
        # Una banda que se come mas de un tercio de la altura no es letterbox:
        # es una imagen oscura de verdad. No se toca.
        if (arriba + (h - 1 - abajo)) > h / 3:
            return 0, 0
        original.crop((0, arriba, w, abajo + 1)).save(ruta)
    return arriba, h - 1 - abajo


def verificar_proporcion(ruta: Path, cfg: dict, tipo: str) -> tuple[str, Path | None]:
    """Comprueba la proporción del fichero y la corrige si el formato la fija.

    El prompt pide 16:9 y el payload lo pide otra vez, pero el modelo puede
    devolver otra cosa: `fal-ai/nano-banana` devuelve 1024x1024 pase lo que
    pase. "Las miniaturas son siempre 16:9" solo es cierto si se verifica en el
    pixel, así que aquí se mide y, si hace falta, se recorta.

    Devuelve (resolución que llegó, ruta corregida o None si no hizo falta).
    """
    from PIL import Image

    with Image.open(ruta) as img:
        recibido = f"{img.size[0]}x{img.size[1]}"

    sup, inf = recortar_bandas(ruta)
    if sup or inf:
        AVISOS.append(
            f"El modelo devolvio {recibido} CON BANDAS NEGRAS ({sup}px arriba, "
            f"{inf}px abajo). Se han recortado. Si se repite, el modelo esta "
            "ignorando la instruccion de llenar el encuadre.")

    with Image.open(ruta) as img:
        ancho, alto = img.size
    devuelto = recibido if not (sup or inf) else f"{recibido} -> {ancho}x{alto} sin bandas"

    fmt = cfg["formatos"].get(tipo)
    if fmt is None:                      # `preserve`: no hay forma que imponer
        return devuelto, None
    objetivo_w, objetivo_h = (int(x) for x in fmt["px"].split("x"))
    if abs(ancho / alto - objetivo_w / objetivo_h) < 0.01:
        return devuelto, None
    if not fmt.get("ratio_fijo"):
        AVISOS.append(
            f"El modelo devolvio {devuelto}, no {fmt['ratio']}. Para forzarlo: "
            f"python3 tools/export_image.py --image {ruta} --type {tipo}")
        return devuelto, None

    # Formato con proporción fija: se corrige aquí mismo, sin gastar créditos.
    import subprocess
    corregido = ruta.with_name(ruta.stem + f"_{objetivo_w}x{objetivo_h}.jpg")
    subprocess.run(
        ["python3", str(Path(__file__).resolve().parent.parent / "export_image.py"),
         "--image", str(ruta), "--type", tipo, "--out", str(corregido)],
        check=True, capture_output=True)
    AVISOS.append(
        f"El modelo devolvio {devuelto}, que no es {fmt['ratio']}. Se ha "
        f"recortado por el centro a {objetivo_w}x{objetivo_h}. ABRE el fichero: "
        "si el sujeto no estaba centrado, el recorte lo habra cortado.")
    return devuelto, corregido


REGISTRO = SALIDA / "registro.jsonl"


def _huella(slug: str, tipo: str, prompt: str) -> str:
    import hashlib
    return hashlib.sha256(f"{slug}|{tipo}|{prompt}".encode()).hexdigest()[:16]


def avisar_si_repetida(slug: str, tipo: str, prompt: str, horas: int = 24) -> None:
    """Avisa si este mismo prompt ya se generó hace poco.

    No se cachea la generación: pedir otra versión del mismo prompt es lo normal
    y devolver el fichero viejo sería peor que cobrar dos veces. Lo que se evita
    es la repetición *accidental* —un reintento, un bucle—, nombrando el fichero
    que ya existe para poder reutilizarlo si sirve.
    """
    import time

    if not REGISTRO.exists():
        return
    huella = _huella(slug, tipo, prompt)
    limite = time.time() - horas * 3600
    for linea in reversed(REGISTRO.read_text(encoding="utf-8").splitlines()):
        try:
            fila = json.loads(linea)
        except Exception:  # noqa: BLE001 — una línea corrupta no rompe nada
            continue
        if fila.get("huella") == huella and fila.get("ts", 0) >= limite:
            AVISOS.append(
                f"Este mismo prompt ya se genero hace poco con {slug}: "
                f"{fila.get('fichero')}. Si vale, reutilizalo y no pagues otra "
                "vez. Si buscabas una variante, ignora este aviso.")
            return


def anotar(tool: str, slug: str, tipo: str, prompt: str, fichero: Path,
           refs: list[dict] | None = None) -> None:
    """Deja constancia de cada generación en `datos/imagenes/registro.jsonl`.

    Sirve para dos cosas: detectar repeticiones, y poder cruzar algún día qué
    miniatura generada acabó subida y qué CTR tuvo. Sin este registro, esa
    validación es imposible de reconstruir.
    """
    import time

    SALIDA.mkdir(parents=True, exist_ok=True)
    fila = {
        "ts": int(time.time()),
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tool": tool,
        "modelo": slug,
        "tipo": tipo,
        "huella": _huella(slug, tipo, prompt),
        "prompt": prompt,
        "fichero": str(fichero),
        "referencias": [f"{r['origen']}:{r['rol']}" for r in (refs or [])],
        "subida_a_youtube": None,   # se rellena a mano cuando se publique
    }
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def ruta_salida(prefijo: str, tipo: str, ext: str = "png") -> Path:
    SALIDA.mkdir(parents=True, exist_ok=True)
    sello = time.strftime("%Y%m%d-%H%M%S")
    return SALIDA / f"{prefijo}_{tipo}_{sello}.{ext}"


def tamanio_payload(cfg: dict, tipo: str) -> dict:
    """Traduce el formato de destino a las claves de tamaño que espera el modelo.

    Cada modelo de fal acepta unas claves y rechaza el resto, así que cuáles se
    envían está en `fal.claves_tamano` de la configuración: si una da 422, se
    quita de ahí sin tocar código.

    `image_size` va como objeto `{width, height}`, que es la forma universal de
    fal. Enviar la cadena "1280x720" no es válido y era el fallo que esto
    corrige.
    """
    fmt = cfg["formatos"][tipo]
    ancho, alto = (int(x) for x in fmt["px"].split("x"))
    claves = cfg["fal"].get("claves_tamano", ["image_size"])
    payload = {}
    if "image_size" in claves:
        payload["image_size"] = {"width": ancho, "height": alto}
    if "aspect_ratio" in claves:
        payload["aspect_ratio"] = fmt["ratio"]
    if "image_size_enum" in claves and fmt.get("enum_fal"):
        payload["image_size"] = fmt["enum_fal"]
    return payload


def validar_ratio(cfg: dict, tipo: str) -> None:
    """Las miniaturas son siempre 16:9. Se comprueba, no se confía."""
    fmt = cfg["formatos"].get(tipo)
    if fmt is None or not fmt.get("ratio_fijo"):
        return
    ancho, alto = (int(x) for x in fmt["px"].split("x"))
    esperado = tuple(int(x) for x in fmt["ratio"].split(":"))
    if abs(ancho / alto - esperado[0] / esperado[1]) > 0.01:
        raise ToolError(
            f"El formato '{tipo}' esta configurado a {fmt['px']}, que no es "
            f"{fmt['ratio']}.", EXIT_NO_DATA,
            "Las miniaturas son siempre 16:9. Corrige `px` en "
            "config/image_providers.json.")


def componer_prompt(tipo: str, prompt: str, refs: list[dict]) -> str:
    """Antepone el spec del formato y, si hay likeness, su cláusula."""
    partes = [SPEC.get(tipo, SPEC["general"])]
    for i, r in enumerate(refs, 1):
        if r["rol"] == "likeness":
            partes.append(LIKENESS.format(etiqueta=f"Reference Image {i}"))
            break
    partes.append(prompt)
    if refs:
        etiquetas = ", ".join(
            f"Reference Image {i} ({r['rol']} reference)" for i, r in enumerate(refs, 1))
        partes.append(f"Reference images provided, in order: {etiquetas}.")
        partes.append("Remove any watermark or third-party logo present in the "
                      "reference images.")
    partes.append("Do not add text that was not requested.")
    return " ".join(partes)


def ordenar_refs(refs: list[dict], cfg: dict) -> list[dict]:
    """Personas primero, objetos después, composición al final. Máximo 3."""
    orden = {"likeness": 0, "style": 1, "packaging": 2, "composition": 3}
    ordenadas = sorted(refs, key=lambda r: orden.get(r["rol"], 9))
    tope = cfg.get("max_referencias", 3)
    if len(ordenadas) > tope:
        raise ToolError(
            f"{len(ordenadas)} referencias, el maximo es {tope}.", EXIT_NO_DATA,
            "Mas referencias diluyen el resultado. Quita las menos importantes.")
    return ordenadas


def parsear_ref(valor: str, cfg: dict) -> dict:
    """`origen:rol`. Sin rol explícito no se adivina: se exige.

    El origen puede llevar dos puntos (una URL los lleva), así que el rol es
    siempre lo que va detrás del ÚLTIMO `:`.
    """
    ruta, _, rol = valor.rpartition(":")
    if not ruta or rol not in cfg["roles_de_referencia"]:
        raise ToolError(
            f"Referencia sin rol valido: {valor}", EXIT_NO_DATA,
            "Formato: --ref ORIGEN:ROL, con ROL en "
            f"{cfg['roles_de_referencia']}. El rol decide el orden de las "
            "referencias y si se aplica la clausula de likeness; adivinarlo "
            "estropea la cara.")
    return {"origen": ruta, "rol": rol}


def directiva_mcp(cfg: dict, accion: str, prompt: str, refs: list[dict],
                  tipo: str) -> dict:
    """En modo MCP esta tool no genera: devuelve qué debe llamar el agente.

    Un script no puede invocar una tool MCP de la sesión. En vez de fingir que
    puede, emite la llamada exacta y para.
    """
    m = cfg["mcp"]
    return {
        "modo": "mcp",
        "accion_requerida": (
            f"Esta tool NO ha generado nada. Llama tu mismo a la tool MCP "
            f"`{m['tools'].get(accion, 'generate_image')}` del servidor "
            f"`{m['servidor']}` con los parametros de `llamada`."
        ),
        "servidor": m["servidor"],
        "tool": m["tools"].get(accion, "generate_image"),
        "llamada": {
            "prompt": prompt,
            "model": m.get("modelo_por_defecto"),
            "aspect_ratio": cfg["formatos"][tipo]["ratio"],
            "referencias": [{"origen": r["origen"], "rol": r["rol"]} for r in refs],
        },
        "avisos": [
            f"Maximo {m.get('max_concurrentes')} generaciones simultaneas.",
            "Las tools MCP no leen ficheros locales: sube la imagen o pasa URL.",
            f"Si `{m['servidor']}` no aparece en la sesion, no esta conectado: "
            "conectalo en los ajustes de conectores, o cambia `provider` a 'fal' "
            "en config/image_providers.json.",
        ],
    }
