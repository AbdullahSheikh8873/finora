"""
Application-wide logging configuration.

Never logs passwords, JWT secrets, database credentials, or raw
financial payloads -- only structural/event-level information.
"""
import logging
import sys


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Keep third-party libraries quiet regardless of app debug mode --
    # SQL echo is opt-in separately via SQLALCHEMY_ECHO if ever needed.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO if debug else logging.WARNING)


logger = logging.getLogger("finora")
