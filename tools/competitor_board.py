#!/usr/bin/env python3
"""Data for the competitor board artifact (artifacts/competitor-board/).

Takes @handles (or UC... channel IDs), pulls every long-form video each channel
published in the window, computes an outlier multiplier per video, flags videos
whose views look bought as ads, and embeds a small thumbnail, so the published
page needs no network. Writes one file per channel so the page downloads only
the channels that are switched on.
"""
from lib import base  # noqa: F401
import base64
import io
import json
import statistics
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib import auth, yt_data
from lib.contract import (DATA_DIR, EXIT_NO_DATA, SOURCE_DERIVED, ToolError,
                          emit, envelope, main, parser)

TOOL = "competitor_board"
DEFAULT_OUT = DATA_DIR / "reports" / "competitor_board"

# A video whose views arrive without the likes that normally come with them is
# the footprint of paid promotion (views bought as ads). Affiliate links are NOT
# the signal: almost every channel in a niche carries them.
AD_LIKE_SHARE = 0.2


def _now():
    return datetime.now(timezone.utc)


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _data_uri(url: str, size: tuple[int, int]) -> str | None:
    """Download an image and return it as a small JPEG data URI."""
    from PIL import Image
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            img = Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception:  # noqa: BLE001 — a missing thumbnail must not sink the run
        return None
    img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=60, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def score(stats: list[dict]) -> tuple[float, float]:
    """Flag ad suspects in place; return (organic median views, median likes/1k).

    Each stat needs `views` and `likes`. Adds `lpk` (likes per 1k views, None
    when unknown) and `ad_suspect`. Suspects stay out of the median: the
    baseline is what the channel does organically.
    """
    for s in stats:
        # 0 likes on 1k+ views means the likes are hidden, not that nobody liked it.
        s["lpk"] = (s["likes"] / s["views"] * 1000
                    if s["views"] >= 1000 and s["likes"] > 0 else None)
    lpks = [s["lpk"] for s in stats if s["lpk"] is not None]
    median_lpk = statistics.median(lpks) if lpks else 0
    first_median = statistics.median([s["views"] for s in stats]) if stats else 0
    for s in stats:
        s["ad_suspect"] = bool(median_lpk and s["lpk"] is not None
                               and s["views"] > first_median
                               and s["lpk"] < AD_LIKE_SHARE * median_lpk)
    organic = [s["views"] for s in stats if not s["ad_suspect"]]
    return (statistics.median(organic) if organic else 0), median_lpk


def resolve(yt, ref: str) -> dict | None:
    ref = ref.strip()
    parts = "snippet,statistics,contentDetails"
    if ref.startswith("UC") and len(ref) == 24:
        req = yt.channels().list(part=parts, id=ref)
    else:
        req = yt.channels().list(part=parts, forHandle="@" + ref.lstrip("@"))
    items = req.execute().get("items", [])
    return items[0] if items else None


def uploads_since(yt, playlist: str, cutoff: datetime) -> list[str]:
    """Video IDs from the uploads playlist, newest first, until the cutoff."""
    ids, token = [], None
    while True:
        resp = yt.playlistItems().list(part="contentDetails", playlistId=playlist,
                                       maxResults=50, pageToken=token).execute()
        stop = False
        for it in resp.get("items", []):
            cd = it["contentDetails"]
            when = cd.get("videoPublishedAt")
            if when and _parse(when) < cutoff:
                stop = True
                continue
            ids.append(cd["videoId"])
        token = resp.get("nextPageToken")
        if stop or not token:
            return ids


def paid_flags(yt, ids: list[str]) -> dict[str, bool]:
    """The creator's own "includes paid promotion" declaration, per video."""
    out = {}
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="paidProductPlacementDetails",
                                id=",".join(ids[i:i + 50])).execute()
        for it in resp.get("items", []):
            out[it["id"]] = bool(it.get("paidProductPlacementDetails", {})
                                 .get("hasPaidProductPlacement"))
    return out


