#!/bin/bash
# Cloud sessions commit as the repository's owner, never as Claude.
#
# A Claude Code cloud container starts with a global git identity of
# "Claude <noreply@anthropic.com>" and signs every commit with the
# environment's key, and the environment's stop hook then asks for commits to
# be rewritten under that identity. In this repository every commit is the
# owner's: this sets the owner's name and email (from the history) on the
# checkout, turns that signing off, and points the stop hook's unpushed check
# at main (work lands on main; the session's own branch is never pushed).
# Runs at every session start, resume, clear and compact; each step is
# idempotent and takes milliseconds. Local sessions are left alone.
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

name="$(git log --author=Steve-is-IT -1 --format=%an 2>/dev/null)"
email="$(git log --author=Steve-is-IT -1 --format=%ae 2>/dev/null)"
if [ -n "$name" ] && [ -n "$email" ]; then
  git config user.name "$name"
  git config user.email "$email"
fi

git config commit.gpgsign false
git config tag.gpgsign false

# The stop hook compares against origin/<current branch> when that ref exists,
# else origin/HEAD. Track main instead of the session branch.
branch="$(git branch --show-current)"
if [ -n "$branch" ] && [ "$branch" != "main" ]; then
  git update-ref -d "refs/remotes/origin/$branch" 2>/dev/null || true
fi
if git rev-parse -q --verify refs/remotes/origin/main >/dev/null; then
  git remote set-head origin main >/dev/null 2>&1 || true
fi
exit 0
