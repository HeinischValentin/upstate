import json
import logging
import ssl
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .interface import (
    AuthenticationError,
    Checker,
    CheckResult,
    ConfigurationError,
    UpdateItem,
)
from .loader import register_checker


def _make_update_item(state: dict[str, Any]) -> UpdateItem | None:
    attributes = state.get("attributes", {})
    name = (
        attributes.get("title")
        or attributes.get("friendly_name")
        or state.get("entity_id")
        or "unknown"
    )
    installed = attributes.get("installed_version")
    latest = attributes.get("latest_version")
    if installed and latest:
        return UpdateItem(
            name=str(name), current_version=str(installed), new_version=str(latest)
        )
    return None


@register_checker("homeassistant")
class HomeAssistantChecker(Checker):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.host = ""
        self.token = ""
        self.verify_ssl = True

    def _check_configuration(self, configuration: dict[str, Any]) -> None:
        if "host" not in configuration:
            raise ConfigurationError("Missing configuration key: 'host'")
        if "token" not in configuration:
            raise ConfigurationError("Missing configuration key: 'token'")
        if "verify_ssl" in configuration and not isinstance(
            configuration["verify_ssl"], bool
        ):
            raise ConfigurationError("Configuration key 'verify_ssl' must be a boolean")

    def configure(self, configuration: dict[str, Any]) -> None:
        self._check_configuration(configuration)
        host = str(configuration["host"]).rstrip("/")
        if not urlparse(host).scheme:
            host = f"http://{host}"
        self.host = host
        self.token = str(configuration["token"])
        self.verify_ssl = configuration.get("verify_ssl", True)

    def _ssl_context(self) -> ssl.SSLContext | None:
        if urlparse(self.host).scheme == "https" and not self.verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        return None

    def _request_json(self, path: str) -> Any:
        request = Request(
            f"{self.host}{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; upstate)",
            },
        )

        try:
            with urlopen(request, context=self._ssl_context(), timeout=30) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError(
                    "Could not authenticate with Home Assistant token"
                ) from exc
            raise

    def check_for_update(self) -> CheckResult:
        self.logger.info("Checking Home Assistant at %s", self.host)
        states = self._request_json("/api/states")
        if not isinstance(states, list):
            raise ValueError("Unexpected response from Home Assistant '/api/states'")

        all_update_entities = [
            state
            for state in states
            if str(state.get("entity_id", "")).startswith("update.")
        ]
        active_update_entities = [
            state for state in all_update_entities if state.get("state") == "on"
        ]

        if not all_update_entities:
            self.logger.info("No Home Assistant update entities found")
            return CheckResult(updates=[])

        items = [
            item
            for state in active_update_entities
            if (item := _make_update_item(state))
        ]

        if not items:
            self.logger.info("No Home Assistant updates available")
        else:
            for item in items:
                self.logger.info(
                    "%s (%s -> %s)", item.name, item.current_version, item.new_version
                )

        return CheckResult(updates=items)
