import os
import re
from pathlib import Path
from typing import Any

import yaml

from .interface import Checker, ConfigurationError

REGISTRY: dict[str, type[Checker]] = {}

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def register_checker(type_name: str):
    def decorator(cls: type[Checker]) -> type[Checker]:
        REGISTRY[type_name] = cls
        cls._checker_type = type_name
        return cls

    return decorator


def _load_env(config_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    env_file = config_path.parent / ".env"
    if env_file.exists():
        from dotenv import dotenv_values

        env.update(dotenv_values(env_file))  # type: ignore[arg-type]
    env.update(os.environ)  # os.environ takes priority
    return env


def _resolve_env_vars(value: Any, env: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v, env) for v in value]
    if isinstance(value, str):

        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name not in env:
                raise ConfigurationError(
                    f"Environment variable '{var_name}' is not set"
                )
            return env[var_name]

        return _ENV_PATTERN.sub(replace, value)
    return value


def load_checkers_from_yaml(config_path: Path) -> list[Checker]:
    # Deferred imports so decorators fire and populate REGISTRY.
    # Add one line here per new checker module.
    from . import docker as _docker  # noqa: F401
    from . import homeassistant as _homeassistant  # noqa: F401
    from .truenas import apps as _apps  # noqa: F401
    from .truenas import system as _system  # noqa: F401

    env = _load_env(config_path)

    with config_path.open() as f:
        raw = yaml.safe_load(f)

    raw = _resolve_env_vars(raw, env)

    entries = raw.get("checkers", [])
    if not entries:
        raise ConfigurationError("No checkers defined in config file.")

    checkers: list[Checker] = []
    for i, entry in enumerate(entries):
        entry = dict(entry)
        type_name = entry.pop("type", None)
        if type_name is None:
            raise ConfigurationError(f"Checker entry {i} missing required key 'type'.")
        cls = REGISTRY.get(type_name)
        if cls is None:
            raise ConfigurationError(
                f"Unknown checker type '{type_name}'. Known types: {sorted(REGISTRY)}"
            )
        instance = cls()
        instance.configure(entry)
        checkers.append(instance)

    return checkers
