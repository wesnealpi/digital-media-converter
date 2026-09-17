# ADR-0003: Use H.265 (HEVC) as the default output codec

- **Status:** Accepted
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

Sources are personal DVD and Blu-ray rips (MPEG-2 / H.264 or VC-1, high bitrate) and phone recordings (H.264 or HEVC at very high bitrate, low compression). Targets:

| Goal | Value |
|------|-------|
| Size reduction | 5x to 10x smaller than the source |
| Quality | Perceptually equivalent; a difference may be detectable side by side but nothing looks degraded |
| Efficiency | Best quality per bit for the encode time spent |

## Decision

H.265 / HEVC is the default output video codec, encoded with `libx265` through FFmpeg, in an MP4 or MKV container. Rate control uses a constant quality target (CRF) rather than a fixed bitrate, with the CRF value, preset, and tune chosen per source type by experiment against `samples/` and recorded in later ADRs. Audio handling is a separate decision.

## Consequences

**Good**

- Roughly 40 to 50 percent smaller than H.264 at the same perceived quality, which is what makes the 5x to 10x target reachable on high-bitrate sources.
- Broad playback support on current TVs, phones, and desktop players.
- CRF gives consistent quality across scenes instead of consistent size.

**Bad / accepted costs**

- Slower to encode than H.264; long Blu-ray encodes are expected.
- Older devices and some browsers do not play HEVC. Not a concern for a personal archive.
- Licensing means some distros ship FFmpeg without `libx265`; the Windows builds used here include it.

## Alternatives considered

- **H.264 (`libx264`):** fastest and most compatible, but cannot hit the size target without visible loss.
- **AV1 (`libsvtav1` / `libaom`):** better compression than HEVC, but much slower on CPU, fewer playback devices in the collection support it, and tooling is less settled. Worth revisiting as a later ADR once the pipeline exists.
- **VP9:** similar efficiency to HEVC with weaker hardware decode support on TVs.

## Related

- ADR-0004 (samples used to tune settings)
- Wes's personal conversion notes, to be added under `docs/` when provided.
