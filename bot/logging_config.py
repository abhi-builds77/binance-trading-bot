import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(order_type: Optional[str] = None, log_dir: str = "logs") -> logging.Logger:
    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Dynamically set the log file name based on the order type (e.g., market_orders.log)
    log_file = f"{order_type.lower()}_orders.log" if order_type else "trading_bot.log"
    log_path = os.path.join(log_dir, log_file)

    # Initialize the main logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to prevent duplicate logs if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define a standard format for all log messages
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup file handler (rotates files if they get larger than 5MB)
    fh = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Setup console handler (prints to the terminal)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # Keep terminal output clean by only showing INFO and above
    ch.setFormatter(fmt)

    # Attach handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Logging initialised → %s", log_path)
    return logger