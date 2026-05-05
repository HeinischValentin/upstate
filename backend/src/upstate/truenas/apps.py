from truenas_api_client import Client
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
        except WebSocketAddressException as e:
            raise CheckerConnectionError(f"Invalid address: {self.uri}") from e

        updates = [self._make_app_update_item(app) for app in apps]

        if not updates:
            self.logger.info("No app updates available")
        else:
            self.logger.info(
                "App updates available: %s", ", ".join(u.name for u in updates)
            )

        return CheckResult(updates=updates)

    def _make_app_update_item(self, app: dict) -> UpdateItem:
        name = str(app.get("id") or app.get("name") or "unknown")

        metadata = app.get("metadata") or {}
        current = metadata.get("version") or "error"
        new = app.get("latest_version") or "error"

        if "error" in (current, new):
            self.logger.info("Couldn't read version for {name}")

        return UpdateItem(name=name, current_version=str(current), new_version=str(new))
