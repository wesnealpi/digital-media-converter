"""Shared fixtures: ffprobe-shaped dicts for each source class.

These are hand-trimmed from real ffprobe output so unit tests run with no
media. The ``samples_dir`` fixture points at real files and skips when empty.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from dmc.probe import parse_ffprobe

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"


def _video(codec, w, h, fps, field_order="progressive", pix_fmt="yuv420p", profile="", extra=None):
    d = {"index": 0, "codec_type": "video", "codec_name": codec, "profile": profile,
         "width": w, "height": h, "field_order": field_order,
         "r_frame_rate": fps, "avg_frame_rate": fps, "pix_fmt": pix_fmt, "disposition": {}}
    if extra:
        d.update(extra)
    return d


def _audio(codec, ch, lang="eng", title="", bit_rate=None, idx=1):
    d = {"index": idx, "codec_type": "audio", "codec_name": codec, "channels": ch,
         "tags": {"language": lang, "title": title}, "disposition": {}}
    if bit_rate:
        d["bit_rate"] = str(bit_rate)
    return d


def _sub(codec, lang, idx, forced=0):
    return {"index": idx, "codec_type": "subtitle", "codec_name": codec,
            "tags": {"language": lang}, "disposition": {"forced": forced}}


def _fmt(name, fmt, dur, size, bit_rate, tags=None):
    return {"filename": name, "format_name": fmt, "duration": str(dur), "size": str(size),
            "bit_rate": str(bit_rate), "tags": tags or {}}


@pytest.fixture
def bluray_rip_json():
    """Raw MakeMKV Blu-ray rip: 1080p H.264, DTS-HD + AC3, PGS subs."""
    return {
        "format": _fmt("Top Gun Maverick_t00.mkv", "matroska,webm", 7814.5, 28_500_000_000, 29_180_000),
        "streams": [
            _video("h264", 1920, 1080, "24000/1001", profile="High"),
            _audio("dts", 8, title="Surround 7.1", idx=1),
            _audio("ac3", 6, bit_rate=640000, idx=2),
            _sub("hdmv_pgs_subtitle", "eng", 3),
            _sub("hdmv_pgs_subtitle", "eng", 4, forced=1),
        ],
    }


@pytest.fixture
def dvd_rip_json():
    """Raw MakeMKV DVD rip: 720x480 MPEG-2, interlaced flags, AC3 5.1, VOB subs."""
    return {
        "format": _fmt("Vegas Vacation_t00.mkv", "matroska,webm", 5671.9, 4_900_000_000, 6_910_000),
        "streams": [
            _video("mpeg2video", 720, 480, "30000/1001", field_order="tt", profile="Main"),
            _audio("ac3", 6, title="Surround 5.1", bit_rate=448000, idx=1),
            _audio("ac3", 2, lang="fre", idx=2),
            _sub("dvd_subtitle", "eng", 3),
            _sub("dvd_subtitle", "spa", 4),
        ],
    }


@pytest.fixture
def old_dvd_rip_json():
    """Low-bitrate early-2000s DVD: same geometry, far fewer bits."""
    return {
        "format": _fmt("Total Recall_t00.mkv", "matroska,webm", 6800.1, 2_600_000_000, 3_050_000),
        "streams": [
            _video("mpeg2video", 720, 480, "30000/1001", field_order="tt", profile="Main"),
            _audio("ac3", 2, idx=1),
        ],
    }


@pytest.fixture
def phone_json():
    """iPhone 4K60 HEVC .mov with rotation side data."""
    return {
        "format": _fmt("IMG_4021.MOV", "mov,mp4,m4a,3gp,3g2,mj2", 93.4, 1_020_000_000, 87_300_000,
                       tags={"com.apple.quicktime.make": "Apple", "com.apple.quicktime.model": "iPhone 15 Pro"}),
        "streams": [
            _video("hevc", 3840, 2160, "60000/1001", pix_fmt="yuv420p10le", profile="Main 10",
                   extra={"side_data_list": [{"side_data_type": "Display Matrix", "rotation": -90}]}),
            _audio("aac", 2, lang="und", idx=1),
        ],
    }


@pytest.fixture
def encoded_output_json():
    """One of Wes's finished encodes (samples/expected): HEVC 10-bit, AAC stereo."""
    return {
        "format": _fmt("Vegas Vacation (1997) {imdb-tt0120434}.mkv", "matroska,webm", 5671.887, 839527253, 1184124),
        "streams": [
            _video("hevc", 720, 480, "24000/1001", field_order="unknown", pix_fmt="yuv420p10le", profile="Main 10"),
            _audio("aac", 2, title="Surround 5.1", idx=1),
            _sub("dvd_subtitle", "eng", 2), _sub("ass", "eng", 3),
            _sub("dvd_subtitle", "fre", 4), _sub("dvd_subtitle", "spa", 5),
        ],
    }


@pytest.fixture
def bluray_rip(bluray_rip_json): return parse_ffprobe(bluray_rip_json, "Top Gun Maverick_t00.mkv")
@pytest.fixture
def dvd_rip(dvd_rip_json): return parse_ffprobe(dvd_rip_json, "Vegas Vacation_t00.mkv")
@pytest.fixture
def old_dvd_rip(old_dvd_rip_json): return parse_ffprobe(old_dvd_rip_json, "Total Recall_t00.mkv")
@pytest.fixture
def phone(phone_json): return parse_ffprobe(phone_json, "IMG_4021.MOV")
@pytest.fixture
def encoded_output(encoded_output_json): return parse_ffprobe(encoded_output_json, "Vegas Vacation (1997) {imdb-tt0120434}.mkv")


def _media_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in {".mkv", ".mp4", ".mov", ".m2ts"})


@pytest.fixture
def samples_dir() -> Path:
    if not _media_files(SAMPLES / "expected") and not any(_media_files(SAMPLES / d) for d in ("bluray", "dvd", "dvd-grainy", "phone")):
        pytest.skip("no media under samples/")
    return SAMPLES


@pytest.fixture
def need_ffprobe():
    if not shutil.which("ffprobe"):
        pytest.skip("ffprobe not on PATH")


@pytest.fixture
def need_handbrake():
    if not shutil.which("HandBrakeCLI"):
        pytest.skip("HandBrakeCLI not on PATH")
