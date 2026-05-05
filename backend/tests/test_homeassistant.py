import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from upstate.homeassistant import HomeAssistantChecker
from upstate.interface import AuthenticationError, ConfigurationError


class HomeAssistantCheckerTests(unittest.TestCase):
    def test_requires_url_and_token(self) -> None:
        checker = HomeAssistantChecker()

        with self.assertRaises(ConfigurationError):
            checker.configure({"token": "secret"})

        with self.assertRaises(ConfigurationError):
            checker.configure({"host": "https://homeassistant.local:8123"})

        with self.assertRaises(ConfigurationError):
            checker.configure(
                {
                    "host": "https://homeassistant.local:8123",
                    "token": "secret",
                    "verify_ssl": "false",
                }
            )

    @patch("upstate.homeassistant.urlopen")
    def test_reports_all_updates_when_available(self, urlopen_mock: MagicMock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            [
                {
                    "entity_id": "update.home_assistant_core_update",
                    "state": "on",
                    "attributes": {
                        "title": "Home Assistant Core Update",
                        "installed_version": "2026.3.0",
                        "latest_version": "2026.3.1",
                    },
                },
                {
                    "entity_id": "update.random_device_update",
                    "state": "on",
                    "attributes": {
                        "friendly_name": "Random Device Update",
                        "installed_version": "1.0.0",
                        "latest_version": "1.0.1",
                    },
                },
                {
                    "entity_id": "sensor.temperature",
                    "state": "21.5",
                    "attributes": {},
                },
            ]
        ).encode()
        urlopen_mock.return_value.__enter__.return_value = response

        checker = HomeAssistantChecker()
        checker.configure(
            {
                "host": "https://homeassistant.local:8123",
                "token": "secret",
            }
        )

        with self.assertLogs("upstate.homeassistant", level="INFO") as logs:
            result = checker.check_for_update()

        self.assertTrue(result)
        request = urlopen_mock.call_args.args[0]
        self.assertEqual(
            request.full_url, "https://homeassistant.local:8123/api/states"
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        log_output = "\n".join(logs.output)
        self.assertIn("Home Assistant Core Update (2026.3.0 -> 2026.3.1)", log_output)
        self.assertIn("Random Device Update (1.0.0 -> 1.0.1)", log_output)

    @patch("upstate.homeassistant.urlopen")
    def test_reports_no_updates_when_core_entities_are_off(
        self, urlopen_mock: MagicMock
    ) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            [
                {
                    "entity_id": "update.home_assistant_core_update",
                    "state": "off",
                    "attributes": {
                        "installed_version": "2026.3.1",
                        "latest_version": "2026.3.1",
                    },
                }
            ]
        ).encode()
        urlopen_mock.return_value.__enter__.return_value = response

        checker = HomeAssistantChecker()
        checker.configure(
            {
                "host": "https://homeassistant.local:8123",
                "token": "secret",
            }
        )

        with self.assertLogs("upstate.homeassistant", level="INFO") as logs:
            result = checker.check_for_update()

        self.assertFalse(result)
        self.assertIn("No Home Assistant updates available", "\n".join(logs.output))

    @patch("upstate.homeassistant.urlopen")
    def test_reports_when_no_update_entities_found(
        self, urlopen_mock: MagicMock
    ) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            [
                {
                    "entity_id": "sensor.temperature",
                    "state": "21.5",
                    "attributes": {},
                }
            ]
        ).encode()
        urlopen_mock.return_value.__enter__.return_value = response

        checker = HomeAssistantChecker()
        checker.configure(
            {
                "host": "https://homeassistant.local:8123",
                "token": "secret",
            }
        )

        with self.assertLogs("upstate.homeassistant", level="INFO") as logs:
            result = checker.check_for_update()

        self.assertFalse(result)
        self.assertIn(
            "No Home Assistant update entities found",
            "\n".join(logs.output),
        )

    @patch("upstate.homeassistant.urlopen")
    def test_authentication_failure_raises_error(self, urlopen_mock: MagicMock) -> None:
        urlopen_mock.side_effect = HTTPError(
            url="https://homeassistant.local:8123/api/states",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )

        checker = HomeAssistantChecker()
        checker.configure(
            {
                "host": "https://homeassistant.local:8123",
                "token": "secret",
            }
        )

        with self.assertRaises(AuthenticationError):
            checker.check_for_update()

    @patch("upstate.homeassistant.ssl.create_default_context")
    @patch("upstate.homeassistant.urlopen")
    def test_disables_ssl_verification_when_configured(
        self,
        urlopen_mock: MagicMock,
        create_default_context_mock: MagicMock,
    ) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps([]).encode()
        urlopen_mock.return_value.__enter__.return_value = response
        ssl_context = MagicMock()
        create_default_context_mock.return_value = ssl_context

        checker = HomeAssistantChecker()
        checker.configure(
            {
                "host": "https://homeassistant.local:8123",
                "token": "secret",
                "verify_ssl": False,
            }
        )

        checker.check_for_update()

        self.assertIs(urlopen_mock.call_args.kwargs["context"], ssl_context)
