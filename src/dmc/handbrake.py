"""Build and run HandBrakeCLI commands from a :class:`Profile`.

``build_command`` is pure and fully unit-tested. ``encode`` runs it and
streams progress to a callback. Flag names follow HandBrake 1.9+ CLI help.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from .profiles import Profile


class HandBrakeError(RuntimeError):
    pass


def handbrake_path() -> str:
    exe = shutil.which("HandBrakeCLI")
    if not exe:
        raise HandBrakeError("HandBrakeCLI not found on PATH; install with: winget install HandBrake.HandBrake.CLI")
    return exe


def build_command(src: Path | str, dst: Path | str, profile: Profile, *, exe: str = "HandBrakeCLI",
                  title: int | None = None, clip: tuple[float, float] | None = None,
                  subtitle_count: int = 0) -> list[str]:
    """Return the HandBrakeCLI argv for encoding ``src`` to ``dst`` with ``profile``.

    Settings mirror the HandBrake GUI choices in Wes's notes:
    MKV, x265 10-bit, medium, fastdecode, the ref/bframes/lookahead encopts,
    constant quality, variable frame rate matching the source, one English
    stereo AAC track at 160 kb/s, all subtitles kept, foreign-audio scan
    with forced subtitles burned in.

    ``clip=(start_s, duration_s)`` encodes only that window; used for quick
    quality trials the way the notes compared 10-second clips.

    ``subtitle_count`` is the number of subtitle tracks in the source (from
    ffprobe). Every track is listed explicitly after ``scan`` because
    ``--all-subtitles`` keeps the tracks but makes HandBrake skip the foreign
    audio search (verified on a Blu-ray rip, 2026-09-17).
    """
    cmd = [exe, "-i", str(src), "-o", str(dst)]
    if title is not None:
        cmd += ["-t", str(title)]
    if clip is not None:
        start, length = clip
        cmd += ["--start-at", f"seconds:{start:g}", "--stop-at", f"seconds:{length:g}"]

    cmd += [
        "-f", profile.container,
        "-e", profile.encoder,
        "--encoder-preset", profile.encoder_preset,
        "--encoder-tune", profile.encoder_tune,
        "-x", profile.encopts,
        "-q", f"{profile.rf:g}",
        "--vfr",
    ]

    # Audio: first English track only, downmixed to stereo AAC. No passthrough.
    cmd += [
        "--audio-lang-list", profile.audio_lang,
        "--first-audio",
        "-E", profile.audio_encoder,
        "-B", str(profile.audio_bitrate),
        "--mixdown", profile.audio_mixdown,
        "--native-language", profile.audio_lang,
    ]

    # Subtitles: keep every track; add a foreign-audio scan track that burns in
    # forced-only subtitles (the HandBrake GUI "Foreign Audio Scan" row).
    tracks = [str(i) for i in range(1, subtitle_count + 1)] if profile.all_subtitles else []
    if profile.foreign_audio_scan_burn:
        # "scan" is output track 1; --subtitle-forced/--subtitle-burned index output tracks.
        cmd += ["-s", ",".join(["scan", *tracks]), "--subtitle-forced=1", "--subtitle-burned=1"]
    elif tracks:
        cmd += ["-s", ",".join(tracks)]
    else:
        cmd += ["-s", "none"]

    # Filters
    if profile.deinterlace:
        cmd += ["--comb-detect", "--decomb"]
    if profile.denoise is not None:
        cmd += [f"--nlmeans={profile.denoise.preset}", "--nlmeans-tune", profile.denoise.tune]

    return cmd


_PROGRESS_RE = re.compile(r"Encoding: task \d+ of \d+, (\d+(?:\.\d+)?) %")


def parse_progress(line: str) -> float | None:
    m = _PROGRESS_RE.search(line)
    return float(m.group(1)) if m else None


def encode(src: Path | str, dst: Path | str, profile: Profile, *,
           on_progress: Callable[[float], None] | None = None,
           title: int | None = None, clip: tuple[float, float] | None = None,
           subtitle_count: int = 0) -> Path:
    """Encode ``src`` to ``dst``. Returns ``dst``. Raises on failure."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_command(src, dst, profile, exe=handbrake_path(), title=title, clip=clip,
                        subtitle_count=subtitle_count)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)
    tail: list[str] = []
    assert proc.stdout is not None
    for raw in proc.stdout:
        for line in raw.replace("\r", "\n").split("\n"):
            line = line.strip()
            if not line:
                continue
            tail.append(line)
            tail = tail[-40:]
            pct = parse_progress(line)
            if pct is not None and on_progress:
                on_progress(pct)
    proc.wait()
    if proc.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
        raise HandBrakeError(f"HandBrakeCLI failed (exit {proc.returncode}) on {Path(src).name}:\n" + "\n".join(tail))
    return dst
