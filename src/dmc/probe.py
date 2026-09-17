"""Read stream metadata with ffprobe.

``probe(path)`` shells out to ffprobe and returns a :class:`MediaInfo`.
``parse_ffprobe(data)`` turns ffprobe's JSON into the same structure and is
pure, so tests can feed it captured JSON without any media present.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path


class ProbeError(RuntimeError):
    """ffprobe is missing, failed, or returned something unusable."""


@dataclass(frozen=True)
class VideoStream:
    codec: str
    width: int
    height: int
    field_order: str  # "progressive", "tt", "bb", "tb", "bt", or "unknown"
    frame_rate: Fraction
    pix_fmt: str
    profile: str = ""
    rotation: int = 0

    @property
    def interlaced_flag(self) -> bool:
        """True when the container says the stream is interlaced.

        DVD MPEG-2 often reports fields even for telecined film, so treat this
        as a hint; HandBrake's comb detector makes the frame-level call.
        """
        return self.field_order in {"tt", "bb", "tb", "bt"}

    @property
    def fps(self) -> float:
        return float(self.frame_rate)


@dataclass(frozen=True)
class AudioStream:
    codec: str
    channels: int
    language: str = "und"
    title: str = ""
    bit_rate: int | None = None


@dataclass(frozen=True)
class SubtitleStream:
    codec: str
    language: str = "und"
    forced: bool = False


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    container: str
    duration_s: float
    bit_rate: int | None
    size_bytes: int
    video: VideoStream
    audio: tuple[AudioStream, ...] = field(default_factory=tuple)
    subtitles: tuple[SubtitleStream, ...] = field(default_factory=tuple)
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def video_bit_rate_estimate(self) -> int | None:
        """Overall bit rate when the video stream does not report its own."""
        return self.bit_rate


def _frac(text: str | None) -> Fraction:
    if not text or text in {"0/0", "N/A"}:
        return Fraction(0)
    num, _, den = text.partition("/")
    den = den or "1"
    if int(den) == 0:
        return Fraction(0)
    return Fraction(int(num), int(den))


def _int_or_none(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rotation(stream: dict) -> int:
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            return int(sd["rotation"]) % 360
    tags = stream.get("tags", {}) or {}
    if "rotate" in tags:
        return int(tags["rotate"]) % 360
    return 0


def parse_ffprobe(data: dict, path: Path | str = "") -> MediaInfo:
    """Build a :class:`MediaInfo` from ffprobe ``-print_format json`` output."""
    fmt = data.get("format", {}) or {}
    streams = data.get("streams", []) or []

    videos = [s for s in streams if s.get("codec_type") == "video"
              and s.get("disposition", {}).get("attached_pic", 0) != 1]
    if not videos:
        raise ProbeError(f"no video stream in {path or 'input'}")
    v = videos[0]
    video = VideoStream(
        codec=v.get("codec_name", ""),
        width=int(v.get("width", 0) or 0),
        height=int(v.get("height", 0) or 0),
        field_order=v.get("field_order", "unknown") or "unknown",
        frame_rate=_frac(v.get("avg_frame_rate")) or _frac(v.get("r_frame_rate")),
        pix_fmt=v.get("pix_fmt", "") or "",
        profile=v.get("profile", "") or "",
        rotation=_rotation(v),
    )

    audio = tuple(
        AudioStream(
            codec=s.get("codec_name", ""),
            channels=int(s.get("channels", 0) or 0),
            language=(s.get("tags", {}) or {}).get("language", "und"),
            title=(s.get("tags", {}) or {}).get("title", ""),
            bit_rate=_int_or_none(s.get("bit_rate")),
        )
        for s in streams if s.get("codec_type") == "audio"
    )
    subtitles = tuple(
        SubtitleStream(
            codec=s.get("codec_name", ""),
            language=(s.get("tags", {}) or {}).get("language", "und"),
            forced=bool((s.get("disposition", {}) or {}).get("forced", 0)),
        )
        for s in streams if s.get("codec_type") == "subtitle"
    )

    return MediaInfo(
        path=Path(path) if path else Path(fmt.get("filename", "")),
        container=(fmt.get("format_name", "") or "").split(",")[0],
        duration_s=float(fmt.get("duration", 0) or 0),
        bit_rate=_int_or_none(fmt.get("bit_rate")),
        size_bytes=int(fmt.get("size", 0) or 0),
        video=video,
        audio=audio,
        subtitles=subtitles,
        tags={k.lower(): v for k, v in (fmt.get("tags", {}) or {}).items()},
    )


def ffprobe_path() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise ProbeError("ffprobe not found on PATH; install FFmpeg (winget install Gyan.FFmpeg)")
    return exe


def probe(path: Path | str) -> MediaInfo:
    """Run ffprobe on ``path`` and return its :class:`MediaInfo`."""
    path = Path(path)
    if not path.is_file():
        raise ProbeError(f"not a file: {path}")
    cmd = [
        ffprobe_path(), "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise ProbeError(f"ffprobe failed on {path.name}: {result.stderr.strip()}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"ffprobe returned invalid JSON for {path.name}") from exc
    return parse_ffprobe(data, path)
