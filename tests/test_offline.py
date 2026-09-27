"""Tests that need no credentials, no network and no quota.

They cover the two things most likely to break silently: the contract every
tool shares, and the rubrics that turn a file of YAML into a score. An API
call cannot be tested here; the shape of what surrounds it can.

Run with:  python3 -m pytest tests/ -q      (or: python3 tests/test_offline.py)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from lib import imagegen as ig            # noqa: E402
from lib.contract import _SOURCES, envelope  # noqa: E402


def _run(*args, expect_ok=True):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT)
    if expect_ok:
        assert r.returncode == 0, f"{args} exited {r.returncode}\n{r.stderr[:400]}"
    return r


# --- the contract ----------------------------------------------------------

def test_every_tool_runs_help():
    """A tool that cannot even print --help is broken for everyone."""
    broken = []
    for f in sorted(TOOLS.glob("*.py")):
        r = _run(str(f), "--help", expect_ok=False)
        # auth_setup legitimately refuses without client_secrets.json
        if r.returncode != 0 and "client_secrets" not in r.stderr:
            broken.append(f"{f.name}: {r.stderr.strip()[:120]}")
    assert not broken, "tools failing --help:\n" + "\n".join(broken)


def test_envelope_rejects_unknown_source():
    """`source` is the honesty mechanism: an unknown value must not pass."""
    try:
        envelope("t", "made_up", {})
    except ValueError:
        return
    raise AssertionError("envelope() accepted an invalid source")


def test_envelope_carries_provenance():
    for source in _SOURCES:
        env = envelope("t", source, {"x": 1})
        assert env["source"] == source
        assert env["notice"], f"{source} has no notice text"


def test_usage_error_does_not_collide_with_auth():
    """argparse exits 2 by default, which is our auth code. Must be 64."""
    r = _run(str(TOOLS / "yt_video_stats.py"), expect_ok=False)
    assert r.returncode == 64, f"expected 64, got {r.returncode}"


# --- rubrics ---------------------------------------------------------------

def test_rubrics_are_valid_and_declare_calibration():
    import yaml
    for name in ("titles.yaml", "thumbnails.yaml"):
        d = yaml.safe_load((ROOT / "config" / "rubrics" / name).read_text(encoding="utf-8"))
        assert "validated_against_ctr" in d, f"{name} does not declare validation"
        axes = d.get("axes") or (d.get("automatic_axes", []) + d.get("judgement_axes", []))
        assert axes, f"{name} has no axes"
        for a in axes:
            assert "id" in a and "weight" in a, f"{name}: malformed axis {a}"


def test_score_titles_runs_and_is_labelled_heuristic():
    r = _run(str(TOOLS / "score_titles.py"), "--title", "I built this in 3 hours")
    d = json.loads(r.stdout)
    assert d["source"] == "heuristic", "a score must never be presented as measured data"
    assert 0 <= d["data"]["results"][0]["score"] <= 100


def test_score_thumbnail_leaves_judgement_axes_open():
    """The 60% it cannot measure must come back unanswered, not invented."""
    from PIL import Image
    img = ROOT / "data" / "images" / "_test.jpg"
    img.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1280, 720), (20, 90, 180)).save(img)
    try:
        r = _run(str(TOOLS / "score_thumbnail.py"), "--image", str(img))
        d = json.loads(r.stdout)["data"]
        assert d["total_score"] is None, "it must not produce a total score on its own"
        assert d["pending_judgement_axes"], "the judgement axes disappeared"
        assert all(a["points"] is None for a in d["pending_judgement_axes"])
    finally:
        img.unlink(missing_ok=True)


# --- image branch ----------------------------------------------------------

def test_thumbnails_are_always_16_9():
    cfg = ig.load()
    fmt = cfg["formats"]["thumbnail"]
    assert fmt.get("fixed_ratio") is True
    w, h = (int(x) for x in fmt["px"].split("x"))
    assert abs(w / h - 16 / 9) < 0.01
    ig.validate_ratio(cfg, "thumbnail")


def test_reference_without_a_role_is_rejected():
    cfg = ig.load()
    try:
        ig.parse_ref("photo.jpg", cfg)
    except Exception:
        return
    raise AssertionError("a reference with no role was accepted")


def test_references_are_ordered_people_first():
    cfg = ig.load()
    refs = [{"source": "a", "role": "composition"}, {"source": "b", "role": "likeness"}]
    assert ig.sort_refs(refs, cfg)[0]["role"] == "likeness"


def test_dry_run_spends_nothing_and_shows_the_prompt():
    r = _run(str(TOOLS / "generate_image.py"), "--type", "banner",
             "--prompt", "a test", "--dry-run")
    d = json.loads(r.stdout)
    assert d["source"] == "config", "a dry run must not be labelled as generated"
    assert "CRITICAL COMPOSITION RULE" in d["data"]["final_prompt"], \
        "the banner safe-zone rule is missing from the prompt"


def test_references_switch_to_the_edit_model():
    """The `generate` slug is text-to-image and discards `image_urls`: with a
    reference it produced faces that were not the creator's."""
    ref = ROOT / "data" / "images" / "_ref.png"
    ref.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (64, 64)).save(ref)
    try:
        r = _run(str(TOOLS / "generate_image.py"), "--prompt", "a test",
                 "--ref", f"{ref}:likeness", "--dry-run")
        models = ig.load()["fal"]["models"]
        assert json.loads(r.stdout)["data"]["model_slug"] == \
            (models.get("edit_gpt") or models["edit"])
    finally:
        ref.unlink(missing_ok=True)


