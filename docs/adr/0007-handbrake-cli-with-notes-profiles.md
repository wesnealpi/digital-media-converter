# ADR-0007: Encode with HandBrakeCLI using the profiles from the 2021 notes

- **Status:** Accepted
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

ADR-0003 picked H.265. Wes has fourteen months of HandBrake GUI experiments (`docs/Movie Encoding 2021.pdf`) that settled on x265 10-bit, medium, fastdecode, a specific encopts string, AAC stereo, and per-source RF values. Those results were judged by eye against a Plex setup and should not be re-derived. FFmpeg's libx265 could reproduce the video settings, but HandBrake also carries the comb detector, NLMeans, foreign-audio scan and subtitle handling the notes depend on.

## Decision

HandBrakeCLI (installed via winget) is the encoder. `src/dmc/profiles.py` holds one profile per source class with the exact values from the notes, and `src/dmc/handbrake.py` maps a profile to CLI flags. The full table is in `docs/encoding-profiles.md`. Changing a value requires updating that document and, for a change of approach, a new ADR.

| Profile | RF | Denoise | Deinterlace |
|---------|----|---------|-------------|
| bluray | 25 (great 21) | none | no |
| dvd | 20 (great 16) | NLMeans ultralight/none | comb-detect + decomb |
| dvd_grainy | 22 (great 18) | NLMeans light/film | comb-detect + decomb |
| phone | 25 (great 21) | none | no |

## Consequences

**Good**

- Output matches what Wes already approved, so the first automated encodes are directly comparable to `samples/expected`.
- One command per file, easy to log and retry.

**Bad / accepted costs**

- Subtitle flags were verified on a Blu-ray rip (2026-09-17): `--all-subtitles` keeps every track but makes HandBrake skip the foreign audio search, so the builder lists every source track explicitly after `scan` (`-s scan,1,...,N --subtitle-forced=1 --subtitle-burned=1`). This means the subtitle count must come from ffprobe before the command is built.
- Hardware encoders (AMD VCE on this machine) are faster but were rejected in the notes for quality; software x265 medium is about 15 minutes per hour of video.
- The phone profile is a placeholder until a real clip is measured.

## Alternatives considered

- **FFmpeg libx265 directly:** same encoder, but re-implementing decomb, NLMeans and forced-subtitle logic would be new untested work.
- **HandBrake GUI presets file:** no saved presets exist on this machine; the CLI flags are the record instead.

## Related

- ADR-0003, ADR-0008, `docs/encoding-profiles.md`
