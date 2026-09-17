---
name: adr
description: Create or update an Architecture Decision Record in docs/adr. Use whenever a design choice is made or changed (codec, container, tooling, quality targets, directory layout, testing strategy), or when the user says ADR, decision record, or "let's document that decision".
---

# Architecture Decision Records

Decisions live in `docs/adr/NNNN-short-kebab-title.md`, numbered sequentially from 0001. `docs/adr/README.md` is the index and must be updated whenever a record is added or its status changes.

## When to write one

Any choice that would be expensive to reverse or that a future reader would ask "why?" about: encoder and settings, container format, how samples are stored, test approach, tool choices, directory layout, account/credential handling. Small implementation details do not get an ADR.

## Procedure

1. Find the next number: highest `NNNN` in `docs/adr/` plus one.
2. Copy `docs/adr/template.md` to the new file and fill every section. Keep it under a page. Write for someone reading it in a year with no context.
3. Status starts as `Proposed` unless the user has already made the call, then `Accepted`. Superseding: set the old record to `Superseded by ADR-NNNN` and link both ways. Never delete or rewrite an accepted ADR's decision; write a new one.
4. Add a line to the index table in `docs/adr/README.md`.
5. If code or config implements the decision, mention the ADR number in the commit message (`adr` type or a reference in the body).

## Style

- Title is the decision, phrased as a short statement: "Use H.265 as the default video codec", not "Codec choice".
- Context states the forces (quality target, size target, sources, hardware, time). Numbers go in a small table.
- Consequences list both the good and the bad, including what becomes harder.
- Alternatives considered get one or two sentences each on why they lost.
