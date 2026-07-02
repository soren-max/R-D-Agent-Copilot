# Git Rollback Playbook

## Roll Back A Risky Commit

When a recent Git change is suspected, prefer a reversible rollback process.

Recommended checks:

- Identify the exact commit range included in the release.
- Read the changed files and risk area.
- Use revert for shared branches instead of rewriting published history.
- Link rollback action to the incident trace.

Risk note: do not force push shared release branches during incident handling unless the repository owner explicitly approves it.
