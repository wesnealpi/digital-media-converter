# digital-media-converter

A project for taking high-res, low-compression original videos from DVD, Blu-ray, and phone to high-compression, high-quality output. The goal is files 5x to 10x smaller that look the same to a viewer. H.265 (HEVC) via FFmpeg is the default codec.

## Status

Prototype. Design decisions are being recorded before code; see [docs/adr/](docs/adr/README.md).

## Layout

| Path | Purpose |
|------|---------|
| `src/dmc/` | The pipeline: probe, classify, profiles, HandBrake command builder, naming, inbox runner |
| `tests/` | Unit tests (no media needed) and `integration/` tests that use `samples/` |
| `docs/adr/` | Architecture Decision Records: what was decided and why |
| `docs/encoding-profiles.md` | The RF, filter and audio settings per source, distilled from the 2021 notes |
| `samples/` | Local-only sample media. Git-ignored; nothing here uploads |
| `.claude/skills/` | Claude Code skills for this repo (git account pinning, commit, push, ADRs) |
| `CLAUDE.md` | Working rules for Claude Code in this repo |

## Working on it

- Windows with PowerShell 5.1. Git runs from the command line, not GitHub Desktop.
- Each clone is pinned to one GitHub account; see ADR-0002 and `.claude/skills/git-account/`.
- Put source videos under `samples/dvd`, `samples/bluray`, or `samples/phone`. They stay on your machine.
- Tests come first (ADR-0005). Integration tests skip when `samples/` is empty or FFmpeg is missing.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\dmc.exe plan "samples\bluray\Some Movie_t00.mkv"
```

## Requirements

- Python 3.13+
- HandBrakeCLI (`winget install HandBrake.HandBrake.CLI`)
- FFmpeg with ffprobe (`winget install Gyan.FFmpeg`)
- MakeMKV for the ripping stage, registered with the current beta key from the MakeMKV forum
- Git 2.x with Git Credential Manager
