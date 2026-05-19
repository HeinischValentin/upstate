import argparse
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from upstate import server


class TestServer(unittest.TestCase):
    def test_multiple_checkers_same_type(self) -> None:
        """Test if multiple checkers of the same type are configured correctly."""
        config = """
checkers:
  - type: truenas
    host: nas.local
    api_key: secret
  - type: truenas
    host: nas2.local
    api_key: another-secret
"""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config)

            with (
                patch("upstate.server.create_app") as create_app_mock,
                patch("upstate.server.parse_args") as parse_args_mock,
                patch("upstate.server.uvicorn.run"),
            ):
                parse_args_mock.return_value = argparse.Namespace(
                    config=config_path,
                    host="0.0.0.0",
                    port="80",
                    log_level="DEBUG",
                    demo=False,
                    ssl_certfile=None,
                )
                server.main()

        actual = list(create_app_mock.call_args[0][0].keys())
        expected = ["truenas", "truenas_1"]
        assert actual == expected
