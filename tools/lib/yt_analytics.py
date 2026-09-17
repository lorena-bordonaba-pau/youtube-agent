"""YouTube Analytics API v2 — solo canal propio.

Incluye las dimensiones que el toolkit original nunca llegó a usar:
curva de retención (`elapsedVideoTimeRatio`) y detalle de fuentes de tráfico
(`insightTrafficSourceDetail`).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from . import auth
from .contrato import EXIT_NO_DATA, ToolError

_channel_id_cache = None


def channel_id() -> str:
    global _channel_id_cache
    if _channel_id_cache is None:
        resp = auth.youtube().channels().list(part="id", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            raise ToolError(
                "La cuenta autorizada no tiene ningun canal asociado.", EXIT_NO_DATA
            )
        _channel_id_cache = items[0]["id"]
    return _channel_id_cache


def _rango(days: int) -> tuple[str, str]:
    hoy = datetime.today()
    return (hoy - timedelta(days=days)).strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")


def _query(days: int, **kwargs) -> list[dict]:
    """Ejecuta un informe y devuelve filas como lista de dicts."""
    inicio, fin = _rango(days)
    resp = auth.analytics().reports().query(
        ids=f"channel=={channel_id()}", startDate=inicio, endDate=fin, **kwargs
    ).execute()
    headers = [c["name"] for c in resp["columnHeaders"]]
    return [dict(zip(headers, fila)) for fila in resp.get("rows", [])]


METRICAS_VIDEO = ("views,estimatedMinutesWatched,averageViewDuration,"
                  "averageViewPercentage,likes,comments,subscribersGained")


def canal(days: int = 28) -> list[dict]:
    return _query(days, dimensions="day", sort="day", metrics=(
        "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
        "subscribersGained,subscribersLost,likes,comments,shares"))


def top_videos(days: int = 90, max_results: int = 25) -> list[dict]:
    return _query(days, dimensions="video", sort="-views",
                  maxResults=max_results, metrics=METRICAS_VIDEO)


def video(video_id: str, days: int = 90) -> list[dict]:
    return _query(days, dimensions="day", sort="day",
                  filters=f"video=={video_id}", metrics=METRICAS_VIDEO)


def trafico(days: int = 28) -> list[dict]:
    return _query(days, dimensions="insightTrafficSourceType", sort="-views",
                  metrics="views,estimatedMinutesWatched")


def trafico_detalle(days: int = 28, tipo: str = "YT_SEARCH",
                    max_results: int = 25, video_id: str | None = None) -> list[dict]:
    """Detalle de una fuente de tráfico.

    Con tipo=YT_SEARCH devuelve los términos de búsqueda REALES que traen
    tráfico. Con RELATED_VIDEO, qué vídeos concretos están sugiriendo el tuyo.
    """
    filtros = f"insightTrafficSourceType=={tipo}"
    if video_id:
        filtros += f";video=={video_id}"
    # La API rechaza maxResults > 25 en insightTrafficSourceDetail con un 500
    # poco descriptivo (FIELD_UNKNOWN_VALUE en max-results).
    max_results = min(max_results, 25)
    return _query(days, dimensions="insightTrafficSourceDetail", sort="-views",
                  filters=filtros, maxResults=max_results,
                  metrics="views,estimatedMinutesWatched")


def demografia(days: int = 90) -> list[dict]:
    return _query(days, dimensions="ageGroup,gender", sort="-viewerPercentage",
                  metrics="viewerPercentage")


def geografia(days: int = 90, max_results: int = 20) -> list[dict]:
    datos = _query(days, dimensions="country", sort="-views", maxResults=max_results,
                   metrics="views,estimatedMinutesWatched,averageViewDuration")
    total = sum(d["views"] for d in datos)
    for d in datos:
        d["viewsPercent"] = round(d["views"] / total * 100, 1) if total else 0
    return datos


def retencion(video_id: str, days: int = 365) -> list[dict]:
    """Curva de retención: 101 puntos de 0.00 a 1.00 del vídeo.

    `audienceWatchRatio` es la proporción de espectadores viendo en ese punto.
    `relativeRetentionPerformance` compara con vídeos de duración similar en
    YouTube (0.5 = mediana).
    """
    return _query(days, dimensions="elapsedVideoTimeRatio", sort="elapsedVideoTimeRatio",
                  filters=f"video=={video_id}",
                  metrics="audienceWatchRatio,relativeRetentionPerformance")
