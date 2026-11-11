"""Future isolated corrosion applicability and STO §6 calculation."""
from .contracts import NotConnectedResult


# Точка будущей реализации одиночной коррозии. Сейчас аргументов и формул нет; возвращается новый объект статуса.
def calculate_single() -> NotConnectedResult:
    return NotConnectedResult()
