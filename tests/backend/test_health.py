from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.corrosion import calculate_single
from backend.app.services.groups import calculate_group
from backend.app.services.dents import calculate_dent
from backend.app.services.categorization import categorize
from backend.app.services.excel_import import import_workbook
from backend.app.services.contracts import CalculationNotConnectedError
from pathlib import Path
import pytest


# TestClient вызывает приложение внутри тестового процесса; отдельный порт 8000 и uvicorn не требуются.
def test_health_reports_local_services():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json()['mode'] == 'local'
    assert response.json()['excel_import_connected'] is True


# Один тест запускается для четырёх заглушек. Проверяет контракт отсутствующего результата, а не инженерную точность.
@pytest.mark.parametrize('calculate', [calculate_single, calculate_group, calculate_dent, categorize])
def test_stubs_never_produce_pressure_or_final_category(calculate):
    result = calculate()
    assert result.status == 'not_connected'
    assert result.pressure_mpa is None
    assert result.final_category is None


# pytest.raises проверяет, что импорт честно отказывает, а не сообщает об успешной проверке.
def test_import_does_not_claim_validation():
    with pytest.raises(CalculationNotConnectedError, match='не проверено'):
        import_workbook(Path('not-an-excel.xlsx'))
