"""YouTube Analytics API v2 — your own channel only.

Includes the dimensions most toolkits never touch: the retention curve
(`elapsedVideoTimeRatio`) and traffic source detail
(`insightTrafficSourceDetail`).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from . import auth
from .contract import EXIT_NO_DATA, ToolError

_channel_id_cache = None


def channel_id() -> str:
    global _channel_id_cache
    if _channel_id_cache is None:
        resp = auth.youtube().channels().list(part="id", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            raise ToolError(
                "The authorised account has no channel associated with it.", EXIT_NO_DATA
            )
        _channel_id_cache = items[0]["id"]
    return _channel_id_cache


def _range(days: int) -> tuple[str, str]:
    hoy = datetime.today()
    return (hoy - timedelta(days=days)).strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d")


def _query(days: int, **kwargs) -> list[dict]:
    """Run a report and return the rows as a list of dicts."""
    start, end = _range(days)
    resp = auth.analytics().reports().query(
        ids=f"channel=={channel_id()}", startDate=start, endDate=end, **kwargs
    ).execute()
    headers = [c["name"] for c in resp["columnHeaders"]]
    return [dict(zip(headers, row)) for row in resp.get("rows", [])]


METRICAS_VIDEO = ("views,estimatedMinutesWatched,averageViewDuration,"
                  "averageViewPercentage,likes,comments,subscribersGained")


def channel(days: int = 28) -> list[dict]:
    return _query(days, dimensions="day", sort="day", metrics=(
        "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
        "subscribersGained,subscribersLost,likes,comments,shares"))


def top_videos(days: int = 90, max_results: int = 25) -> list[dict]:
    # The Analytics API calls the dimension `video`; every other tool in this
    # harness calls it `video_id`. Normalised in top_videos() below so the
    # output of one tool can be fed straight into the next.
    rows = _query(days, dimensions="video", sort="-views",
                  maxResults=max_results, metrics=METRICAS_VIDEO)
    for r in rows:
        r["video_id"] = r.pop("video", None)
    return rows


def video(video_id: str, days: int = 90) -> list[dict]:
    return _query(days, dimensions="day", sort="day",
                  filters=f"video=={video_id}", metrics=METRICAS_VIDEO)


def traffic(days: int = 28) -> list[dict]:
    return _query(days, dimensions="insightTrafficSourceType", sort="-views",
                  metrics="views,estimatedMinutesWatched")


def traffic_detail(days: int = 28, kind: str = "YT_SEARCH",
                    max_results: int = 25, video_id: str | None = None) -> list[dict]:
    """Detail for one traffic source.

    With kind=YT_SEARCH it returns the REAL search terms bringing traffic.
    With RELATED_VIDEO, which specific videos are suggesting yours.
    """
    filtros = f"insightTrafficSourceType=={kind}"
    if video_id:
        filtros += f";video=={video_id}"
    # The API rejects maxResults > 25 on insightTrafficSourceDetail with an
    # unhelpful 500 (FIELD_UNKNOWN_VALUE on max-results).
    max_results = min(max_results, 25)
    return _query(days, dimensions="insightTrafficSourceDetail", sort="-views",
                  filters=filtros, maxResults=max_results,
                  metrics="views,estimatedMinutesWatched")


def demographics(days: int = 90) -> list[dict]:
    return _query(days, dimensions="ageGroup,gender", sort="-viewerPercentage",
                  metrics="viewerPercentage")


def geography(days: int = 90, max_results: int = 20) -> list[dict]:
    payload_data = _query(days, dimensions="country", sort="-views", maxResults=max_results,
                   metrics="views,estimatedMinutesWatched,averageViewDuration")
    total = sum(d["views"] for d in payload_data)
    for d in payload_data:
        d["viewsPercent"] = round(d["views"] / total * 100, 1) if total else 0
    return payload_data


def retention(video_id: str, days: int = 365) -> list[dict]:
    """Retention curve: 101 points from 0.00 to 1.00 of the video.

    `audienceWatchRatio` is the share of viewers still watching at that point.
    `relativeRetentionPerformance` compares against videos of similar length
    across YouTube (0.5 = median).
    """
    return _query(days, dimensions="elapsedVideoTimeRatio", sort="elapsedVideoTimeRatio",
                  filters=f"video=={video_id}",
                  metrics="audienceWatchRatio,relativeRetentionPerformance")