def build_channel(yt, ref: str, cutoff: datetime, min_seconds: int,
                  own: bool = False) -> tuple[dict, list[dict]]:
    c = resolve(yt, ref)
    if not c:
        key = ref.strip().lstrip("@").lower()
        return {"key": key, "ref": ref, "error": "channel not found"}, []
    sn, st = c["snippet"], c["statistics"]
    handle = sn.get("customUrl") or ref
    key = handle.lstrip("@").lower()
    thumbs = sn.get("thumbnails", {})
    avatar_url = (thumbs.get("default") or thumbs.get("medium") or {}).get("url")

    ids = uploads_since(yt, c["contentDetails"]["relatedPlaylists"]["uploads"], cutoff)
    stats = [s for s in yt_data.video_stats(ids)
             if s["duration_s"] >= min_seconds
             and _parse(s["published_at"]) >= cutoff]
    paid = paid_flags(yt, [s["video_id"] for s in stats])
    median, median_lpk = score(stats)

    videos = []
    for s in stats:
        hours = max((_now() - _parse(s["published_at"])).total_seconds() / 3600, 1)
        videos.append({
            "id": s["video_id"],
            "ch": key,
            "title": s["title"],
            "published_at": s["published_at"],
            "views": s["views"],
            "ratio": round(s["views"] / median, 2) if median else None,
            "vph": round(s["views"] / hours, 1),
            "lpk": round(s["lpk"], 1) if s["lpk"] is not None else None,
            "like_share": round(s["lpk"] / median_lpk, 2)
            if s["lpk"] is not None and median_lpk else None,
            "paid": paid.get(s["video_id"], False),
            "ad_suspect": s["ad_suspect"],
            "duration": yt_data.fmt_duration(s["duration"]),
            "thumb": _data_uri(f"https://i.ytimg.com/vi/{s['video_id']}/mqdefault.jpg",
                               (224, 126)),
        })
    channel = {
        "key": key, "ref": ref, "channel_id": c["id"], "handle": handle,
        "title": sn["title"], "subs": int(st.get("subscriberCount", 0)),
        "avatar": _data_uri(avatar_url, (64, 64)) if avatar_url else None,
        "median_views": int(median), "median_lpk": round(median_lpk, 1),
        "n_videos": len(videos), "own": own,
    }
    return channel, videos


def _own_channel_id() -> str | None:
    """Your channel, through OAuth. The board works without it."""
    try:
        return yt_data.channel_info()["channel_id"]
    except Exception:  # noqa: BLE001 — no OAuth token is a normal setup
        return None


def _lang() -> str:
    try:
        return (yt_data.load_config().get("language") or "en")[:2]
    except ToolError:
        return "en"


