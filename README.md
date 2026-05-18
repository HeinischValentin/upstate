<h1>
  <p align=center>
    <img src=".github/assets/logo.svg" alt="Logo" width="128">
    <br>Upstate
  </p>
</h1>



Keeping track of your systems made easy.
`upstate` is a command-line tool that checks for pending updates on your systems and reports them in a human-friendly format.
It supports various technologies and offers lightweight configuration.

## Currently supported systems

- `truenas`: checks for pending TrueNAS system updates.
- `truenas-apps`: checks installed TrueNAS apps for available upgrades.
- `homeassistant`: checks Home Assistant core/system update entities.
- `docker`: checks whether running containers are using the latest image from the registry.

## Running

**CLI** — prints results to stdout:

```bash
upstate path/to/config.yaml
```

**API server** — serves a REST API:

```bash
upstate-api path/to/config.yaml
```

Options: `--host`, `--port`, `--ssl-certfile`, `--ssl-keyfile`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/checkers` | Get a list of all available checkers |
| GET | `/checkers/<checker>` | Get JSON result of `<checker>` |
| GET | `/health` | Liveness check |
| GET | `/docs` | Interactive OpenAPI documentation |

## Configuration

Configuration is loaded from a YAML file with a top-level `checkers` list.
Values can reference environment variables with `${VAR}`; a sibling `.env` file is loaded before falling back to the process environment.

Example:

```yaml
checkers:
  - type: truenas
    host: truenas.example.com
    api_key: ${TRUENAS_API_KEY}
    verify_ssl: false

  - type: truenas-apps
    host: truenas.example.com
    api_key: ${TRUENAS_API_KEY}

  - type: homeassistant
    url: https://homeassistant.local:8123
    token: ${HOMEASSISTANT_TOKEN}

  - type: docker
```
### TrueNAS

The TrueNAS system and apps checkers also support username/password authentication instead of `api_key`:

```yaml
checkers:
  - type: truenas-apps
    host: truenas.example.com
    username: ${TRUENAS_USERNAME}
    password: ${TRUENAS_PASSWORD}
```

Set `verify_ssl: false` only when needed for self-signed or otherwise untrusted certificates. If omitted, SSL certificate verification stays enabled.

### Home Assistant

The Home Assistant checker uses a long-lived access token and inspects Home Assistant core/system update entities exposed by the REST API.

```yaml
checkers:
  - type: homeassistant
    url: https://homeassistant.local:8123
    token: ${HOMEASSISTANT_TOKEN}
    verify_ssl: false
```

### Docker

The Docker checker connects to the local Docker socket and compares each running container's local image digest against the current digest in the registry using [`regctl`](https://regclient.org/cli/regctl/).
Containers whose image has no registry digest (e.g. locally built images) are silently skipped.

`regctl` must be installed and available on `$PATH` (or configured via `regctl_path`).

```yaml
checkers:
  - type: docker
    socket: /var/run/docker.sock  # optional, this is the default
    regctl_path: regctl           # optional, this is the default
```

## Docker Compose

The easiest way to run the full stack (API + web UI) on any machine is with the provided `docker-compose.yml`.

1. Copy `conf.yml` and create a `.env` file with your secrets next to it:

```env
TRUENAS_API_KEY=your-key
HOMEASSISTANT_TOKEN=your-token
```

2. Start the stack:

```bash
docker compose up -d
```

The web UI is then available at `http://localhost:8080`.

## Security considerations

This service is **not safe** for public exposure!
Neither backend nor frontend currently contain any sort of authentication or encryption.
Use at your own risk and do not expose to the internet!

To fetch information about running containers, the tool has to access the docker socket.
While upstate won't do anything harmful, giving anyone access to the socket is technically a risk.
See the [docker docs](https://docs.docker.com/engine/daemon/remote-access/) for more information.

## Roadmap

Just some ideas for the future:

- Parallelization of backend tasks
- Notifications
- Exclusion rules

## Development

### Backend

We use [uv](https://github.com/astral-sh/uv) for handling python dependencies.

Install development dependencies with:

```bash
uv sync --group dev
```

Run linting with:

```bash
uv run ruff check .
```

Format the project with:

```bash
uv run ruff format .
```
