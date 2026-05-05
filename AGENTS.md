# AGENTS.md

This file provides guidance for agents when working with code in this repository.

## Backend (Python)

```bash
cd backend
uv sync --group dev          # install deps
uv run ruff format .         # format
uv run ruff check .          # lint
uv run python -m unittest discover -s tests -v  # all tests
uv run python -m unittest tests.test_loader     # single test module
```

## Frontend (TypeScript/React)

```bash
cd frontend
npm ci          # install deps
npm run lint    # lint
npm run build   # type-check + production build
```

## Architecture

The app checks for updates across multiple systems (TrueNAS, Home Assistant, Docker) via a YAML-configured plugin system.

- `backend/src/upstate/interface.py` — abstract `Checker` base class all plugins implement
- `backend/src/upstate/loader.py` — parses YAML config, interpolates `${ENV_VAR}` syntax
- `backend/src/upstate/server.py` — FastAPI app; `GET /checkers` lists types, `GET /checkers/{type}` runs one
- `frontend/src/App.tsx` — fetches from those endpoints; `UpdateCard` renders each result

Two entry points: `upstate` (CLI, prints to stdout) and `upstate-api` (REST server).

## General

When adding new third-party applications or libraries, remember checking their license and adding it to THIRD_PARTY_LICENSES.

