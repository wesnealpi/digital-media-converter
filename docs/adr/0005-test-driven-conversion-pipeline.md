# ADR-0005: Build the conversion pipeline test-first

- **Status:** Proposed
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

The pipeline will be tuned by repeated experiment. Without tests, each tuning change risks regressing a source type that was already working, and "does this still look right" becomes a manual step.

## Decision

Every behaviour is written test-first. Three layers:

1. **Unit tests** for pure logic (command building, source detection, size math, settings lookup). No media required; run everywhere.
2. **Integration tests** that run FFmpeg on files under `samples/` and assert on measurable outputs: container and codec of the result, size ratio against the source within a target band, and objective quality metrics (VMAF, with SSIM as a fallback) above a threshold. Skipped when samples or FFmpeg are absent.
3. **Manual review** for perceptual sign-off. Approved outputs are copied to `samples/expected/` and become the reference for later runs.

Implementation language, test runner, and metric thresholds are open until Wes's conversion notes are in; they will be settled in follow-up ADRs.

## Consequences

**Good**

- Tuning becomes a loop of change a number, run tests, compare metrics.
- Quality and size targets are stated as assertions rather than remembered.

**Bad / accepted costs**

- VMAF scoring is slow on long sources; integration tests should use short clips or a time-limited segment.
- Some setup before the first useful encode runs.

## Alternatives considered

- **Script first, test later:** faster start, but the tuning loop is exactly where regressions happen.

## Related

- ADR-0003, ADR-0004
