"""Integration tests against real media in samples/. Skip cleanly when absent.

``samples/expected`` holds Wes's approved encodes. They confirm the probe and
naming code against real files. Raw rips under ``samples/{bluray,dvd,
dvd-grainy,phone}`` drive the classifier; those folders are the labels.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dmc.classify import classify, classify_by_metadata, grain_score
from dmc.naming import parse_stem
from dmc.probe import probe
from dmc.profiles import SourceClass

pytestmark = [pytest.mark.samples, pytest.mark.tools]

LABELS = {"bluray": SourceClass.BLURAY, "dvd": SourceClass.DVD,
          "dvd-grainy": SourceClass.DVD_GRAINY, "phone": SourceClass.PHONE}


def _readable(p: Path) -> bool:
    """False while a file is still being copied in (Windows holds it locked)."""
    try:
        with p.open("rb"):
            return True
    except OSError:
        return False


def _files(folder: Path):
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.glob("*")
                  if p.suffix.lower() in {".mkv", ".mp4", ".mov", ".m2ts"} and _readable(p))


def test_expected_outputs_match_the_notes_profile(samples_dir, need_ffprobe):
    files = _files(samples_dir / "expected")
    if not files:
        pytest.skip("no samples/expected")
    for f in files:
        info = probe(f)
        assert info.video.codec == "hevc", f.name
        assert info.video.pix_fmt == "yuv420p10le", f.name
        assert [a.codec for a in info.audio][:1] == ["aac"], f.name
        assert info.audio[0].channels == 2, f.name


def test_expected_outputs_have_parseable_plex_names(samples_dir):
    files = _files(samples_dir / "expected")
    if not files:
        pytest.skip("no samples/expected")
    for f in files:
        n = parse_stem(f.stem)
        assert n.year and n.imdb_id, f.name


@pytest.mark.parametrize("folder", list(LABELS))
def test_raw_rips_classify_by_metadata_as_labelled(samples_dir, need_ffprobe, folder):
    files = _files(samples_dir / folder)
    if not files:
        pytest.skip(f"no samples/{folder}")
    expected = LABELS[folder]
    for f in files:
        got = classify_by_metadata(probe(f)).source
        if expected in {SourceClass.DVD, SourceClass.DVD_GRAINY}:
            assert got in {SourceClass.DVD, SourceClass.DVD_GRAINY}, f.name
        else:
            assert got is expected, f.name


@pytest.mark.parametrize("folder", ["dvd", "dvd-grainy"])
def test_grain_score_separates_dvd_from_grainy(samples_dir, need_ffprobe, folder):
    """Prints scores so the threshold can be calibrated; asserts only once both folders have files."""
    clean, grainy = _files(samples_dir / "dvd"), _files(samples_dir / "dvd-grainy")
    if not clean or not grainy:
        pytest.skip("need files in both samples/dvd and samples/dvd-grainy to calibrate")
    scores = {}
    for f in clean + grainy:
        info = probe(f)
        scores[f.name] = grain_score(f, info.duration_s, samples=3)
        print(f"{f.parent.name}/{f.name}: grain={scores[f.name]}")
    assert max(scores[f.name] for f in clean) < min(scores[f.name] for f in grainy), scores
