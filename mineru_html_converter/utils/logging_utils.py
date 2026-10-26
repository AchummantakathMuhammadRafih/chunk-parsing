"""Logging setup with Rich terminal formatting."""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()

def setup_logger(verbose: bool = False) -> logging.Logger:
    """Setup and configure a logger instance."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
        force=True
    )
    return logging.getLogger("mineru_html_converter")

logger = setup_logger()
