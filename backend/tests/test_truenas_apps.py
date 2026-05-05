import unittest
from unittest.mock import MagicMock, patch

from upstate.interface import ConfigurationError
from upstate.truenas.apps import TrueNASAppsChecker
from upstate.truenas.system import TrueNASChecker


class TrueNASAppsCheckerTests(unittest.TestCase):
    def test_requires_host_and_credentials(self) -> None:
        checker = TrueNASAppsChecker()

        with self.assertRaises(ConfigurationError):
            checker.configure({"api_key": "secret"})

        with self.assertRaises(ConfigurationError):
            checker.configure({"host": "nas.local"})

        with self.assertRaises(ConfigurationError):
            checker.configure(
                {"host": "nas.local", "api_key": "secret", "verify_ssl": "false"}
            )

    @patch("upstate.truenas.apps.Client")
    def test_reports_app_updates_when_available(self, client_cls: MagicMock) -> None:
        client = client_cls.return_value.__enter__.return_value
        client.call.side_effect = [
            True,
            [
                {
                    "id": "immich",
                    "version": "1.0.0",
                    "latest_version": "1.1.0",
                    "metadata": {"app_version": "2024.1.0"},
                    "latest_app_version": "2024.2.0",
                }
            ],
        ]

        checker = TrueNASAppsChecker()
        checker.configure({"host": "nas.local", "api_key": "secret"})

        with self.assertLogs("upstate.truenas.apps", level="INFO") as logs:
            result = checker.check_for_update()

        self.assertTrue(result)
        client_cls.assert_called_once_with(
            uri="wss://nas.local/api/current", verify_ssl=True
        )
        client.call.assert_any_call("auth.login_with_api_key", "secret")
        client.call.assert_any_call("app.query", [["upgrade_available", "=", True]])
        self.assertIn("App updates available: immich", "\n".join(logs.output))

    @patch("upstate.truenas.apps.Client")
    def test_reports_no_updates_when_none_available(
        self, client_cls: MagicMock
    ) -> None:
        client = client_cls.return_value.__enter__.return_value
        client.call.side_effect = [True, []]

        checker = TrueNASAppsChecker()
        checker.configure({"host": "nas.local", "api_key": "secret"})

        with self.assertLogs("upstate.truenas.apps", level="INFO") as logs:
            result = checker.check_for_update()

        self.assertFalse(result)
        client_cls.assert_called_once_with(
            uri="wss://nas.local/api/current", verify_ssl=True
        )
        self.assertIn("No app updates available", "\n".join(logs.output))

    @patch("upstate.truenas.apps.Client")
    def test_disables_ssl_verification_when_configured(
        self, client_cls: MagicMock
    ) -> None:
        client = client_cls.return_value.__enter__.return_value
        client.call.side_effect = [True, []]

        checker = TrueNASAppsChecker()
        checker.configure(
            {"host": "nas.local", "api_key": "secret", "verify_ssl": False}
        )

        checker.check_for_update()

        client_cls.assert_called_once_with(
            uri="wss://nas.local/api/current", verify_ssl=False
        )


class TrueNASSystemCheckerTests(unittest.TestCase):
    @patch("upstate.truenas.system.Client")
    def test_system_checker_still_reports_updates(self, client_cls: MagicMock) -> None:
        client = client_cls.return_value.__enter__.return_value
        client.call.side_effect = [
            True,
            [
                {"id": "25.04.0", "active": True},
                {"id": "25.04.1", "active": False},
            ],
        ]

        checker = TrueNASChecker()
        checker.configure({"host": "nas.local", "api_key": "secret"})

        self.assertTrue(checker.check_for_update())
        client_cls.assert_called_once_with(
            uri="wss://nas.local/api/current", verify_ssl=True
        )
        client.call.assert_any_call("boot.environment.query")

    @patch("upstate.truenas.system.Client")
    def test_system_checker_disables_ssl_verification_when_configured(
        self, client_cls: MagicMock
    ) -> None:
        client = client_cls.return_value.__enter__.return_value
        client.call.side_effect = [
            True,
            [
                {"id": "25.04.0", "active": True},
            ],
        ]

        checker = TrueNASChecker()
        checker.configure(
            {"host": "nas.local", "api_key": "secret", "verify_ssl": False}
        )

        self.assertFalse(checker.check_for_update())
        client_cls.assert_called_once_with(
            uri="wss://nas.local/api/current", verify_ssl=False
        )


if __name__ == "__main__":
    unittest.main()
