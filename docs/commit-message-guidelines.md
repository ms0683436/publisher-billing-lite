# Commit Message Guidelines (Conventional Commits)

This repo uses the Conventional Commits format to keep history readable and to make it easier to review changes, generate changelogs, and understand impact at a glance.

## 1) Required Format

```text
<type>(<scope>)!: <subject>

<body>

<footer>
```

- `type`: change category (required)
- `scope`: impacted area (recommended; can be omitted for truly generic changes)
- `!`: indicates a **breaking change** (use only when it is actually breaking)
- `subject`: one-line summary (required)
- `body`: explains *why* and *how* (optional but recommended)
- `footer`: issue/PR references, breaking-change details (optional)

## 2) Allowed Types

Use only the following types (avoid inventing new ones):

- `feat`: a new user-visible feature
- `fix`: a bug fix (logic errors, exceptions, incorrect data handling)
- `refactor`: refactoring (no behavior change, not a bug fix, not a new feature)
- `perf`: performance improvements
- `docs`: documentation only (README, comments, API docs)
- `test`: adding/updating tests only
- `build`: build tooling, dependencies, Dockerfile, build scripts
- `ci`: CI/CD configuration (pipelines, GitHub Actions)
- `chore`: maintenance work (formatting, lint rules, misc repo upkeep)
- `revert`: revert a previous commit

## 3) Scope Rules (Recommended)

Scope helps readers locate the affected area quickly. Prefer this fixed set:

- `api`: backend API (FastAPI / Python)
- `web`: frontend web app (React / Vite)
- `db`: data layer / seed / migrations (if applicable)
- `docker`: Docker / Compose
- `deps`: dependency updates (pnpm/uv/poetry/lockfiles)
- `repo`: repository-wide maintenance (structure, tooling, git hooks)

Examples: `feat(api): ...`, `fix(web): ...`, `chore(deps): ...`

> Rule: scopes are lowercase and short; don’t use long paths (e.g. `apps/api/app/services`).

## 4) Subject Rules (Must Follow)

- Use the imperative mood (e.g. “add”, “fix”, “remove”, “update”)
- Do not end with a period (`.`)
- Keep it short (recommended ≤ 72 chars)
- Be specific (avoid vague messages):
  - Good: `fix(api): handle missing adjustments as 0`
  - Bad: `fix: bug`

## 5) Body Rules (Recommended)

The body should answer:

- **Why**: why is this change needed? (context, constraints, problems)
- **How**: how does it solve it? (approach, decisions, trade-offs)

Wrap lines at ~72 characters and use paragraphs.

## 6) Footer / Issue References

- Reference without auto-closing: `Refs #123`
- Auto-close on merge: `Closes #123`

Multiple references are fine:

```text
Refs #12
Closes #34
```

## 7) Breaking Changes

A change is **breaking** if it requires consumer action, for example:

- API contract changes (remove/rename fields, incompatible type changes)
- incompatible schema changes
- configuration or usage changes required by users

Use one of these forms:

1. Add `!` in the header

```text
feat(api)!: rename invoice adjustments field
```

1. Add a `BREAKING CHANGE:` footer (recommended for more detail)

```text
feat(api): rename invoice adjustments field

BREAKING CHANGE: clients must send `adjustments_cents` instead of `adjustments`.
```

## 8) Common Examples (Copy/Paste)

### Feature

```text
feat(web): add invoice adjustments editor
```

### Bug fix

```text
fix(api): validate adjustment input is numeric
```

### Refactor

```text
refactor(api): extract invoice total calculation
```

### Dependency update

```text
chore(deps): bump mui to latest compatible version
```

### Docker / Compose

```text
build(docker): cache pnpm store layer
```

### Revert

```text
revert: feat(web): add invoice adjustments editor

This reverts commit <SHA>.
```

## 9) Team Agreements (Quick Tips)

- One commit should represent one cohesive change (split “feature” vs “refactor”)
- Prefer multiple small commits over one huge commit (easier review)
- Don’t mix formatting/lint-only changes with feature work (use a separate `chore:` commit)

## 10) (Optional) Git Commit Template

To nudge yourself into the format every time, enable the repo’s `.gitmessage` template:

```bash
git config commit.template .gitmessage
```
