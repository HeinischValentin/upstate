import http.client
import json
import logging
import socket
import subprocess
import urllib.parse
from typing import Any

from .interface import (
    Checker,
    CheckResult,
    ConfigurationError,
    UpdateItem,
)
from .loader import register_checker


class _UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


@register_checker("docker")
class DockerChecker(Checker):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.socket_path = "/var/run/docker.sock"
        self.regctl_path = "regctl"

    def _check_configuration(self, configuration: dict[str, Any]) -> None:
        for key in ("socket", "regctl_path"):
            if key in configuration and not isinstance(configuration[key], str):
                raise ConfigurationError(f"docker checker: '{key}' must be a string")

    def configure(self, configuration: dict[str, Any]) -> None:
        self._check_configuration(configuration)
        self.socket_path = configuration.get("socket", "/var/run/docker.sock")
        self.regctl_path = configuration.get("regctl_path", "regctl")

    def check_for_update(self) -> CheckResult:
        updates: list[UpdateItem] = []
        containers = self._get_running_containers()

        seen: set[str] = set()
        for container in containers:
            self.logger.debug(f"Checking container {container.get('Names')}")
            image_name: str = container.get("Image", "")
            if not image_name or image_name.startswith("sha256:") or image_name in seen:
                self.logger.debug(f"Skipping {container.get('Names')}")
                continue
            seen.add(image_name)

            local_digest = self._get_local_digest(image_name)
            if local_digest is None:
                self.logger.warning(f"Can't find local digest for image {image_name}.")
                continue

            remote_digest = self._get_remote_digest(image_name)
            if remote_digest is None:
                self.logger.warning(f"Can't find remote digest for image {image_name}.")
                continue

            self.logger.debug(f"Local: {local_digest}")
            self.logger.debug(f"Remote: {remote_digest}")
            if local_digest != remote_digest:
                updates.append(
                    UpdateItem(
                        name=image_name,
                        current_version=local_digest[:19],
                        new_version=remote_digest[:19],
                    )
                )

        return CheckResult(updates)

    def _get_running_containers(self) -> list[dict]:
        conn = _UnixSocketHTTPConnection(self.socket_path)
        conn.request("GET", "/containers/json")
        resp = conn.getresponse()
        return json.loads(resp.read())

    def _get_local_digest(self, image_name: str) -> str | None:
        conn = _UnixSocketHTTPConnection(self.socket_path)
        encoded = urllib.parse.quote(image_name, safe="")
        conn.request("GET", f"/images/{encoded}/json")
        resp = conn.getresponse()
        if resp.status != 200:
            self.logger.debug("Image %s not found in local daemon", image_name)
            return None
        data = json.loads(resp.read())
        repo_digests: list[str] = data.get("RepoDigests", [])
        if not repo_digests:
            self.logger.debug(
                "Image %s has no RepoDigests (locally built?), skipping", image_name
            )
            return None
        # format: "nginx@sha256:abc..." — take the part after "@"
        entry = repo_digests[0]
        return entry.split("@", 1)[1] if "@" in entry else entry

    def _get_remote_digest(self, image_name: str) -> str | None:
        result = subprocess.run(
            [self.regctl_path, "image", "digest", image_name],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.logger.error(
                f"regctl failed for {image_name}: {result.stderr.strip()}"
            )
            return None
        return result.stdout.strip()
