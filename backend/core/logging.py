import logging
import sys
from loguru import logger
from config import settings, Environment
from core.logging_context import get_request_id, get_user_id


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def context_patcher(record):
    """
    Patcher that injects context variables into every log record.
    This runs for EVERY log statement in the application before it reaches any sink.
    """
    record["extra"]["request_id"] = get_request_id() or "no-request-id"
    record["extra"]["user_id"] = get_user_id() or "anonymous"


def setup_logging():
    """
    Configure the logging:
    - Remove default Loguru handler
    - Configure patcher to inject context
    - Add sink based on environment (JSON for prod, colored for dev)
    - Intercept standard library logging
    """
    # Remove all existing handlers
    logger.remove()

    # Configure patcher to always inject context
    logger.configure(patcher=context_patcher)

    if settings.ENVIRONMENT in [Environment.PROD, Environment.UAT]:
        # Production/UAT: Serialize to JSON with context
        logger.add(
            sys.stdout,
            serialize=True,
            level=settings.LOG_LEVEL,
            enqueue=True,  # Async safe
        )
    else:
        # Development: Human readable with context in format string
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <yellow>req:{extra[request_id]}</yellow> | <magenta>user:{extra[user_id]}</magenta> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
        )

    # Intercept everything from standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Specifically for Uvicorn and FastAPI
    for log_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
