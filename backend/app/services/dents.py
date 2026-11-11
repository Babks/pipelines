"""Future approved RM1/RM2/RM3 models; RM3 must wait for required RM2."""
from .contracts import NotConnectedResult


# Заглушка будущих моделей вмятин; frontend её пока не вызывает, endpoint расчёта не зарегистрирован.
def calculate_dent() -> NotConnectedResult:
    return NotConnectedResult()
