from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class CheckerError(Exception):
    pass


class AuthenticationError(CheckerError):
    pass


class ConfigurationError(CheckerError):
    pass


class CheckerConnectionError(CheckerError):
    pass


@dataclass
class UpdateItem:
    name: str
    current_version: str
    new_version: str


@dataclass
class CheckResult:
    updates: list[UpdateItem] = field(default_factory=list)

    @property
    def update_available(self) -> bool:
        return bool(self.updates)

    def __bool__(self) -> bool:
        return self.update_available


class Checker(ABC):
    _checker_type: str = ""

    @abstractmethod
    def _check_configuration(self, configuration: dict[str, Any]) -> None: ...

    @abstractmethod
    def configure(self, configuration: dict[str, Any]) -> None: ...

    @abstractmethod
    def check_for_update(self) -> CheckResult: ...
