# Encoding profiles

Distilled from Wes's "Movie Encoding 2021" notes (`docs/Movie Encoding 2021.pdf`, July 2021 to September 2022). The code in `src/dmc/profiles.py` is the executable form of this page; keep the two in step.

## Settings shared by every profile

| Setting | Value | Why (from the notes) |
|---------|-------|----------------------|
| Container | MKV | "MKV does subtitles correctly. MP4 keeps burning in the wrong subtitle." Plex streams MKV x265 fine. |
| Video encoder | x265 10-bit | 10-bit "looks smoother" than 8-bit at similar size; x265 beats x264 by a wide margin at the same quality. |
| Encoder preset | medium | Medium vs fast: "big difference", medium motion is smoother. Medium vs slow: almost no visual difference, slow is much larger and takes 2x as long. |
| Encoder tune | fastdecode | "No visual difference, 0.14% cost." Keeps playback light on TVs and phones. |
| Advanced options | `ref=4:bframes=8:rc-lookahead=60:subme=7:aq-mode=3` | The "switched" settings: 2.5% size change for a "major quality difference". |
| Rate control | Constant quality (RF), variable frame rate same as source | Consistent look across scenes. |
| Audio | First English track, AAC 160 kb/s stereo downmix, no passthrough | 5.1 costs about 9% more for no gain on the target players. |
| Subtitles | All tracks kept; Foreign Audio Scan with forced-only burned in; English first | Fixes foreign-dialogue scenes without burning full subtitles. |

Encode time on the 2021 machine: x265 medium roughly 15 min per hour of video; NVENC/AMD hardware about 4 to 5 min per hour but lower quality per bit. Software x265 was chosen.

## Per-source profiles

| Profile | RF usual | RF great | Range seen | Denoise | Deinterlace | Notes |
|---------|----------|----------|------------|---------|-------------|-------|
| `bluray` | 25 | 21 | 24 to 27 | none | no | "26 medium looks great"; 24 for the pretty ones. Washed-out or low-light films (Endgame, Captain Marvel, Star Trek II, Sully) want 20 to 23. |
| `dvd` | 20 | 16 | 18 to 22 | NLMeans Ultralight, tune none | comb-detect + decomb | Men In Black, A Knight's Tale, Capaldi Doctor Who at 18 to 20. |
| `dvd_grainy` | 22 | 18 | 20 to 24 | NLMeans Light or Ultralight, tune film | comb-detect + decomb | TMNT at 22 to 24. Expendables "grainy and washed out" at 24. Unsharp caused edge distortion and was dropped. |
| `phone` | 25 | 21 | 23 to 27 | none | no | Assumed Blu-ray-like. Not yet tuned against a real phone clip. |

### Hard cases from the notes

- **Arrival (DVD):** "looks bad no matter what". Best result was NLMeans Ultralight + Unsharp Light at RF 12, or no filter at RF 16. Low light and low contrast compress badly; use `--rf 16 --force dvd`.
- **Doctor Who (2005) DVDs:** Ultralight at RF 18 to 23 depending on series; 20 looks great but is 3 GB per hour, 23 is the compromise.
- **Animation:** listed as "still working on" in the notes; no settled profile.
- **Compression achieved:** Blu-ray 4.4 to 5x at RF 24 to 26 (up to 30x on some titles); RF 26 "starts to get the pixelation distortion" on fast scenes; RF 34 and 40 are unusable.

## Classification rules (ADR-0008)

| Observation | Class |
|-------------|-------|
| Width >= 1280 in MKV from MakeMKV | `bluray` |
| Width >= 1280, MP4/MOV, H.264/HEVC, rotation tag or >= 29 fps or Apple/Android tags | `phone` |
| 720 (or less) wide, 480 or 576 tall, or MPEG-2 | `dvd`, then grain score decides `dvd` vs `dvd_grainy` |
| SD with overall bit rate under 3.5 Mb/s | leans `dvd_grainy` before measuring |

The grain score is the mean luma difference between sampled frames and a Gaussian-blurred copy (0 to 255). Threshold starts at 6.0 and must be calibrated with labelled files in `samples/dvd` and `samples/dvd-grainy`; the integration test prints the scores.

## Trial results (this machine, AMD Radeon 890M laptop, software x265)

| Source | Clip | Output | Notes |
|--------|------|--------|-------|
| Star Trek TNG S3E16 Blu-ray, 1080p H.264 24.9 Mb/s | 60 s at 10:00, `bluray` RF 25 | 1.14 Mb/s HEVC 10-bit, 1436x1080 after autocrop, 43 s wall | About 22x smaller. Autocrop removed the 4:3 pillarbox. Encode ran at about 1.4x real time, so a 46-minute episode is roughly 33 minutes and a two-hour film about 90. |

## Manual overrides

```
dmc plan <file>                    show the decision and HandBrake command, encode nothing
dmc encode <file> --great          use the "great" RF for a favourite
dmc encode <file> --rf 16          exact RF
dmc encode <file> --force dvd_grainy
dmc run <root> --watch             unattended: <root>/inbox -> <root>/outbox
```
