from enum import Enum
from typing import Any

from pydantic import BaseModel
from truenas_api_client import JSONRPCClient


class UpdateStatusCode(str, Enum):
    NORMAL = "NORMAL"
    ERROR = "ERROR"


class UpdateStatusStatusCurrentVersion(BaseModel):
    train: str
    profile: str
    matches_profile: bool


class UpdateStatusStatusNewVersion(BaseModel):
    version: str
    manifest: dict[str, Any]
    release_notes: str | None
    release_notes_url: str


class UpdateStatusStatus(BaseModel):
    current_version: UpdateStatusStatusCurrentVersion
    new_version: UpdateStatusStatusNewVersion | None


class UpdateStatusError(BaseModel):
    errname: str
    reason: str


class UpdateStatusUpdateDownloadProgress(BaseModel):
    percent: str
    description: str
    version: str


class UpdateStatus(BaseModel):
    code: UpdateStatusCode
    status: UpdateStatusStatus | None
    error: UpdateStatusError | None
    update_download_progress: UpdateStatusUpdateDownloadProgress | None

    @classmethod
    def call(cls, client: JSONRPCClient) -> "UpdateStatus":
        return cls(**client.call("update.status"))
