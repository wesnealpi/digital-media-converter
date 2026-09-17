---
name: git-account
description: Check, set, or register which GitHub/GitLab account a repository commits and pushes as. Use before any commit or push, when the user mentions switching accounts, wrong author, or a credential prompt for the wrong account, or when setting up a new clone.
---

# Git account (per-repo identity and credentials)

Wes switches between a personal GitHub account and several professional ones on the same machine, all over HTTPS with Git Credential Manager (GCM). The rule that makes this safe:

**Every repo is pinned locally to one account, and its origin URL embeds that account's username** (`https://<username>@github.com/owner/repo.git`). GCM stores one token per `username@host`, so the embedded name selects the right token and no repo ever falls back to the shared `git:https://github.com` credential. The global `~/.gitconfig` identity is never relied on.

Account aliases live in `~/.git-accounts.json` (outside the repo, never committed). Each entry: `host`, `username`, `name`, `email`.

All scripts are in `scripts/` next to this file and run under Windows PowerShell 5.1. Call them from the repo root, for example:
`powershell -NoProfile -File .claude/skills/git-account/scripts/Get-GitAccount.ps1`

## Check the current account

```
Get-GitAccount.ps1 [-Strict]
```

Prints alias, name/email with their config scope, origin URL, and the account in the URL. `-Strict` exits 1 if anything is not pinned locally or the URL has no username. The `git-commit` and `git-push` skills run this first and stop on failure.

## Pin a repo to an account

```
Set-GitAccount.ps1 -Account <alias> [-RepoPath <path>] [-WhatIf]
```

Sets local `user.name`, `user.email`, `credential.username`, and rewrites the origin URL with the username. Refuses to rewrite the URL if the remote host does not match the account's host. Tell the user which alias you chose and why; if the right alias is not obvious from the remote owner, ask.

## Register a new account alias

```
Register-GitAccount.ps1 -Alias <alias> -Username <login> -Name '<Full Name>' -Email '<email>' [-HostName github.com]
```

Ask the user for the login and the email GitHub expects (the `noreply` address if they keep email private). Never guess an email.

## Choosing an alias

Look at the origin owner. Personal projects under `wesnealpi` use `personal`. Professional orgs map to whichever registered alias has push rights there. When a repo is new and has no remote, ask which account it belongs to before adding one.

## What this skill never does

- Never edits `~/.gitconfig`.
- Never stores or prints tokens. GCM prompts in a browser the first time a new `username@host` is used; that prompt is expected.
- Never switches accounts by rewriting history or amending existing commits. If past commits carry the wrong author, report it and let the user decide.
