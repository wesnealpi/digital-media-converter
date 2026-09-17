"""Unattended batch: inbox -> classify -> encode -> outbox.

Layout the runner expects (all paths configurable):

    <root>/inbox/     raw MakeMKV rips waiting to be encoded
    <root>/outbox/    finished Plex-named MKVs
    <root>/done/      originals moved here after a successful encode
    <root>/failed/    originals moved here when the encode failed
    <root>/logs/      one .log per job

``plan`` is pure and testable; ``run`` performs the work.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from . import classify as _classify
from .handbrake import encode, HandBrakeError
from .naming import parse_stem
from .probe import probe, MediaInfo, ProbeError
from .profiles import Profile, SourceClass, profile_for

SOURCE_EXTS = {".mkv", ".mp4", ".mov", ".m2ts", ".ts", ".vob", ".mpg", ".avi", ".m4v"}
log = logging.getLogger("dmc")


@dataclass(frozen=True)
class Job:
    src: Path
    dst: Path
    source: SourceClass
    profile_name: str
    rf: float
    reason: str
    grain_score: float | None
    subtitle_count: int = 0

    def to_json(self) -> str:
        d = asdict(self)
        d["src"], d["dst"] = str(self.src), str(self.dst)
        return json.dumps(d, indent=2)


@dataclass(frozen=True)
class Folders:
    root: Path

    @property
    def inbox(self) -> Path: return self.root / "inbox"
    @property
    def outbox(self) -> Path: return self.root / "outbox"
    @property
    def done(self) -> Path: return self.root / "done"
    @property
    def failed(self) -> Path: return self.root / "failed"
    @property
    def logs(self) -> Path: return self.root / "logs"

    def ensure(self) -> "Folders":
        for p in (self.inbox, self.outbox, self.done, self.failed, self.logs):
            p.mkdir(parents=True, exist_ok=True)
        return self


def pending_sources(inbox: Path) -> list[Path]:
    """Files in the inbox that look like video and are not still being written."""
    out = []
    for p in sorted(inbox.iterdir()):
        if p.is_file() and p.suffix.lower() in SOURCE_EXTS and not p.name.startswith("~"):
            out.append(p)
    return out


def is_stable(path: Path, wait_s: float = 2.0) -> bool:
    """True when the file size does not change over ``wait_s`` (copy finished)."""
    a = path.stat().st_size
    time.sleep(wait_s)
    return a == path.stat().st_size


def plan(info: MediaInfo, outbox: Path, *, force: SourceClass | None = None,
         rf_override: float | None = None, great: bool = False,
         measure_grain: bool = True) -> tuple[Job, Profile]:
    """Decide the profile and output name for one probed file."""
    if force is not None:
        cls = _classify.Classification(force, "forced by caller")
    else:
        cls = _classify.classify(info, measure_grain=measure_grain)
    if cls.source is SourceClass.UNKNOWN:
        raise ValueError(f"cannot classify {info.path.name}: {cls.reason}")
    profile = profile_for(cls.source)
    if great:
        profile = profile.great
    if rf_override is not None:
        profile = profile.with_rf(rf_override)
    name = parse_stem(info.path.stem)
    dst = outbox / name.filename(".mkv")
    job = Job(info.path, dst, cls.source, profile.name, profile.rf, cls.reason, cls.grain_score,
              subtitle_count=len(info.subtitles))
    return job, profile


def run_one(src: Path, folders: Folders, **plan_kwargs) -> Job:
    """Probe, plan, encode and file one source. Returns the job that ran."""
    src_size = src.stat().st_size
    info = probe(src)
    job, profile = plan(info, folders.outbox, **plan_kwargs)
    log_path = folders.logs / (src.stem + ".log")
    log_path.write_text(job.to_json() + "\n", encoding="utf-8")
    log.info("%s -> %s [%s rf=%g] %s", src.name, job.dst.name, job.profile_name, job.rf, job.reason)

    tmp = job.dst.with_suffix(".part.mkv")
    last = {"pct": -5.0}

    def progress(pct: float) -> None:
        if pct - last["pct"] >= 5:
            last["pct"] = pct
            log.info("  %s %5.1f%%", src.name, pct)

    try:
        encode(src, tmp, profile, on_progress=progress, subtitle_count=job.subtitle_count)
    except HandBrakeError as exc:
        log.error("FAILED %s: %s", src.name, exc)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(str(exc) + "\n")
        if tmp.exists():
            tmp.unlink()
        shutil.move(str(src), folders.failed / src.name)
        raise
    tmp.replace(job.dst)
    shutil.move(str(src), folders.done / src.name)
    out_size = job.dst.stat().st_size
    ratio = src_size / out_size if out_size else 0
    log.info("DONE %s: %.0f MB -> %.0f MB (%.1fx)", job.dst.name, src_size / 1e6, out_size / 1e6, ratio)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"result: {src_size} -> {out_size} bytes, {ratio:.2f}x\n")
    return job


def run(folders: Folders, *, watch: bool = False, poll_s: float = 30.0, **plan_kwargs) -> int:
    """Process everything in the inbox. With ``watch`` keep polling forever.

    Returns the number of successful encodes (until interrupted when watching).
    """
    folders.ensure()
    ok = 0
    while True:
        for src in pending_sources(folders.inbox):
            if not is_stable(src):
                log.info("skipping %s, still being written", src.name)
                continue
            try:
                run_one(src, folders, **plan_kwargs)
                ok += 1
            except (HandBrakeError, ProbeError, ValueError) as exc:
                log.error("%s: %s", src.name, exc)
                if src.exists():
                    shutil.move(str(src), folders.failed / src.name)
        if not watch:
            return ok
        time.sleep(poll_s)
