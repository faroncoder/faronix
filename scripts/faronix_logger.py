# _script/faronix_logger.py

import logging
import logging.handlers

logger = logging.getLogger("faronix")
logger.setLevel(logging.INFO)

try:
    handler = logging.handlers.SysLogHandler(address="/dev/log")
    formatter = logging.Formatter("[faronix] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
except Exception as e:
    fallback = logging.FileHandler("/tmp/faronix.log")
    fallback.setFormatter(logging.Formatter("[faronix:FALLBACK] %(message)s"))
    logger.addHandler(fallback)
    logger.error(f"⚠️ Could not bind to syslog. Logging to /tmp/faronix.log. Reason: {e}")

def log(msg, level="INFO"):
    logger.log(getattr(logging, level), msg)
    print(f"[faronix:{level}] {msg}")