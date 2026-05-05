import logging
from typing import Any

from truenas_api_client import JSONRPCClient

from ..interface import AuthenticationError, Checker, ConfigurationError


class TrueNASCheckerBase(Checker):
    def __init__(self, logger_name: str) -> None:
        self.logger = logging.getLogger(logger_name)
        self.uri = ""
        self.api_key = ""
        self.username = ""
        self.password = ""
        self.verify_ssl = True

    def _check_configuration(self, configuration: dict[str, Any]) -> None:
        if "host" not in configuration:
            raise ConfigurationError("Missing configuration key: 'host'")
        if "api_key" not in configuration and not (
            "username" in configuration and "password" in configuration
        ):
            raise ConfigurationError(
                "Must provide either 'api_key' or both 'username' and 'password' in configuration"
            )
        if "verify_ssl" in configuration and not isinstance(
            configuration["verify_ssl"], bool
        ):
            raise ConfigurationError("Configuration key 'verify_ssl' must be a boolean")

    def configure(self, configuration: dict[str, Any]) -> None:
        self._check_configuration(configuration)
        self.uri = f"wss://{configuration['host']}/api/current"
        self.api_key = configuration.get("api_key", "")
        self.username = configuration.get("username", "")
        self.password = configuration.get("password", "")
        self.verify_ssl = configuration.get("verify_ssl", True)

    def _login(self, client: JSONRPCClient) -> None:
        if self.api_key:
            if not client.call("auth.login_with_api_key", self.api_key):
                raise AuthenticationError("Could not authenticate with API key")
        elif self.username and self.password:
            if not client.call("auth.login", self.username, self.password):
                raise AuthenticationError(
                    "Could not authenticate with username and password"
                )
        else:
            raise ValueError("configure() not called.")
