# digital-media-converter

Prototype for converting high-bitrate personal video (DVD and Blu-ray rips, phone recordings) into much smaller files at perceptually equivalent quality, named for Plex. H.265 via HandBrakeCLI is the encoder (ADR-0003, ADR-0007). Target is 5x to 10x size reduction. End goal is disc in, MakeMKV rip, encode, IMDb lookup, NAS upload, unattended.

## Working rules

- **Windows, PowerShell 5.1.** Git, HandBrake, FFmpeg, and project scripts run from PowerShell, never from the GitHub Desktop app.
- **Git goes through the skills.** Use `git-account` to check or pin the account, `git-commit` to commit, `git-push` to push. Each verifies the repo is pinned to one GitHub account before touching the remote (ADR-0002). This repo is the personal account, `wesnealpi`.
- **Check-in cadence.** Build a feature, then wait. Never commit until Wes confirms. When Wes says "checkin" (or "check in"), that means commit **and** push in one go; no separate confirmation is needed for the push. Any other wording ("commit", "save") means commit only.
- **Decisions get an ADR.** Any codec, container, quality target, tooling, or layout choice is recorded in `docs/adr/` with the `adr` skill before or alongside the code that implements it. Read `docs/adr/README.md` first when picking up work.
- **Encoding numbers come from Wes's notes.** `docs/encoding-profiles.md` is the distilled table and `src/dmc/profiles.py` its executable form. Do not change an RF, filter, or encoder option in one without the other, and cite the notes or a new measurement.
- **Test-driven.** Write the failing test, then the code (ADR-0005). Unit tests need no media or tools. Integration tests under `tests/integration/` read from `samples/` and skip when it is empty or a tool is missing.
- **Samples never upload.** `samples/` is git-ignored except for its README. Never weaken that rule or add media elsewhere in the tree.
- **Docs are part of the deliverable.** Public behaviour gets a docstring; a new module gets a short section in `docs/`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q          # all tests (integration skips without samples)
.\.venv\Scripts\dmc.exe probe <file>             # stream metadata
.\.venv\Scripts\dmc.exe classify <file>          # source class + reason + grain score
.\.venv\Scripts\dmc.exe plan <file>              # decision + HandBrakeCLI command, no encode
.\.venv\Scripts\dmc.exe encode <file> --clip 600 60   # 60 s trial from 10:00
.\.venv\Scripts\dmc.exe run <root> --watch       # unattended inbox/outbox pipeline
```

First-time setup: `python -m venv .venv; .\.venv\Scripts\pip install -e ".[dev]"`. New shells may need PATH refreshed for winget-installed tools.

## Layout

```
.claude/skills/   project skills: git-account, git-commit, git-push, adr
docs/adr/         Architecture Decision Records (index in README.md)
docs/             encoding-profiles.md, Wes's Movie Encoding 2021.pdf
src/dmc/          probe, classify, profiles, handbrake, naming, pipeline, cli
tests/            unit tests; tests/integration/ needs samples
samples/          local-only media: bluray/, dvd/, dvd-grainy/, phone/ (raw rips, folder = label), expected/ (Wes's approved encodes)
```

## Tooling on this machine (checked 2026-09-17)

- HandBrakeCLI 1.11.2 and FFmpeg 9.0.1 (with libx265) installed via winget; HandBrake GUI 1.11.2 also present.
- MakeMKV 1.18.4 installed and registered with the beta key from forum.makemkv.com (thread t=1053); the key expires and must be refreshed from that thread.
- No optical drive was visible when checked; the disc-ripping stage cannot be tested until one is attached.
- `gh` CLI is not installed; pull requests are opened in the browser.
- GPU is AMD Radeon 890M; hardware HEVC encode exists but the notes chose software x265 for quality.

## Open items

- Calibrate the grain threshold once `samples/dvd` and `samples/dvd-grainy` have files (ADR-0008).
- TV episode naming (`Show (Year) - s01e05 - Title.mkv`) is not implemented; `naming.py` is movies only.
- IMDb lookup and NAS upload stages are not started.
