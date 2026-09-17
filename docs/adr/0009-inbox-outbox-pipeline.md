# ADR-0009: Unattended encoding as an inbox/outbox folder pipeline

- **Status:** Proposed
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

The full goal is disc in, MakeMKV rip, HandBrake encode, IMDb lookup for Plex naming, NAS upload, all without intervention. Stages finish at very different speeds (a rip is minutes, an encode is hours) and each can fail independently.

## Decision

Stages hand off through folders under one root:

```
<root>/inbox/    raw rips arrive here (from MakeMKV, or copied by hand)
<root>/outbox/   finished Plex-named MKVs
<root>/done/     originals after a successful encode
<root>/failed/   originals after a failed encode, with the log
<root>/logs/     one JSON-plus-text log per job
```

`dmc run <root> --watch` polls the inbox, waits until a file's size is stable, probes, classifies, encodes to a `.part.mkv` and renames on success. Later stages (IMDb rename, NAS copy) will watch the outbox the same way, so each stage can be run, restarted or replaced on its own.

## Consequences

**Good**

- Restart-safe: a crash leaves the source in the inbox and a `.part.mkv` that is overwritten.
- Each stage is testable with fake files; the pipeline tests run without HandBrake.

**Bad / accepted costs**

- Polling rather than filesystem events; 30-second latency is fine for hours-long encodes.
- Single encode at a time. Parallel encodes would fight for CPU anyway.

## Alternatives considered

- **A queue database:** more machinery than four folders justify at this scale.
- **HandBrake's own queue:** GUI-only and not scriptable per-file.

## Related

- ADR-0007, ADR-0008, `src/dmc/pipeline.py`
