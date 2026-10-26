"""Logging and console helpers for markdown_redactor."""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Configure rich logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    return logging.getLogger("markdown_redactor")
