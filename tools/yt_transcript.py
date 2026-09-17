#!/usr/bin/env python3
"""Transcript of a YouTube video (any channel).

It tries YouTube captions first (fast, free, no API quota). If there are
none, it downloads the audio and transcribes it with whisper-cli.
Cached for 30 days: a video's content does not change.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

from lib import base  # noqa: F401
from lib.contract import (CONFIG_DIR, DATA_DIR, EXIT_NO_DATA, SOURCE_API, SOURCE_DERIVED,
                          ToolError, emit, main, parser, envelope)

# Language/region for autocomplete and transcription. Set `language` and
# `region` in config/config.json; they default to English.
def _locale():
    try:
        import json as _j
        c = _j.loads((CONFIG_DIR / "config.json").read_text(encoding="utf-8"))
        return c.get("language", "en"), c.get("region", "us")
    except Exception:  # noqa: BLE001 — a missing config must not break the tool
        return "en", "us"


LANG, REGION = _locale()

TOOL = "yt_transcript"
DIR = DATA_DIR / "transcripts"

_TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->")
_TAG = re.compile(r"<[^>]+>")


def parsear_vtt(text: str) -> list[dict]:
    """VTT -> list of {t, text}, de-duplicating the rollup effect of auto
    captions, which repeat each line several times."""
    segments, current, vistos = [], None, set()
    for line in text.splitlines():
        m = _TS.search(line)
        if m:
            h, mi, s = (int(x) for x in m.groups())
            current = h * 3600 + mi * 60 + s
            continue
        line = _TAG.sub("", line).strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")) or current is None:
            continue
        if line in vistos:
            continue
        vistos.add(line)
        if segments and segments[-1]["t"] == current:
            segments[-1]["text"] += " " + line
        else:
            segments.append({"t": current, "text": line})
    return segments


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
        out = Path(tmp) / "out"
        subprocess.run(["whisper-cli", "-f", str(audio), "-l", args.lang, "-ovtt",
                        "-of", str(out)],
                       capture_output=True, text=True, timeout=1800)
        vtt = out.with_suffix(".vtt")
        if not vtt.exists():
            return None
        return parsear_vtt(vtt.read_text(encoding="utf-8", errors="ignore"))


def run():
    p = parser(__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--lang", default=LANG,
                   help="caption/transcription language code (default from "
                        "config.json `language`, else `en`)")
    p.add_argument("--whisper", action="store_true",
                   help="force whisper even when captions exist")
    p.add_argument("--plain", action="store_true", help="text only, no timestamps")
    args = p.parse_args()

    DIR.mkdir(parents=True, exist_ok=True)
    dest = DIR / f"{args.video}.{args.lang}.json"

    if dest.exists() and not args.no_cache:
        saved = json.loads(dest.read_text(encoding="utf-8"))
        segments, method, hit = saved["segments"], saved["method"], True
    else:
        segments = None if args.whisper else via_subtitulos(args.video, args.lang)
        method = "subtitulos_youtube"
        if not segments:
            segments, method = via_whisper(args.video), "whisper_local"
        if not segments:
            raise ToolError(
                f"Could not transcribe {args.video}.", EXIT_NO_DATA,
                "No captions available and no downloadable audio. Check the "
                "video is public and that yt-dlp is up to date.")
        dest.write_text(json.dumps(
            {"video_id": args.video, "method": method, "segments": segments},
            ensure_ascii=False), encoding="utf-8")
        hit = False

    text = " ".join(s["text"] for s in segments)
    data = {"video_id": args.video, "method": method, "words": len(text.split()),
            "duration_s": segments[-1]["t"] if segments else 0,
            "text": text}
    if not args.plain:
        data["segments"] = segments

    # Captions come from YouTube; a Whisper transcript is generated on this
    # machine, and those are not the same thing.
    source = SOURCE_API if method == "subtitulos_youtube" else SOURCE_DERIVED
    env = envelope(TOOL, source, data, {"video": args.video, "lang": args.lang}, hit,
                notes=[f"Transcrito via {method}. Toda transcript_cache automatica "
                       "has recognition errors: do not quote it verbatim as the "
                       "author's words without checking the video."])
    emit(env, args, lambda e: base.md_header(e) + "\n" + e["data"]["text"])


if __name__ == "__main__":
    main(TOOL, run)
