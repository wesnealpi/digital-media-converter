"""Command line: ``dmc probe|classify|plan|encode|run``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .classify import classify
from .handbrake import build_command
from .pipeline import Folders, plan, run
from .probe import probe
from .profiles import PROFILES, SourceClass


def _add_plan_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--force", choices=[s.value for s in SourceClass if s is not SourceClass.UNKNOWN],
                   help="skip classification and use this profile")
    p.add_argument("--rf", type=float, help="override the profile's constant-quality value")
    p.add_argument("--great", action="store_true", help="use the profile's 'great quality' RF")
    p.add_argument("--no-grain", action="store_true", help="skip the grain measurement (metadata only)")


def _plan_kwargs(ns: argparse.Namespace) -> dict:
    return {
        "force": SourceClass(ns.force) if ns.force else None,
        "rf_override": ns.rf,
        "great": ns.great,
        "measure_grain": not ns.no_grain,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dmc", description="Classify and encode video for Plex.")
    ap.add_argument("--version", action="version", version=f"dmc {__version__}")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="show stream metadata"); p.add_argument("file", type=Path)
    p = sub.add_parser("classify", help="show the source class"); p.add_argument("file", type=Path)
    p.add_argument("--no-grain", action="store_true")
    p = sub.add_parser("plan", help="print the HandBrakeCLI command without running it")
    p.add_argument("file", type=Path); p.add_argument("--outbox", type=Path, default=Path("outbox")); _add_plan_args(p)
    p = sub.add_parser("encode", help="encode one file"); p.add_argument("file", type=Path)
    p.add_argument("--outbox", type=Path, default=Path("outbox")); _add_plan_args(p)
    p.add_argument("--clip", nargs=2, type=float, metavar=("START_S", "LENGTH_S"),
                   help="encode only this window, for quick quality trials")
    p = sub.add_parser("run", help="process an inbox folder"); p.add_argument("root", type=Path)
    p.add_argument("--watch", action="store_true", help="keep polling the inbox"); _add_plan_args(p)
    p = sub.add_parser("profiles", help="list encoding profiles")

    ns = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if ns.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    if ns.cmd == "profiles":
        for prof in PROFILES.values():
            dn = f"nlmeans {prof.denoise.preset}/{prof.denoise.tune}" if prof.denoise else "no denoise"
            print(f"{prof.name:<11} rf={prof.rf:<4g} great={prof.rf_great:<4g} range={prof.rf_range}  "
                  f"{dn}, {'decomb' if prof.deinterlace else 'no deinterlace'}")
        return 0

    if ns.cmd == "probe":
        info = probe(ns.file)
        v = info.video
        print(f"{info.path.name}: {info.container}, {info.duration_s/60:.1f} min, "
              f"{(info.bit_rate or 0)//1000} kb/s, {info.size_bytes/1e6:.0f} MB")
        print(f"  video: {v.codec} {v.profile} {v.width}x{v.height} {v.pix_fmt} {v.fps:.3f} fps field_order={v.field_order}")
        for a in info.audio:
            print(f"  audio: {a.codec} {a.channels}ch {a.language} {a.title}")
        for s in info.subtitles:
            print(f"  sub:   {s.codec} {s.language}{' forced' if s.forced else ''}")
        return 0

    if ns.cmd == "classify":
        cls = classify(probe(ns.file), measure_grain=not ns.no_grain)
        g = f" grain={cls.grain_score:.2f}" if cls.grain_score is not None else ""
        print(f"{ns.file.name}: {cls.source.value} (confidence {cls.confidence:.1f}){g}\n  {cls.reason}")
        return 0

    if ns.cmd in {"plan", "encode"}:
        info = probe(ns.file)
        job, profile = plan(info, ns.outbox, **_plan_kwargs(ns))
        print(job.to_json())
        clip = tuple(ns.clip) if getattr(ns, "clip", None) else None
        dst = job.dst
        if clip:
            dst = dst.with_name(f"{dst.stem} [clip {clip[0]:g}s+{clip[1]:g}s rf{profile.rf:g}]{dst.suffix}")
        cmd = build_command(job.src, dst, profile, clip=clip, subtitle_count=job.subtitle_count)
        print("\n" + " ".join(f'"{c}"' if " " in c else c for c in cmd))
        if ns.cmd == "encode":
            from .handbrake import encode
            ns.outbox.mkdir(parents=True, exist_ok=True)
            encode(job.src, dst, profile, clip=clip, subtitle_count=job.subtitle_count,
                   on_progress=lambda p: print(f"\r{p:5.1f}%", end="", flush=True))
            print(f"\nwrote {dst}")
        return 0

    if ns.cmd == "run":
        n = run(Folders(ns.root), watch=ns.watch, **_plan_kwargs(ns))
        print(f"{n} encoded")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
