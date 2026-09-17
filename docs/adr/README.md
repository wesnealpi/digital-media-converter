# Architecture Decision Records

Short records of the design choices behind this project and why they were made. New records follow `template.md`; numbering is sequential and never reused. See the `adr` skill in `.claude/skills/adr/` for the procedure.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions in this directory | Accepted |
| [0002](0002-pin-git-account-per-repo.md) | Pin each repo to one GitHub account via username-in-URL | Accepted |
| [0003](0003-use-h265-as-default-codec.md) | Use H.265 (HEVC) as the default output codec | Accepted |
| [0004](0004-keep-sample-media-out-of-git.md) | Keep sample media local and out of git | Accepted |
| [0005](0005-test-driven-conversion-pipeline.md) | Build the conversion pipeline test-first | Proposed |
| [0006](0006-python-and-pytest.md) | Implement the pipeline in Python with pytest | Accepted |
| [0007](0007-handbrake-cli-with-notes-profiles.md) | Encode with HandBrakeCLI using the profiles from the 2021 notes | Accepted |
| [0008](0008-source-classification.md) | Classify sources by metadata first, then a measured grain score | Proposed |
| [0009](0009-inbox-outbox-pipeline.md) | Unattended encoding as an inbox/outbox folder pipeline | Proposed |