def test_export_image_is_deterministic_and_exact():
    from PIL import Image
    src = ROOT / "data" / "images" / "_src.png"
    out = ROOT / "data" / "images" / "_out.jpg"
    src.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1920, 1080), (200, 30, 30)).save(src)
    try:
        _run(str(TOOLS / "export_image.py"), "--image", str(src),
             "--type", "thumbnail", "--out", str(out))
        with Image.open(out) as im:
            assert im.size == (1280, 720), f"got {im.size}"
    finally:
        src.unlink(missing_ok=True)
        out.unlink(missing_ok=True)


def test_tools_agree_on_the_video_id_field():
    """Chaining only works if every tool calls the identifier the same thing.

    The channel-analytics skill feeds yt_top_videos into yt_retention; when one
    returned `video` and the other expected `video_id`, that flow broke and
    nothing failed loudly."""
    import re
    offenders = []
    for f in sorted(TOOLS.glob("*.py")):
        src = f.read_text(encoding="utf-8")
        # `"video":` as an output field. A value that is a list is a column
        # alias table, not output, so it is skipped.
        for m in re.finditer(r'^\s*"video":(?!\s*\[)', src, re.M):
            line = src[:m.start()].count("\n") + 1
            offenders.append(f"{f.name}:{line}")
    assert not offenders, (
        "these emit `video` instead of `video_id`: " + ", ".join(offenders))


def test_cache_is_versioned():
    """A change in output shape must invalidate cached entries, or an upgrade
    keeps serving the old field names until each TTL expires."""
    from lib import cache
    assert isinstance(cache.SCHEMA, int) and cache.SCHEMA >= 1
    a = cache._path("own_analytics", "k")
    cache.SCHEMA += 1
    try:
        assert cache._path("own_analytics", "k") != a, \
            "bumping SCHEMA does not change the cache path"
    finally:
        cache.SCHEMA -= 1


