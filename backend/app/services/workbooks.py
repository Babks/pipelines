"""Импорт XLSX с адресами ячеек, типами и построчными ошибками.

Оригинальная книга не изменяется. Формулы во входных колонках не исполняются:
для воспроизводимого расчёта требуются фактические числовые значения выгрузки.
"""
from datetime import date, datetime
from io import BytesIO
from math import isfinite
from zipfile import ZipFile, BadZipFile
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


class WorkbookError(ValueError):
    pass


def read_workbook(data: bytes):
    try:
        with ZipFile(BytesIO(data)) as z:
            if sum(x.file_size for x in z.infolist()) > 250 * 1024 * 1024:
                raise WorkbookError('Распакованная книга превышает 250 МБ')
        wb = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
    except (BadZipFile, OSError, KeyError, ValueError) as e:
        raise WorkbookError(f'Не удалось прочитать XLSX: {e}') from e
    try:
        missing = {'anom', 'weld'} - set(wb.sheetnames)
        if missing:
            raise WorkbookError('Отсутствуют листы: ' + ', '.join(sorted(missing)))
        tables = {}
        for name in ('anom', 'weld'):
            sheet = wb[name]
            rows = sheet.iter_rows()
            header = next(rows, ())
            names = [str(c.value).strip() if c.value is not None else '' for c in header]
            nonempty = [n for n in names if n]
            if len(nonempty) != len(set(nonempty)):
                raise WorkbookError(f'{name}: повторяющиеся названия колонок')
            required = {'n_tube', 'id_mu', 'pass_vtd'} | ({'n_defekta', 'osob_character'} if name == 'anom' else set())
            if required - set(names):
                raise WorkbookError(f'{name}: нет колонок {", ".join(sorted(required-set(names)))}')
            records = []
            for row_number, row in enumerate(rows, start=2):
                if not any(c.value is not None for c in row):
                    continue
                values, sources = {}, {}
                for column_number, (key, cell) in enumerate(zip(names, row), start=1):
                    if not key:
                        continue
                    value = cell.value
                    if isinstance(value, (date, datetime)):
                        value = value.isoformat()
                    if isinstance(value, float) and not isfinite(value):
                        value = None
                    values[key] = value
                    sources[key] = {'sheet': name, 'cell': f'{get_column_letter(column_number)}{row_number}', 'value': value,
                                    'formula': cell.data_type == 'f'}
                values['_excel_row'] = row_number
                values['_sources'] = sources
                records.append(values)
                if len(records) > 100000:
                    raise WorkbookError(f'{name}: более 100000 записей')
            tables[name] = records
        return tables
    finally:
        wb.close()
