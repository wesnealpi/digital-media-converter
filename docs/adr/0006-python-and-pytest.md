# ADR-0006: Implement the pipeline in Python with pytest

- **Status:** Accepted
- **Date:** 2026-09-17
- **Deciders:** Wes Watson (language left to Claude)

## Context

The pipeline is glue around command-line tools: makemkvcon, HandBrakeCLI, ffprobe, ffmpeg, later an IMDb lookup and a NAS copy. It needs subprocess handling, JSON parsing, a small CLI, and a test runner that makes test-first development cheap (ADR-0005). Python 3.14 and 3.13 are already installed on the development machine.

## Decision

Python 3.13+ with the standard library only at runtime, pytest for tests, a `src/dmc` package with a `dmc` console script, and a project-local `.venv`. Each pipeline stage is a module whose decision logic is a pure function (`parse_ffprobe`, `classify_by_metadata`, `build_command`, `plan`) and whose side effects are thin wrappers that tests replace.

## Consequences

**Good**

- Unit tests run in under a second with no media or tools present.
- ffprobe JSON maps directly onto dataclasses.
- Easy to add the IMDb and NAS stages later without new tooling.

**Bad / accepted costs**

- A virtual environment must be created on each machine (`python -m venv .venv`, `pip install -e .[dev]`).
- Python is a second language next to the PowerShell git tooling.

## Alternatives considered

- **PowerShell:** already used for git skills, but Pester-driven test-first work is clumsier and JSON handling is weaker.
- **Shell scripts calling HandBrake presets:** no tests, no classification logic.

## Related

- ADR-0005, `pyproject.toml`, `tests/`