def test_no_mangled_english_in_user_facing_strings():
    """A bulk rename once turned "error" into "err" inside a message the user
    reads. Cheap to guard, embarrassing to ship."""
    import re
    bad = [r"\berr\b(?!or)", r"\benvelope (el|the|los|las)\b", r"payload_data/",
           r"\bmodel_slug\b(?=[ .,])", r"\bthumbnail_cache\b(?=[ .,])",
           # Spanish left behind inside English messages by the translation
           r"\bhace \{?\w+\}? days\b", r"\bTranscrito\b", r"\*\*Modelo\*\*",
           r"\bListas disponibles\b", r"\bo pasa --", r"\bORIGEN:ROL\b"]
    pat = re.compile("|".join(bad))
    hits = []
    for f in list(TOOLS.rglob("*.py")) + list((ROOT / "config").rglob("*.yaml")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = pat.search(line)
            if m:
                hits.append(f"{f.name}:{i} contains {m.group(0)!r}")
    assert not hits, "mangled strings:\n" + "\n".join(hits)


def test_skill_names_match_their_folders():
    """A skill whose front-matter name differs from its folder is invisible:
    the agent looks it up by one and finds the other."""
    bad = []
    for d in sorted((ROOT / ".claude" / "skills").iterdir()):
        if not d.is_dir():
            continue
        for line in (d / "SKILL.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                if line.split(":", 1)[1].strip() != d.name:
                    bad.append(f"{d.name} declares {line.strip()!r}")
                break
        else:
            bad.append(f"{d.name} has no name in its front matter")
    assert not bad, "\n".join(bad)


def test_front_matter_is_valid_yaml():
    """An unquoted ": " inside a description makes the front matter invalid
    YAML. A lenient loader may still show the skill, but fields after it (an
    agent's `hooks`, for one) are then at the mercy of the parser."""
    import yaml
    claude = ROOT / ".claude"
    bad = []
    for f in sorted([*claude.glob("skills/*/SKILL.md"), *claude.glob("agents/*.md"),
                     *claude.glob("commands/*.md")]):
        text = f.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        try:
            meta = yaml.safe_load(text.split("---", 2)[1])
            assert isinstance(meta, dict) and meta.get("description")
        except Exception as e:  # noqa: BLE001
            bad.append(f"{f.relative_to(ROOT)}: {str(e).splitlines()[0]}")
    assert not bad, "\n".join(bad)


def test_skills_share_one_skeleton():
    """Every skill says when it applies, where its figures come from and what
    it delivers, in that order. Skill-specific sections go in between."""
    bad = []
    for f in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        heads = [l[3:].strip() for l in f.read_text(encoding="utf-8").splitlines()
                 if l.startswith("## ")]
        need = ["WHEN", "SOURCES", "OUTPUT"]
        if [h for h in heads if h in need] != need or heads[0] != "WHEN" \
                or heads[-1] != "OUTPUT":
            bad.append(f"{f.parent.name}: {heads}")
    assert not bad, "skills off the WHEN … SOURCES → OUTPUT skeleton:\n" + "\n".join(bad)


def test_channel_lists_ignore_documentation_keys():
    """channels_lists.json carries an `_instructions` key. Read as a list, it
    broke every tool that loads all lists at once (radar included)."""
    r = _run(str(TOOLS / "yt_channels_list.py"), "--json")
    assert json.loads(r.stdout)["source"] == "config"


def test_reference_prompt_avoids_blocked_wording():
    """fal.ai's content checker rejects "watermark": with it in the prompt,
    every generation with a reference failed with content_policy_violation."""
    prompt = ig.compose_prompt("thumbnail", "a test", [{"role": "likeness"}])
    assert "watermark" not in prompt.lower(), prompt


def test_spend_hook_asks_only_when_money_or_quota_is_at_stake():
    """`Bash(python3 tools/*)` is allowed wholesale; the hook is what stops an
    image generation or a 100-unit search from running without a yes."""
    hook = ROOT / ".claude" / "hooks" / "confirm_spend.py"

    def decision(command):
        r = subprocess.run([sys.executable, str(hook)], capture_output=True, text=True,
                           input=json.dumps({"tool_input": {"command": command}}))
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] \
            if r.stdout.strip() else None

    assert decision("python3 tools/generate_image.py --prompt x") == "ask"
    assert decision("python3 tools/refine_image.py --image a.png") == "ask"
    assert decision("python3 tools/yt_search.py --query x") == "ask"
    assert decision("python3 tools/kw_research.py --kw x") == "ask"
    assert decision("python3 tools/yt_discover_channels.py --terms x") == "ask"
    assert decision("python3 tools/generate_image.py --prompt x --dry-run") is None
    assert decision("python3 tools/kw_research.py --kw x --no-competition") is None
    assert decision("python3 tools/yt_report.py") is None


def test_strategist_can_only_write_to_memory():
    hook = ROOT / ".claude" / "hooks" / "memory_only.py"

    def exit_code(path):
        return subprocess.run(
            [sys.executable, str(hook)], capture_output=True, text=True,
            env={"CLAUDE_PROJECT_DIR": str(ROOT)},
            input=json.dumps({"tool_input": {"file_path": path}})).returncode

    assert exit_code(str(ROOT / "memory" / "channel_positioning.md")) == 0
    assert exit_code("memory/sop/pillars_sop.md") == 0
    assert exit_code(str(ROOT / "tools" / "init.py")) == 2
    assert exit_code(str(ROOT / "memory" / ".." / "CLAUDE.md")) == 2


def test_discovery_keeps_only_videos_clearing_every_threshold():
    from datetime import datetime, timedelta, timezone
    from lib import discovery
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    th = discovery.thresholds({"discovery": {"min_views": 50_000}})
    assert th["min_views"] == 50_000 and th["min_ratio"] == 3.0

    def v(vid, cid, views, days_ago, dur=600, title="How I did it"):
        when = (now - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"video_id": vid, "channel_id": cid, "channel_title": cid,
                "title": title, "views": views, "duration_s": dur,
                "published_at": when, "language": "en", "term": "t"}
    videos = [v("ok", "A", 90_000, 10),
              v("low_ratio", "B", 90_000, 10),
              v("few_views", "A", 10_000, 10),
              v("short", "A", 90_000, 10, dur=45),
              v("old", "A", 90_000, 200),
              v("pod", "C", 90_000, 10, title="The Podcast ep. 12")]
    found = discovery.outliers(videos, {"A": 20_000, "B": 60_000, "C": 10_000}, th, now)
    assert sorted(f["video_id"] for f in found) == ["ok", "pod"]
    assert next(f for f in found if f["video_id"] == "pod")["not_solo"]

    rows = discovery.group_by_channel(found, existing={"C": "inspiration"})
    assert next(r for r in rows if r["channel_id"] == "C")["already_in"] == "inspiration"
    assert next(r for r in rows if r["channel_id"] == "A")["languages"] == ["en"]


def test_channel_list_edits_keep_one_list_per_channel_and_the_docs():
    from lib import discovery
    cfg = {"_instructions": ["keep me"], "competitors": [], "inspiration": []}
    cfg = discovery.add_channel(cfg, "competitors", {"channel_id": "X", "name": "x"})
    cfg = discovery.add_channel(cfg, "inspiration", {"channel_id": "X", "name": "x"})
    assert cfg["competitors"] == [] and cfg["inspiration"][0]["channel_id"] == "X"
    assert cfg["_instructions"] == ["keep me"]
    assert discovery.remove_channel(cfg, "X")["inspiration"] == []
    try:
        discovery.add_channel(cfg, "_instructions", {"channel_id": "Y"})
    except ValueError:
        pass
    else:
        raise AssertionError("a documentation key was accepted as a list")


def test_strategy_template_starts_the_kickoff():
    """init.py reads the Stage line; an unfilled strategy must start at the start."""
    text = (ROOT / "memory" / "strategy.md").read_text(encoding="utf-8")
    assert "**Stage:**" in text
    if "NOT POPULATED" in text:
        assert "**Stage:** not started" in text


def test_data_directories_exist_on_a_fresh_clone():
    """The install guide tells you to save client_secrets.json into
    data/auth/. If .gitignore excludes the directory itself, git cannot ship
    the .gitkeep inside it and that path does not exist after cloning."""
    missing = [d for d in ("auth", "cache", "history", "reports", "transcripts",
                           "thumbnails", "packaging", "images")
               if not (ROOT / "data" / d / ".gitkeep").exists()]
    assert not missing, f"data/ subdirectories not shipped: {missing}"


def test_board_flags_bought_views_and_keeps_them_out_of_the_median():
    """An ad-promoted video posted 323x on the real board: 25M views, 0.4 likes
    per 1k against a channel usual of ~20. Hidden likes (0) must not trip it."""
    sys.path.insert(0, str(TOOLS))
    import competitor_board as cb
    organic = [{"views": v, "likes": v // 50} for v in (8000, 10000, 12000, 15000)]
    ad = {"views": 900000, "likes": 360}            # 0.4 likes per 1k
    hidden = {"views": 40000, "likes": 0}           # likes hidden by the creator
    stats = organic + [ad, hidden]
    median, median_lpk = cb.score(stats)
    assert ad["ad_suspect"] and not hidden["ad_suspect"]
    assert hidden["lpk"] is None
    assert not any(s["ad_suspect"] for s in organic)
    assert median == 12000, "the ad video leaked into the baseline"
    assert round(median_lpk) == 20


def test_board_page_only_fetches_what_it_publishes():
    """The artifact sandbox blocks every network call except files published
    next to the page. A fetch to anything else fails silently for the viewer."""
    import re
    page = (ROOT / "artifacts" / "competitor-board" / "index.html").read_text(encoding="utf-8")
    fetched = re.findall(r'fetch\(\s*["\']?([^"\')]+)', page)
    assert fetched, "the board no longer fetches its data"
    assert all(not f.startswith("http") for f in fetched), fetched


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
