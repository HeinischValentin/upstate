from truenas_api_client import Client
from websocket import WebSocketAddressException

from ..interface import CheckerConnectionError, CheckerError, CheckResult, UpdateItem
from ..loader import register_checker
from .base import TrueNASCheckerBase


@register_checker("truenas")
class TrueNASChecker(TrueNASCheckerBase):
    def __init__(self) -> None:
        super().__init__(__name__)

    def check_for_update(self) -> CheckResult:
        self.logger.info("Checking TrueNAS at %s", self.uri)
        try:
            with Client(uri=self.uri, verify_ssl=self.verify_ssl) as c:
                self._login(c)
                update_status = c.call("update.status")
                current_version = c.call("system.version_short")
        except WebSocketAddressException as e:
            raise CheckerConnectionError(f"Invalid address: {self.uri}") from e

        return_code = update_status["code"]
        if return_code != "NORMAL":
            error_name = update_status["error"]["errname"]
            error_reason = update_status["error"]["reason"]
            raise CheckerError(f"Got API error: {error_name}: {error_reason}")

        new_version = update_status["status"]["new_version"]
        if new_version is not None:
            version_identifier = new_version["version"]
            return CheckResult(
                updates=[
                    UpdateItem(
                        name="TrueNAS",
                        current_version=current_version,
                        new_version=version_identifier,
                    )
                ]
            )

        return CheckResult(updates=[])
