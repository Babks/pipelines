"""Separate future TZ 2025 layer. No category inferred from demo fixtures."""
from .contracts import NotConnectedResult


# Будущий отдельный слой категорирования по ТЗ. Не использует demoCategory и не назначает A/B/C.
def categorize() -> NotConnectedResult:
    return NotConnectedResult()
