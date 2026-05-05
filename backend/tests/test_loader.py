import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from upstate.homeassistant import HomeAssistantChecker
from upstate.loader import load_checkers_from_yaml
from upstate.truenas.apps import TrueNASAppsChecker
from upstate.truenas.system import TrueNASChecker


class LoadCheckersFromYamlTests(unittest.TestCase):
    def test_loads_system_and_app_checkers(self) -> None:
        config = """
checkers:
  - type: truenas
    host: nas.local
    api_key: secret
  - type: truenas-apps
    host: apps.local
    api_key: another-secret
"""

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config)

            checkers = load_checkers_from_yaml(config_path)

        self.assertEqual(
            [type(checker) for checker in checkers],
            [TrueNASChecker, TrueNASAppsChecker],
        )
        self.assertEqual(checkers[0].uri, "wss://nas.local/api/current")
        self.assertEqual(checkers[1].uri, "wss://apps.local/api/current")

    def test_resolves_environment_variables_for_app_checker(self) -> None:
        config = """
checkers:
  - type: truenas-apps
    host: ${TRUENAS_HOST}
    api_key: ${TRUENAS_API_KEY}
"""

        env_file = "TRUENAS_HOST=env.local\nTRUENAS_API_KEY=env-secret\n"

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".env").write_text(env_file)
            config_path = root / "config.yaml"
            config_path.write_text(config)

            checkers = load_checkers_from_yaml(config_path)

        self.assertEqual(len(checkers), 1)
        self.assertIsInstance(checkers[0], TrueNASAppsChecker)
        self.assertEqual(checkers[0].uri, "wss://env.local/api/current")
        self.assertEqual(checkers[0].api_key, "env-secret")

    def test_loads_verify_ssl_when_disabled(self) -> None:
        config = """
checkers:
  - type: truenas
    host: nas.local
    api_key: secret
    verify_ssl: false
"""

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config)

            checkers = load_checkers_from_yaml(config_path)

        self.assertEqual(len(checkers), 1)
        self.assertIsInstance(checkers[0], TrueNASChecker)
        self.assertFalse(checkers[0].verify_ssl)

    def test_loads_homeassistant_checker(self) -> None:
        config = """
checkers:
  - type: homeassistant
    host: https://homeassistant.local:8123
    token: secret-token
    verify_ssl: false
"""

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config)

            checkers = load_checkers_from_yaml(config_path)

        self.assertEqual(len(checkers), 1)
        self.assertIsInstance(checkers[0], HomeAssistantChecker)
        self.assertEqual(checkers[0].host, "https://homeassistant.local:8123")
        self.assertEqual(checkers[0].token, "secret-token")
        self.assertFalse(checkers[0].verify_ssl)

    def test_resolves_environment_variables_for_homeassistant_checker(self) -> None:
        config = """
checkers:
  - type: homeassistant
    host: ${HOMEASSISTANT_URL}
    token: ${HOMEASSISTANT_TOKEN}
"""

        env_file = (
            "HOMEASSISTANT_URL=https://homeassistant.local:8123\n"
            "HOMEASSISTANT_TOKEN=ha-secret-token\n"
        )

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".env").write_text(env_file)
            config_path = root / "config.yaml"
            config_path.write_text(config)

            checkers = load_checkers_from_yaml(config_path)

        self.assertEqual(len(checkers), 1)
        self.assertIsInstance(checkers[0], HomeAssistantChecker)
        self.assertEqual(checkers[0].host, "https://homeassistant.local:8123")
        self.assertEqual(checkers[0].token, "ha-secret-token")


if __name__ == "__main__":
    unittest.main()
