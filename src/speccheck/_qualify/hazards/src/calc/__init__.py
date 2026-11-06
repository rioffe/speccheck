"""calc: the speccheck golden fixture (see SPEC.md)."""

from .core import add, divide, scale, subtract
from .summary import Summary, summarize

__version__ = "0.1.0"

__all__ = ["Summary", "add", "divide", "scale", "subtract", "summarize"]
