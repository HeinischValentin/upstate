FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git && rm -rf /var/lib/apt/lists/*

# Install UV (manually because the astral images don't support armhf)
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# pyproject.toml declares readme = "../README.md", which resolves to /README.md from WORKDIR /app
COPY README.md /README.md
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src ./src

RUN uv sync --frozen --no-dev --no-editable

COPY --from=ghcr.io/regclient/regctl /regctl regctl
RUN chmod 755 regctl


FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/regctl /usr/bin/regctl

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["upstate-api"]
CMD ["/config/config.yaml"]
