# ADR-0002: Pin each repo to one GitHub account via username-in-URL

- **Status:** Accepted
- **Date:** 2026-09-17
- **Deciders:** Wes Watson

## Context

The same Windows machine is used for a personal GitHub account (`wesnealpi`) and several professional accounts and orgs, all over HTTPS. Git Credential Manager (GCM) 2.9 caches one token per credential target. With a bare `https://github.com/...` remote every repo shares the `git:https://github.com` target, so whichever account signed in last wins, and commits fall through to the global `user.email`. Switching accounts in GitHub Desktop is manual and error-prone.

One unrelated repo on this machine already uses the `https://<other-account>@github.com/...` form and has its own `git:https://<other-account>@github.com` credential. That pattern works and needs no extra tooling.

## Decision

Every repository is pinned locally, never globally:

1. `user.name`, `user.email`, and `credential.username` are set in the repo's `.git/config`.
2. The origin URL embeds the account: `https://<username>@github.com/<owner>/<repo>.git`. GCM then stores and looks up a token per `username@host`.
3. Account aliases live in `~/.git-accounts.json`, outside any repo.
4. Commits and pushes are done from PowerShell with plain `git`, through the `git-commit` and `git-push` skills, which refuse to run until `Get-GitAccount.ps1 -Strict` passes.

## Consequences

**Good**

- No repo can accidentally push or commit as the wrong account; the check is mechanical.
- No dependence on GitHub Desktop or on which account a browser is signed into.
- Works for GitLab the same way.

**Bad / accepted costs**

- Each new clone needs one `Set-GitAccount.ps1` call.
- The first push per account per machine triggers a GCM browser sign-in.
- SSH remotes are not covered; they would need per-account `Host` entries in `~/.ssh/config`.

## Alternatives considered

- **`includeIf` by directory in `~/.gitconfig`:** fixes identity but not credentials, and repos for different accounts are mixed in one `dev/git` folder.
- **`credential.useHttpPath = true`:** stores a token per repository path, which means signing in once per repo rather than once per account.
- **`gh auth switch`:** `gh` is not installed and it still leaves the git credential ambiguous.
- **SSH keys per account:** works, but the existing tokens and GCM setup are HTTPS, and Windows SSH agent handling adds friction.

## Related

- `.claude/skills/git-account/`, `.claude/skills/git-commit/`, `.claude/skills/git-push/`
