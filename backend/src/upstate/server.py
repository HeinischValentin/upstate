import argparse
import asyncio
import logging
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .demo import DemoChecker
from .interface import (
    AuthenticationError,
    Checker,
    CheckerConnectionError,
    CheckResult,
    UpdateItem,
)
from .loader import load_checkers_from_yaml

logger = logging.getLogger(__name__)


class CheckerStatus(BaseModel):
    type: str
    update_available: bool
    updates: list[UpdateItem]
    error: str | None = None

    model_config = {"arbitrary_types_allowed": True}


def create_app(checkers: dict[str, Checker]) -> FastAPI:
    app = FastAPI(title="Upstate API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/checkers", response_model=list[str])
    def list_checkers() -> list[str]:
        return list(checkers.keys())

    @app.get("/checkers/{checker_type}", response_model=CheckerStatus)
    async def get_checker(checker_type: str) -> CheckerStatus:
        checker = checkers.get(checker_type)
        if checker is None:
            raise HTTPException(
                status_code=404, detail=f"Unknown checker: {checker_type!r}"
            )
        try:
            result: CheckResult = await asyncio.to_thread(checker.check_for_update)
            return CheckerStatus(
                type=checker_type,
                update_available=result.update_available,
                updates=result.updates,
            )
        except AuthenticationError as e:
            logger.warning("Checker %s: authentication failed: %s", checker_type, e)
            raise HTTPException(status_code=401, detail=str(e))
        except CheckerConnectionError as e:
            logger.error("Checker %s: connection failed: %s", checker_type, e)
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            logger.error("Checker %s failed: %s", checker_type, e)
            raise HTTPException(status_code=500, detail=str(e))

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the upstate API server.")
    parser.add_argument(
        "config", type=Path, help="Path to YAML configuration file.", nargs="?"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Bind port (default: 8000)."
    )
    parser.add_argument(
        "--ssl-certfile", help="Path to SSL certificate file for HTTPS."
    )
    parser.add_argument("--ssl-keyfile", help="Path to SSL private key file for HTTPS.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO).",
    )
    parser.add_argument("--demo", action="store_true", help="Activate demo mode.")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    if args.demo:
        demo_checker1 = DemoChecker()
        demo_checker2 = DemoChecker()
        demo_checker2.timeout = 4
        checkers = {"demo1": demo_checker1, "demo2": demo_checker2}
    else:
        if not args.config:
            logger.error("Missing path to config file!")
            return
        checkers_list = load_checkers_from_yaml(args.config)
        checkers: dict[str, Checker] = {
            c._checker_type or type(c).__name__: c for c in checkers_list
        }
    app = create_app(checkers)

    uvicorn_kwargs: dict[str, Any] = {
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
    }
    if args.ssl_certfile:
        uvicorn_kwargs["ssl_certfile"] = args.ssl_certfile
        uvicorn_kwargs["ssl_keyfile"] = args.ssl_keyfile

    uvicorn.run(app, **uvicorn_kwargs)
