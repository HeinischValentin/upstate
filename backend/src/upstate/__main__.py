import argparse
import logging
import sys
from pathlib import Path

from .interface import (
    AuthenticationError,
    CheckerConnectionError,
    CheckerError,
    ConfigurationError,
)
from .loader import load_checkers_from_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for available updates.")
    parser.add_argument("config", type=Path, help="Path to YAML configuration file.")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: WARNING).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger("upstate")

    try:
        checkers = load_checkers_from_yaml(args.config)
    except (ConfigurationError, FileNotFoundError) as e:
        logger.error("%s", e)
        sys.exit(1)

    for checker in checkers:
        label = checker._checker_type or type(checker).__name__
        try:
            result = checker.check_for_update()
        except AuthenticationError as e:
            print(f"{label}: authentication error — {e}", file=sys.stderr)
            continue
        except CheckerConnectionError as e:
            print(f"{label}: connection error — {e}", file=sys.stderr)
            continue
        except CheckerError as e:
            print(f"{label}: error — {e}", file=sys.stderr)
            continue
        if result.update_available:
            count = len(result.updates)
            print(f"{label}: {count} update{'s' if count != 1 else ''} available")
            for item in result.updates:
                print(f"  {item.name}: {item.current_version} → {item.new_version}")
        else:
            print(f"{label}: up to date")
