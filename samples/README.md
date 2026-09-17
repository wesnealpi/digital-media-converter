# samples/

Local-only sample media for testing conversions. Every file and folder in here is ignored by git (see the `.gitignore` next to this file), so drop originals in freely. Nothing placed here will be uploaded.

Suggested layout, one folder per source type:

```
samples/
  bluray/      raw MakeMKV rips from Blu-ray (H.264/VC-1 1080p, DTS/TrueHD audio)
  dvd/         raw MakeMKV rips from good-quality DVDs (MPEG-2 720x480/576)
  dvd-grainy/  raw rips from old or poorly encoded DVDs
  phone/       high-resolution, low-compression phone recordings (MP4/MOV, H.264 or HEVC)
  expected/    Wes's hand-approved encodes, used as references by tests
```

The folder a raw rip sits in is its label: the integration tests assert that the classifier agrees with the folder. Keep the original filename; tests locate fixtures by folder and extension, not by a fixed name.

If a sample is small enough to share and free to redistribute, that is a separate decision (see `docs/adr/0004-keep-sample-media-out-of-git.md`), not something to do by editing the ignore rules here.
