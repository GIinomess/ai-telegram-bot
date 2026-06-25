import sys

import structlog

from src.core.logging import configure_logging

configure_logging()

log = structlog.get_logger(__name__)
log.info("application_ready", stage=1)

sys.exit(0)
