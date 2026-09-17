# ADR-0008: Classify sources by metadata first, then a measured grain score

- **Status:** Proposed
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

Unattended encoding needs to pick a profile without a human looking at the file. Blu-ray, DVD and phone video differ in resolution, codec and container and can be told apart from ffprobe output alone. Clean DVD versus grainy or poorly encoded DVD cannot; it is a property of the picture.

## Decision

1. `classify_by_metadata` decides Blu-ray / DVD / phone from width, height, codec, container, frame rate, rotation and device tags. SD sources with an overall bit rate under 3.5 Mb/s lean grainy.
2. For SD sources only, `grain_score` samples five one-second windows, subtracts a Gaussian-blurred copy from each frame, and averages the luma difference with FFmpeg's `signalstats`. Scores at or above a threshold (initially 6.0) mean `dvd_grainy`.
3. Every decision carries a reason string, a confidence, and the score, and is written to the job log so a wrong call can be traced and overridden with `--force`.

The threshold is unvalidated. It gets calibrated with labelled rips in `samples/dvd` and `samples/dvd-grainy`; the integration test prints the scores and asserts separation once both folders have files.

## Consequences

**Good**

- No manual step for the common cases.
- The measurement is cheap (a few seconds per file) compared with an encode.

**Bad / accepted costs**

- A wrong grain call costs an encode at the wrong RF; the log makes it visible but not automatic to fix.
- Animation and VHS captures have no class yet; they will need their own rules once samples exist.

## Alternatives considered

- **Folder-based labelling only:** works but is exactly the manual step Wes wants to remove.
- **Encode-year or title lookup:** age correlates with grain but not reliably; remasters exist.
- **VMAF against a reference:** there is no reference for a raw rip.

## Related

- ADR-0007, `src/dmc/classify.py`, `tests/integration/test_samples.py`
