"""Decide which source class a file belongs to.

Two layers:

1. ``classify_by_metadata`` uses only what ffprobe reports (resolution, codec,
   container, field order, bit rate). It separates Blu-ray, DVD and phone
   video reliably and is pure, so it is unit-tested without media.
2. ``grain_score`` measures high-frequency noise in a few sampled frames with
   FFmpeg. It splits DVD into clean vs grainy. The threshold is a guess until
   calibrated against Wes's labelled rips (ADR-0008), so the score is always
   reported alongside the decision.
"""

from __future__ import annotations

import re
import shutil
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .probe import MediaInfo
from .profiles import SourceClass

# Standard-definition disc geometry. DVD video is 720 (or 704/352) wide,
# 480 tall for NTSC, 576 for PAL. Anything meaningfully larger is HD.
_SD_MAX_WIDTH = 720
_SD_HEIGHTS = {480, 576}
_HD_MIN_WIDTH = 1280

# Above this a DVD-resolution source was probably encoded well; below it the
# MPEG-2 encode itself is likely to show blocking. Bits per second.
_DVD_LOW_BITRATE = 3_500_000

# grain_score is the mean luma difference between each frame and a blurred copy
# (0..255). Clean DVDs sit low, film grain and MPEG-2 noise push it up. To be
# calibrated; see docs/encoding-profiles.md.
GRAIN_THRESHOLD = 6.0

_PHONE_CONTAINERS = {"mov", "mp4"}
_PHONE_CODECS = {"h264", "hevc"}


@dataclass(frozen=True)
class Classification:
    source: SourceClass
    reason: str
    grain_score: float | None = None
    confidence: float = 1.0


def classify_by_metadata(info: MediaInfo) -> Classification:
    """Assign a source class from container and stream metadata alone."""
    v = info.video
    w, h = v.width, v.height

    if w >= _HD_MIN_WIDTH:
        looks_like_phone = (
            info.container in _PHONE_CONTAINERS
            and v.codec in _PHONE_CODECS
            and (v.rotation != 0 or v.fps >= 29 or info.tags.get("com.apple.quicktime.make") or
                 "android" in " ".join(info.tags.values()).lower())
        )
        if looks_like_phone:
            return Classification(SourceClass.PHONE, f"{w}x{h} {v.codec} in {info.container} with phone markers")
        if info.container in _PHONE_CONTAINERS and v.codec in _PHONE_CODECS:
            return Classification(SourceClass.PHONE, f"{w}x{h} {v.codec} in {info.container}", confidence=0.7)
        return Classification(SourceClass.BLURAY, f"{w}x{h} {v.codec}, HD disc geometry")

    if w <= _SD_MAX_WIDTH and h in _SD_HEIGHTS or v.codec == "mpeg2video":
        if info.bit_rate is not None and info.bit_rate < _DVD_LOW_BITRATE:
            return Classification(
                SourceClass.DVD_GRAINY,
                f"{w}x{h} {v.codec} at {info.bit_rate // 1000} kb/s, low-bitrate SD",
                confidence=0.6,
            )
        return Classification(SourceClass.DVD, f"{w}x{h} {v.codec}, SD disc geometry", confidence=0.8)

    if w > _SD_MAX_WIDTH and w < _HD_MIN_WIDTH:
        return Classification(SourceClass.BLURAY, f"{w}x{h} {v.codec}, between SD and HD; treating as HD", confidence=0.5)

    return Classification(SourceClass.UNKNOWN, f"{w}x{h} {v.codec} in {info.container} matched no rule", confidence=0.0)


_YAVG_RE = re.compile(r"lavfi\.signalstats\.YAVG=([0-9.]+)")


def _ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def parse_yavg(text: str) -> list[float]:
    """Pull every YAVG value out of ffmpeg ``metadata=print`` output."""
    return [float(m) for m in _YAVG_RE.findall(text)]


def grain_score(path: Path | str, duration_s: float, samples: int = 5, seconds: float = 1.0) -> float | None:
    """Mean high-frequency luma energy over ``samples`` short windows.

    Each window is blurred and subtracted from itself; the average difference
    is what NLMeans would remove. Returns ``None`` when ffmpeg is missing or
    the measurement fails, so callers can fall back to metadata only.
    """
    exe = _ffmpeg_path()
    if not exe or duration_s <= 0:
        return None
    filt = (
        "split[a][b];[a]gblur=sigma=1.5[bl];[b][bl]blend=all_mode=difference,"
        "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-"
    )
    means: list[float] = []
    for i in range(samples):
        start = duration_s * (i + 1) / (samples + 1)
        cmd = [exe, "-v", "error", "-ss", f"{start:.2f}", "-t", f"{seconds}", "-i", str(path),
               "-vf", filt, "-an", "-sn", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        values = parse_yavg(result.stdout) + parse_yavg(result.stderr)
        if values:
            means.append(statistics.fmean(values))
    if not means:
        return None
    return statistics.fmean(means)


def refine_with_grain(base: Classification, score: float | None, threshold: float = GRAIN_THRESHOLD) -> Classification:
    """Split DVD into clean vs grainy using a measured grain score."""
    if score is None or base.source not in {SourceClass.DVD, SourceClass.DVD_GRAINY}:
        return Classification(base.source, base.reason, score, base.confidence)
    if score >= threshold:
        return Classification(SourceClass.DVD_GRAINY, f"{base.reason}; grain {score:.1f} >= {threshold}", score, 0.8)
    return Classification(SourceClass.DVD, f"{base.reason}; grain {score:.1f} < {threshold}", score, 0.8)


def classify(info: MediaInfo, measure_grain: bool = True) -> Classification:
    """Full classification: metadata first, then grain measurement for SD sources."""
    base = classify_by_metadata(info)
    if not measure_grain or base.source not in {SourceClass.DVD, SourceClass.DVD_GRAINY}:
        return base
    return refine_with_grain(base, grain_score(info.path, info.duration_s))
