# Safety and Git Baseline

## Before any change

Capture:
- Canonical repository root.
- Git worktree status, including staged, unstaged, and untracked files.
- Current branch and HEAD commit.
- Remote names and URLs, with embedded credentials redacted.
- Detached HEAD, shallow clone, submodule, linked worktree, and divergence indicators where available.

## Protect pre-existing work

- Treat every change present at initialization as user-owned.
- Do not stage, edit, delete, stash, reset, clean, or overwrite it.
- Do not include it in a RepoCraft commit.
- If a planned edit overlaps a pre-existing modified file, stop and ask before editing that file.
- Do not use destructive cleanup commands.

## Git restrictions

Never:
- `git reset --hard`
- `git clean -fd` (or broader destructive variants)
- force-push
- rewrite published history
- bypass branch protection
- blindly stage the entire repository
- commit secrets, credentials, private keys, local environment files, or unrelated user work

## Publishing preconditions

Publishing requires all of the following:
1. User authorization under the active policy.
2. Verified repository root, remote, branch, and account context.
3. No unrelated or pre-existing user changes in the commit.
4. All mandatory configured quality gates pass.
5. No unresolved critical security finding.
6. Final diff and staged content reviewed.
7. No secrets or sensitive artifacts staged.
8. Remote and branch protection rules permit the action.

If any precondition is unknown or false, do not publish.
