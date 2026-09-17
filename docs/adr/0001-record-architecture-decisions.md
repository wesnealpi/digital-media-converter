# ADR-0001: Record architecture decisions in this directory

- **Status:** Accepted
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

This is a prototype that will go through several rounds of trying encoder settings, containers, and tooling. Without a written trail the reasons behind a setting get lost, and later experiments repeat earlier ones.

## Decision

Keep Architecture Decision Records in `docs/adr/`, one Markdown file per decision, numbered from 0001, using `template.md`. `README.md` in the same directory is the index. Accepted records are never edited to change the decision; a new record supersedes them.

## Consequences

**Good**

- Every non-obvious setting has a "why" that a future reader can find.
- Reversals are visible as a chain of records rather than silent edits.

**Bad / accepted costs**

- Small overhead per decision. Kept low by a one-page limit.

## Alternatives considered

- **Wiki or issue comments:** not versioned with the code and easy to lose when switching accounts.
- **Comments in code:** fine for local detail, but codec and quality targets cut across files.

## Related

- `.claude/skills/adr/SKILL.md`
