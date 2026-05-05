from truenas_api_client import Client
from websocket import WebSocketAddressException

from ..interface import CheckerConnectionError, CheckResult, UpdateItem
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
                boot_envs = c.call("boot.environment.query")
        except WebSocketAddressException as e:
            raise CheckerConnectionError(f"Invalid address: {self.uri}") from e

        def parse_version(env):
            try:
                return tuple(int(x) for x in env["id"].split("."))
            except ValueError:
                return (0,)

        current = next(env for env in boot_envs if env["active"])
        current_version = parse_version(current)

        newer = [env for env in boot_envs if parse_version(env) > current_version]

        if newer:
            latest = max(newer, key=parse_version)
            return CheckResult(
                updates=[
                    UpdateItem(
                        name="TrueNAS",
                        current_version=current["id"],
                        new_version=latest["id"],
                    )
                ]
            )

        return CheckResult(updates=[])
