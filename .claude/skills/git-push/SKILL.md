---
name: git-push
description: Push the current branch to origin from PowerShell after confirming the pinned GitHub account and that the remote URL selects the right Credential Manager token. Use when the user asks to push, publish, or sync to GitHub.
---

# Git push (PowerShell, account-checked)

Pushing is outward-facing, so it only happens when the user asks for it in the current conversation. Wes's word **"checkin"** means commit and push together, so after a `git-commit` triggered by "checkin", run this skill immediately without asking again. "commit" or "save" alone does not authorise a push.

## Procedure

1. **Verify the account.**
   `powershell -NoProfile -File .claude/skills/git-account/scripts/Get-GitAccount.ps1 -Strict`
   Stop on failure. The origin URL must contain `<username>@` so GCM picks that account's token. Report the alias and the URL to the user before pushing.
2. **Check what will go out.** `git fetch origin` then `git log --oneline '@{u}..HEAD'` (or `origin/main..HEAD` for a new branch). If there are commits authored by a different email than the pinned one, stop and report them.
3. **Push.**
   - Existing upstream: `git push`
   - New branch: `git push -u origin HEAD`
   - Never `--force`. If the user needs a force push, use `--force-with-lease` and only after they confirm the branch name.
4. **First push on a new account.** GCM opens a browser sign-in for `<username>@github.com`. Tell the user to sign in as that account; if the browser is already logged into a different account, they should use a private window or sign out first. The token is then stored under `git:https://<username>@github.com` and later pushes are silent.
5. **Confirm.** `git status -sb` should show the branch in sync with its upstream.

## Rules

- No pull request creation from this skill; `gh` is not installed on this machine. Give the user the compare URL instead: `https://github.com/<owner>/<repo>/compare/<branch>?expand=1`.
- If the push is rejected as non-fast-forward, do `git pull --rebase` only after showing the user the incoming commits; never merge silently.
