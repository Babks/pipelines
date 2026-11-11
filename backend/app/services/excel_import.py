"""Future XLSX parsing, anom/weld schema validation and pipe matching."""
from pathlib import Path
from .contracts import CalculationNotConnectedError


# path только описывает будущий вход. Файл не открывается: функция сразу сообщает о неподключённом импорте.
def import_workbook(path: Path) -> None:
    raise CalculationNotConnectedError("Импорт Excel не подключён; содержимое файла не проверено")
