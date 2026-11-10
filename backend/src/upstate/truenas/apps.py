from truenas_api_client import Client, ClientException
from websocket import WebSocketAddressException

from ..interface import CheckerConnectionError, CheckResult, UpdateItem
from ..loader import register_checker
from .base import TrueNASCheckerBase


@register_checker("truenas-apps")
class TrueNASAppsChecker(TrueNASCheckerBase):
    def __init__(self) -> None:
        super().__init__(__name__)

    def check_for_update(self) -> CheckResult:
        self.logger.info("Checking TrueNAS apps at %s", self.uri)
        try:
            with Client(uri=self.uri, verify_ssl=self.verify_ssl) as client:
                self._login(client)
                apps = client.call("app.query", [["upgrade_available", "=", True]])
                updates = [self._make_app_update_item(client, app) for app in apps]
        except WebSocketAddressException as e:
            raise CheckerConnectionError(f"Invalid address: {self.uri}") from e

        if not updates:
            self.logger.info("No app updates available")
        else:
            self.logger.info(
                "App updates available: %s", ", ".join(u.name for u in updates)
            )

        return CheckResult(updates=updates)

    def _make_app_update_item(self, client: Client, app: dict) -> UpdateItem:
        name = str(app.get("id") or app.get("name") or "unknown")

        metadata = app.get("metadata") or {}
        current = str(metadata.get("version") or "error")
        new = str(app.get("latest_version") or "error")

        if "error" in (current, new):
            self.logger.info("Couldn't read version for %s", name)

        return UpdateItem(
            name=name,
            current_version=self._format_version(current, metadata.get("app_version")),
            new_version=self._format_version(
                new, self._get_latest_app_version(client, name, new)
            ),
        )

    def _get_latest_app_version(
        self, client: Client, name: str, chart_version: str
    ) -> str | None:
        """Return the upstream app version of the latest available release.

        `app.query` doesn't expose it, so it's derived from the upgrade summary's
        `latest_human_version`, which has the form `<app_version>_<chart_version>`.
        """
        try:
            summary = client.call("app.upgrade_summary", name)
        except ClientException as e:
            self.logger.info("Couldn't read upgrade summary for %s: %s", name, e)
            return None

        human_version = str((summary or {}).get("latest_human_version") or "")
        suffix = f"_{chart_version}"
        if human_version.endswith(suffix) and len(human_version) > len(suffix):
            return human_version[: -len(suffix)]
        return None

    @staticmethod
    def _format_version(chart_version: str, app_version: str | None) -> str:
        """Return the chart version, followed by the app version if known."""
        if app_version:
            return f"{chart_version} ({app_version})"
        return chart_version
