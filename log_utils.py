from loguru import logger
import sys
from pathlib import Path
import logging


class InterceptHandler(logging.Handler):
    def emit(self, record):
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

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)

format_ = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:}</level> | <cyan>{file}</cyan>:<cyan>{' \
          'function}</cyan>:<cyan>[line:{line}]</cyan>  - <level>{message}</level> '
runtime_log_path = Path(Path(sys.argv[0]).parent, "Log", "runtime.log")
error_log_path = Path(Path(sys.argv[0]).parent, "Log", "error.log")
logger.remove(None)
logger.add(sys.stderr, format=format_, level="DEBUG")
logger.add(error_log_path, level="ERROR", encoding="utf-8", format=format_, enqueue=True)
logger.add(runtime_log_path, rotation="18:00", level="DEBUG",
           encoding="utf-8", enqueue=True,
           catch=False,
           format=format_)

log = logger.bind()
