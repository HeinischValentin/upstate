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

## General

When adding new third-party applications or libraries, remember checking their license and adding it to THIRD_PARTY_LICENSES.

