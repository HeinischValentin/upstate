from random import randint
from time import sleep
from typing import Any

from .interface import (
    Checker,
    CheckResult,
    UpdateItem,
)


class DemoChecker(Checker):
    _checker_type = "demo"

    def __init__(self) -> None:
        self.timeout = 2
        self.updates_available = True

    def _check_configuration(self, configuration: dict[str, Any]) -> None:
        pass

    def configure(self, configuration: dict[str, Any]) -> None:
        pass

    def check_for_update(self) -> CheckResult:
        sleep(self.timeout)
        if self.updates_available:
            return CheckResult(
                updates=[
                    UpdateItem(
                        name="nginx",
                        current_version=f"1.{randint(0, 10)}",
                        new_version=f"1.{randint(10, 100)}",
                    ),
                    UpdateItem(
                        name="postgres",
                        current_version=f"1.{randint(0, 10)}",
                        new_version=f"1.{randint(10, 100)}",
                    ),
                ],
            )
        else:
            return CheckResult(updates=[])
