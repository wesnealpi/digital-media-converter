---
name: git-commit
description: Stage and commit work in this repo from the PowerShell command line, verifying the pinned GitHub account first. Use when the user asks to commit, check in, save to git, or wrap up a change. Never pushes.
---

# Git commit (PowerShell, account-checked)

Commits are made with plain `git` from PowerShell, not the GitHub Desktop app, so that the per-repo account pinning from the `git-account` skill is always what decides author and credentials.

## When to run

Only after Wes has confirmed the feature is done and asked for it. Never commit on your own initiative, even for docs. If Wes said **"checkin"**, run this skill and then the `git-push` skill without asking again. If Wes said "commit" or "save", stop after the commit.

## Procedure

1. **Verify the account.** Run
   `powershell -NoProfile -File .claude/skills/git-account/scripts/Get-GitAccount.ps1 -Strict`
   If it fails, stop and fix it with the `git-account` skill before staging anything. Show the user the alias it reports.
2. **Review what changed.** `git status` and `git diff` (plus `git diff --cached` if something is already staged). Do not commit files that are obviously unintended: secrets, `.env`, credentials, media under `samples/`, build output.
3. **Branch check.** If on `main` and the change is more than a docs or config tweak, create a branch first (`git switch -c <type>/<short-name>`) unless the user said to commit on main.
4. **Stage precisely.** Prefer `git add <paths>` over `git add -A` so nothing surprising rides along. Use `git add -A` only when the user asks or the diff has been reviewed in full.
5. **Write the message.** Format:

   ```
   <type>(<scope>): <imperative summary, under 72 chars>

   <why this change, not what; wrap at 72>

   Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
   ```

   Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `adr`. Scope is optional (`encoder`, `dvd`, `phone`, `adr`, `skills`). Reference an ADR by number when the commit implements or records a decision.
6. **Commit from PowerShell.** Multi-line messages are easiest with repeated `-m`; each one becomes a paragraph:

   ```powershell
   git commit -m "adr: record H.265 as default codec" -m "Explains the size/quality trade-off chosen for the first prototype. See ADR-0003." -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
   ```

   For long bodies, write the message to a file in the scratchpad and use `git commit -F <file>`.
7. **Confirm.** Run `git log -1 --format='%h %an <%ae> %s'` and show the user the author line so a wrong-account commit is caught immediately.

## Rules

- One logical change per commit. Split unrelated edits.
- Tests accompany code. If a commit adds behaviour without tests, say so in the reply and in the message body.
- Never `--amend`, `--no-verify`, or rewrite history unless the user asks for that specific commit.
- Never push from this skill. Pushing is the `git-push` skill. "checkin" from Wes covers both; anything else needs a separate go-ahead for the push.
