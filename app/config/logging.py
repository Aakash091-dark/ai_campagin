# app/config/logging.py

import logging
import sys

import structlog

from app.config.settings import settings


# =========================================================
# CONFIGURE LOGGING
# =========================================================
def setup_logging():

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(
                fmt="iso"
            ),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    print("Logging initialized")


# =========================================================
# GET LOGGER
# =========================================================
def get_logger(name: str = "lemon-ai"):

    return structlog.get_logger(name)