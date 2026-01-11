# Development Workflow & Branching Strategy

We follow a GitFlow-lite process designed for fast iteration with clear stability lanes.

## Branches
- `main`: Always deployable. Protected; merges only via PRs.
- `develop`: Integration branch for upcoming changes. CI must pass before merge to `main`.
- `feature/<slug>`: New work tied to an issue or task. Merge into `develop` via PR.
- `hotfix/<slug>`: Critical fixes branching off `main`. Merge back into `main` and `develop`.

## Rules
- Every change lands through a Pull Request.
- CI must pass; reviewers required for `main` and `develop`.
- Descriptive commit messages and PR descriptions.

## Naming
- Feature: `feature/live-team-stats` or `feature/email-template-refresh`
- Hotfix: `hotfix/fix-daily-cron`

## Protections (Repository Settings)
- Protect `main` and `develop`: require PR, status checks, and linear history.
- Require `ci` workflow to pass (see `.github/workflows/ci.yml`).

## Release Flow
1. Work in `feature/*`, open PR to `develop`.
2. Stabilize in `develop`; tag release commit when ready.
3. Open PR `develop` → `main`; deploy on merge.

## Tips
- Small PRs (under ~300 lines) are easier to review.
- Keep commits logically grouped.
- Document non-obvious decisions in `docs/decisions/` (ADRs) as needed.
