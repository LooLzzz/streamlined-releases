# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A Docker-based GitHub Action that automates semantic versioning and changelog generation using [`git-cliff`](https://git-cliff.org/). It runs in two modes:

- **On push** → Creates/updates a Release Candidate (RC) PR with a bumped version and changelog diff
- **On PR merged** (for RC branches) → Creates a GitHub Release with the full changelog

## Development Commands

```bash
# Run locally (requires .env file with GitHub Actions context vars)
uv run python -m streamlined_releases

# Format code
autopep8 --in-place --aggressive --aggressive src/
isort src/
sort-all src/

# Build Docker image
docker build .

# Build multi-platform image for publishing
docker compose build
```

## Architecture

### Entry Point Flow

```
__main__.py
  → setup logging (utils/logging.py)
  → load settings (settings.py)
  → match GITHUB_EVENT_NAME:
      push         → events/push.py → on_push()
      pull_request → events/pull_request.py → on_pull_request_merged()
```

### Key Files

| File | Role |
|------|------|
| `settings.py` | Pydantic settings binding all `GITHUB_*` env vars; exposes `app_settings` singleton |
| `events/push.py` | RC PR creation/update logic |
| `events/pull_request.py` | GitHub Release creation on RC merge |
| `services/git.py` | `git-cliff` and `uv version` operations; branch/commit management |
| `services/github.py` | PyGithub API calls (PR create/update, release create) |
| `action.yml` | GitHub Action metadata; inputs: `git_username`, `git_email`; outputs: `diff_changelog`, `changelog` |
| `Dockerfile` | Builds on `uv:python3.12-bookworm-slim`; installs git-cliff binary |

### RC Branch Convention

RC branches follow the pattern `rc/{bumped_version}-{source_branch}`, e.g. `rc/1.2.0-main`. The push handler searches for existing RC PRs matching this pattern to decide whether to create or update.

### Settings Structure

- `GithubEnv` — maps all `GITHUB_*` env vars; provides `.event_payload`, `.pull_request`, `.github` (PyGithub client, cached with `@lru_cache`)
- `Inputs` — maps `INPUT_*` env vars (action inputs); `git_username`, `git_email` override `bump_commit_actor` at startup via `@model_validator`
- `Settings` — app-level config (release branches, changelog path, bump commit actor; defaults to `github-actions[bot]` identity)
- All composed into `app_settings = Settings()`

### External Tools

- **git-cliff** — changelog generation from conventional commits (installed in Docker image)
- **uv** — version bumping via `uv version --bump patch/minor/major`

## Environment Variables

For local testing, create a `.env` file with standard GitHub Actions context variables (`GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `GITHUB_REF`, `GITHUB_EVENT_NAME`, `GITHUB_EVENT_PATH`, etc.). See `settings.py → GithubEnv` for the full list.

Set `RUNNER_DEBUG=1` to enable `DEBUG`-level logging.
