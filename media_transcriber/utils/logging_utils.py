"""Logging and rich terminal styling utilities."""

import logging
from rich.console import Console

console = Console()


def setup_logger(name: str = "media_transcriber", verbose: bool = False) -> logging.Logger:
    """Configure logger with appropriate verbosity."""
    logger = logging.getLogger(name)
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
