#!/usr/bin/env python3
"""Transcripción de un vídeo de YouTube (cualquier canal).

Primero intenta los subtítulos de YouTube (rápido, gratis, sin cuota de API).
Si no hay, descarga el audio y lo transcribe con whisper-cli.
Cachea 30 días: el contenido de un vídeo no cambia.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

from lib import base  # noqa: F401
from lib.contrato import (DATOS_DIR, EXIT_NO_DATA, SOURCE_API, SOURCE_DERIVED,
                          ToolError, emitir, main, parser, sobre)

TOOL = "yt_transcript"
DIR = DATOS_DIR / "transcripciones"

_TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->")
_TAG = re.compile(r"<[^>]+>")


def parsear_vtt(texto: str) -> list[dict]:
    """VTT -> lista de {t, texto}, deduplicando el efecto rollup de los
    subtítulos automáticos (que repiten cada línea varias veces)."""
    segmentos, actual, vistos = [], None, set()
    for linea in texto.splitlines():
        m = _TS.search(linea)
        if m:
            h, mi, s = (int(x) for x in m.groups())
            actual = h * 3600 + mi * 60 + s
            continue
        linea = _TAG.sub("", linea).strip()
        if not linea or linea.startswith(("WEBVTT", "Kind:", "Language:")) or actual is None:
            continue
        if linea in vistos:
            continue
        vistos.add(linea)
        if segmentos and segmentos[-1]["t"] == actual:
            segmentos[-1]["texto"] += " " + linea
        else:
            segmentos.append({"t": actual, "texto": linea})
    return segmentos


def via_subtitulos(video_id: str, idioma: str) -> list[dict] | None:
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            ["yt-dlp", "--skip-download", "--write-auto-sub", "--write-sub",
             "--sub-lang", idioma, "--sub-format", "vtt", "-o",
             str(Path(tmp) / "%(id)s"), f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=180)
        vtts = list(Path(tmp).glob("*.vtt"))
        if not vtts:
            return None
        return parsear_vtt(vtts[0].read_text(encoding="utf-8", errors="ignore"))


def via_whisper(video_id: str) -> list[dict] | None:
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video_id}.wav"
        r = subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "wav", "--postprocessor-args",
             "-ar 16000 -ac 1", "-o", str(Path(tmp) / "%(id)s.%(ext)s"),
             f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=900)
        if not audio.exists():
            cands = list(Path(tmp).glob("*.wav"))
            if not cands:
                return None
            audio = cands[0]
        salida = Path(tmp) / "out"
        subprocess.run(["whisper-cli", "-f", str(audio), "-l", "es", "-ovtt",
                        "-of", str(salida)],
                       capture_output=True, text=True, timeout=1800)
        vtt = salida.with_suffix(".vtt")
        if not vtt.exists():
            return None
        return parsear_vtt(vtt.read_text(encoding="utf-8", errors="ignore"))


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--lang", default="es")
    p.add_argument("--whisper", action="store_true",
                   help="fuerza whisper aunque haya subtítulos")
    p.add_argument("--plano", action="store_true", help="solo el texto, sin timestamps")
    args = p.parse_args()

    DIR.mkdir(parents=True, exist_ok=True)
    destino = DIR / f"{args.video}.{args.lang}.json"

    if destino.exists() and not args.no_cache:
        guardado = json.loads(destino.read_text(encoding="utf-8"))
        segmentos, metodo, hit = guardado["segmentos"], guardado["metodo"], True
    else:
        segmentos = None if args.whisper else via_subtitulos(args.video, args.lang)
        metodo = "subtitulos_youtube"
        if not segmentos:
            segmentos, metodo = via_whisper(args.video), "whisper_local"
        if not segmentos:
            raise ToolError(
                f"No se pudo transcribir {args.video}.", EXIT_NO_DATA,
                "Ni subtitulos disponibles ni audio descargable. Comprueba que "
                "el video es publico y que yt-dlp esta actualizado.")
        destino.write_text(json.dumps(
            {"video": args.video, "metodo": metodo, "segmentos": segmentos},
            ensure_ascii=False), encoding="utf-8")
        hit = False

    texto = " ".join(s["texto"] for s in segmentos)
    data = {"video": args.video, "metodo": metodo, "palabras": len(texto.split()),
            "duracion_s": segmentos[-1]["t"] if segmentos else 0,
            "texto": texto}
    if not args.plano:
        data["segmentos"] = segmentos

    # Los subtitulos vienen de YouTube; una transcripcion de Whisper la genera
    # esta maquina, y eso no es lo mismo.
    source = SOURCE_API if metodo == "subtitulos_youtube" else SOURCE_DERIVED
    env = sobre(TOOL, source, data, {"video": args.video, "lang": args.lang}, hit,
                notas=[f"Transcrito via {metodo}. Toda transcripcion automatica "
                       "tiene errores de reconocimiento: no citar literalmente "
                       "como palabras del autor sin verificar en el video."])
    emitir(env, args, lambda e: base.cabecera_md(e) + "\n" + e["data"]["texto"])


if __name__ == "__main__":
    main(TOOL, run)
