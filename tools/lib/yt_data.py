"""YouTube Data API v3 — cualquier canal público.

Consolida los helpers que en el toolkit original estaban copiados en tres
ficheros (`_fmt`, `_fmt_duration`, `_get_video_stats_batch`).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from . import auth
from .contrato import CONFIG_DIR, EXIT_NO_DATA, ToolError

# --- Formato ---------------------------------------------------------------

def fmt(n) -> str:
    """1234567 -> '1.2M'"""
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


_DUR = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def fmt_duracion(iso: str) -> str:
    """'PT1H2M3S' -> '1:02:03'"""
    m = _DUR.match(iso or "")
    if not m:
        return "?"
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return f"{h}:{mi:02d}:{s:02d}" if h else f"{mi}:{s:02d}"


def segundos(iso: str) -> int:
    m = _DUR.match(iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


# --- Canales ---------------------------------------------------------------

def canal_info(channel_id: str | None = None) -> dict:
    """Info de un canal. Sin argumento, el canal propio."""
    yt = auth.youtube()
    parts = "snippet,statistics,contentDetails"
    req = (yt.channels().list(part=parts, mine=True) if channel_id is None
           else yt.channels().list(part=parts, id=channel_id))
    items = req.execute().get("items", [])
    if not items:
        raise ToolError(f"Canal no encontrado: {channel_id or 'propio'}", EXIT_NO_DATA)
    c = items[0]
    st, sn = c["statistics"], c["snippet"]
    return {
        "channel_id": c["id"],
        "title": sn["title"],
        "description": sn.get("description", ""),
        "country": sn.get("country"),
        "created_at": sn.get("publishedAt"),
        "subscribers": int(st.get("subscriberCount", 0)),
        "total_views": int(st.get("viewCount", 0)),
        "total_videos": int(st.get("videoCount", 0)),
        "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def videos_de_canal(channel_id: str | None = None, max_results: int = 50) -> list[dict]:
    """Vídeos recientes de un canal, del más nuevo al más antiguo."""
    yt = auth.youtube()
    uploads = canal_info(channel_id)["uploads_playlist"]
    videos, token = [], None
    while len(videos) < max_results:
        resp = yt.playlistItems().list(
            part="snippet", playlistId=uploads,
            maxResults=min(50, max_results - len(videos)), pageToken=token,
        ).execute()
        for it in resp.get("items", []):
            sn = it["snippet"]
            thumbs = sn.get("thumbnails", {})
            mejor = thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default", {})
            videos.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn["title"],
                "published_at": sn.get("publishedAt"),
                "description": sn.get("description", ""),
                "thumbnail": mejor.get("url"),
            })
        token = resp.get("nextPageToken")
        if not token:
            break
    return videos[:max_results]


# --- Vídeos ----------------------------------------------------------------

def stats_videos(video_ids: list[str]) -> list[dict]:
    """Estadísticas públicas en lotes de 50."""
    if not video_ids:
        return []
    yt = auth.youtube()
    salida = []
    for i in range(0, len(video_ids), 50):
        lote = video_ids[i:i + 50]
        resp = yt.videos().list(
            part="snippet,statistics,contentDetails", id=",".join(lote)
        ).execute()
        for v in resp.get("items", []):
            st, sn, cd = v["statistics"], v["snippet"], v["contentDetails"]
            thumbs = sn.get("thumbnails", {})
            mejor = thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default", {})
            vistas = int(st.get("viewCount", 0))
            likes = int(st.get("likeCount", 0))
            comentarios = int(st.get("commentCount", 0))
            salida.append({
                "video_id": v["id"],
                "title": sn["title"],
                "channel_id": sn["channelId"],
                "channel_title": sn["channelTitle"],
                "published_at": sn.get("publishedAt"),
                "description": sn.get("description", ""),
                "tags": sn.get("tags", []),
                "thumbnail": mejor.get("url"),
                "duration": cd.get("duration"),
                "duration_s": segundos(cd.get("duration", "")),
                "views": vistas,
                "likes": likes,
                "comments": comentarios,
                "engagement_rate": round((likes + comentarios) / vistas * 100, 2)
                if vistas else 0,
            })
    return salida


def media_vistas_canal(channel_id: str, muestra: int = 15) -> float:
    """Media de vistas de las últimas N subidas — base del ratio de outlier."""
    vids = videos_de_canal(channel_id, max_results=muestra)
    if not vids:
        return 0.0
    stats = stats_videos([v["video_id"] for v in vids])
    if not stats:
        return 0.0
    return sum(s["views"] for s in stats) / len(stats)


def items_playlist(playlist_id: str, days: int | None = None) -> list[dict]:
    """Ítems de una playlist. Con `days`, solo los añadidos recientemente."""
    yt = auth.youtube()
    corte = (datetime.now(timezone.utc) - timedelta(days=days)) if days else None
    items, token = [], None
    while True:
        resp = yt.playlistItems().list(
            part="snippet", playlistId=playlist_id, maxResults=50, pageToken=token
        ).execute()
        for it in resp.get("items", []):
            sn = it["snippet"]
            añadido = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            if corte and añadido < corte:
                return items  # la playlist viene del más reciente al más antiguo
            items.append({
                "video_id": sn["resourceId"]["videoId"],
                "title": sn["title"],
                "added_at": sn["publishedAt"],
            })
        token = resp.get("nextPageToken")
        if not token:
            return items


def buscar(query: str, max_results: int = 10, orden: str = "viewCount",
           duracion: str = "medium", dias: int | None = None) -> list[dict]:
    """search.list — CUESTA 100 UNIDADES DE CUOTA. Siempre cachear."""
    yt = auth.youtube()
    params = {
        "part": "snippet", "q": query, "type": "video", "order": orden,
        "maxResults": max_results,
    }
    if duracion and duracion != "any":
        params["videoDuration"] = duracion
    if dias:
        desde = datetime.now(timezone.utc) - timedelta(days=dias)
        params["publishedAfter"] = desde.strftime("%Y-%m-%dT%H:%M:%SZ")
    resp = yt.search().list(**params).execute()
    ids = [it["id"]["videoId"] for it in resp.get("items", [])]
    return stats_videos(ids)


# --- Configuración ---------------------------------------------------------

def cargar_config() -> dict:
    ruta = CONFIG_DIR / "config.json"
    if not ruta.exists():
        raise ToolError(f"Falta {ruta}", EXIT_NO_DATA)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_canales(lista: str | None = None) -> list[dict]:
    """Canales de competencia e inspiración, con su `list_type` inyectado."""
    ruta = CONFIG_DIR / "channels_lists.json"
    if not ruta.exists():
        raise ToolError(f"Falta {ruta}", EXIT_NO_DATA)
    with open(ruta, encoding="utf-8") as f:
        cfg = json.load(f)
    if lista and lista not in cfg:
        raise ToolError(
            f"La lista {lista!r} no existe en {ruta.name}.", EXIT_NO_DATA,
            f"Listas disponibles: {', '.join(cfg)}")
    salida = []
    for tipo, entradas in cfg.items():
        if lista and tipo != lista:
            continue
        for e in entradas:
            salida.append({**e, "list_type": tipo})
    return salida
