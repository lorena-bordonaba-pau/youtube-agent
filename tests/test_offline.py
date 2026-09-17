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
    img = ROOT / "datos" / "images" / "_test.jpg"
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


def test_export_image_is_deterministic_and_exact():
    from PIL import Image
    src = ROOT / "datos" / "images" / "_src.png"
    out = ROOT / "datos" / "images" / "_out.jpg"
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


def test_data_directories_exist_on_a_fresh_clone():
    """The install guide tells you to save client_secrets.json into
    data/auth/. If .gitignore excludes the directory itself, git cannot ship
    the .gitkeep inside it and that path does not exist after cloning."""
    missing = [d for d in ("auth", "cache", "history", "reports", "transcripts",
                           "thumbnails", "packaging", "images")
               if not (ROOT / "data" / d / ".gitkeep").exists()]
    assert not missing, f"data/ subdirectories not shipped: {missing}"


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
