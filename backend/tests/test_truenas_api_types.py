import unittest
from typing import Any

from upstate.truenas.api_types import UpdateStatus


class MockTruenasClient:
    def __init__(self, returns: dict[Any, Any]) -> None:
        self.returns = returns

    def call(self, *_args, **_kwargs) -> dict[Any, Any]:
        return self.returns


update_status__update_available = {
    "code": "NORMAL",
    "status": {
        "current_version": {
            "train": "stable",
            "profile": "General",
            "matches_profile": True,
        },
        "new_version": {
            "version": "2.0.0",
            "manifest": {},
            "release_notes": "Some notes",
            "release_notes_url": "https://www.example.com",
        },
    },
    "error": None,
    "update_download_progress": None,
}


class TrueNASAPITypes(unittest.TestCase):
    def test_update_available(self) -> None:
        client = MockTruenasClient(update_status__update_available)
        self.assertEqual(UpdateStatus.call(client).status.new_version.version, "2.0.0")
