import logging
import sys


class QuietPollingFilter(logging.Filter):
    NOISY_SUCCESS_PATHS = (
        "/api/jobs",
        "/api/sources",
        "/api/chat/history",
        "/api/auth/me",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        is_success = any(status in message for status in (" 200 OK", '" 200', '" 204', '" 304'))
        if not is_success:
            return True
        return not any(
            f'"GET {path}' in message or f'"OPTIONS {path}' in message
            for path in self.NOISY_SUCCESS_PATHS
        )


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True,
)

logger = logging.getLogger("app")

logging.getLogger("uvicorn.access").addFilter(QuietPollingFilter())
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