def run():
    p = parser(__doc__)
    p.add_argument("--handles", nargs="*", default=[],
                   help="@handles or UC... channel IDs")
    p.add_argument("--handles-file",
                   help="JSON file with a list of @handles, or of objects with a "
                        "`handle` field (the board's `competitors` collection)")
    p.add_argument("--list", dest="items",
                   help="seed from a list in config/channels_lists.json "
                        "(competitors, inspiration...)")
    p.add_argument("--own", default="auto",
                   help="your own @handle or channel ID, shown behind the "
                        "'include my channel' switch. Default: your OAuth channel. "
                        "`none` to leave it out.")
    p.add_argument("--days", type=int, default=183)
    p.add_argument("--min-seconds", type=int, default=181,
                   help="drop videos shorter than this (Shorts proxy, default 181)")
    p.add_argument("--out", default=str(DEFAULT_OUT))
    args = p.parse_args()

    refs = list(args.handles)
    if args.handles_file:
        raw = json.loads(Path(args.handles_file).read_text())
        refs += [r["handle"] if isinstance(r, dict) else r for r in raw]
    if args.items:
        refs += [c["channel_id"] for c in yt_data.load_channels(args.items)]
    refs = list(dict.fromkeys(r for r in refs if r and r.strip()))
    if not refs:
        raise ToolError("No channels given.", EXIT_NO_DATA,
                        "Pass --handles @one @two, --handles-file list.json or "
                        "--list competitors.")
    own = (None if args.own.lower() == "none"
           else _own_channel_id() if args.own == "auto" else args.own)

    yt = auth.youtube(public_only=True)
    cutoff = _now() - timedelta(days=args.days)
    channels, videos = [], []
    for ref, is_own in [(r, False) for r in refs] + ([(own, True)] if own else []):
        ch, vids = build_channel(yt, ref, cutoff, args.min_seconds, is_own)
        channels.append(ch)
        videos += vids
    videos.sort(key=lambda v: v["published_at"], reverse=True)

    out = Path(args.out)
    (out / "ch").mkdir(parents=True, exist_ok=True)
    before = {f.stem for f in (out / "ch").glob("*.json")}
    for f in (out / "ch").glob("*.json"):
        f.unlink()
    written = set()
    for ch in channels:
        if ch.get("error"):
            continue
        mine = [v for v in videos if v["ch"] == ch["key"]]
        (out / "ch" / f"{ch['key']}.json").write_text(json.dumps(mine, ensure_ascii=False))
        written.add(ch["key"])
    (out / "index.json").write_text(json.dumps({
        "generated_at": _now().isoformat(timespec="seconds"),
        "source": SOURCE_DERIVED,
        "lang": _lang(),
        "window_days": args.days,
        "min_seconds": args.min_seconds,
        "ad_like_share": AD_LIKE_SHARE,
        "channels": channels,
    }, ensure_ascii=False))

    # Exactly what the Artifact tool's `files` parameter takes: every file to
    # publish next to the page, and null for channels that are gone.
    cwd = Path.cwd().resolve()
    rel = out.resolve().relative_to(cwd) if out.resolve().is_relative_to(cwd) else out
    publish_files = {"index.json": str(rel / "index.json")}
    publish_files |= {f"ch/{k}.json": str(rel / "ch" / f"{k}.json") for k in sorted(written)}
    publish_files |= {f"ch/{k}.json": None for k in sorted(before - written)}

    organic = sorted((v for v in videos if not v["ad_suspect"] and v["ratio"]),
                     key=lambda v: v["ratio"], reverse=True)
    by_key = {c["key"]: c for c in channels}
    top = [{"title": v["title"], "channel": by_key[v["ch"]]["title"],
            "video_id": v["id"], "ratio": v["ratio"], "views": v["views"],
            "days": (_now() - _parse(v["published_at"])).days,
            "likes_per_1k": v["lpk"]} for v in organic[:20]]
    env = envelope(TOOL, SOURCE_DERIVED, {
        "out": str(out),
        "size_kb": round(sum(f.stat().st_size for f in out.rglob("*.json")) / 1024),
        "total_videos": len(videos),
        "ad_suspects": sum(v["ad_suspect"] for v in videos),
        "channels": [{"handle": c.get("handle", c["ref"]), "title": c.get("title"),
                      "subs": c.get("subs"), "videos": c.get("n_videos", 0),
                      "median_views": c.get("median_views"), "error": c.get("error")}
                     for c in channels],
        "top_organic_outliers": top,
        "publish_files": publish_files,
    }, {"days": args.days, "min_seconds": args.min_seconds}, notes=[
        "`ratio` = views / median views of THAT channel's long-form videos in "
        "the window, excluding ad suspects.",
        f"`ad_suspect` is a HEURISTIC: views above the channel median with likes "
        f"per 1k views under {AD_LIKE_SHARE:.0%} of the channel's own median, the "
        "footprint of bought views. Declare it as an estimate.",
        "`paid` = the creator declared paid promotion (API). It marks a "
        "sponsorship, not bought views.",
        "`vph` = views / hours since publication: a lifetime average, not the "
        "current velocity.",
        "Recent videos have a deflated ratio: they have not finished "
        "accumulating views.",
    ])

    def md(e):
        d = e["data"]
        return "\n".join([
            base.md_header(e),
            f"\n**{d['total_videos']} videos**, {d['ad_suspects']} ad suspects "
            f"left out, {d['size_kb']} KB\n",
            base.md_table(d["channels"], ["handle", "title", "subs", "videos",
                                          "median_views", "error"]),
            "\n### Top organic outliers\n",
            base.md_table(d["top_organic_outliers"],
                          ["title", "channel", "ratio", "views", "days", "likes_per_1k"]),
        ])

    emit(env, args, md)


if __name__ == "__main__":
    main(TOOL, run)
