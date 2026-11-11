from typing import Literal
from pydantic import BaseModel


# Общий контракт заглушек. None сериализуется в JSON null; отсутствие результата нельзя заменить нулём.
class NotConnectedResult(BaseModel):
    status: Literal["not_connected"] = "not_connected"
    message: str = "Расчёт не подключён"
    pressure_mpa: None = None
    final_category: None = None


# Собственный тип исключения для неподключённой операции; наследуется от стандартного NotImplementedError.
class CalculationNotConnectedError(NotImplementedError):
    """A future algorithm must never silently return fictitious results."""
