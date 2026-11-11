from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from backend.app.main import app

SAMPLE = Path(__file__).resolve().parents[2] / 'docs/reference/received/0936a617-4998-43d9-8020-97b5606c3f69.xlsx'


def test_import_persistence_recalculation_export(tmp_path, monkeypatch):
    monkeypatch.setenv('VTD_DATA_DIR', str(tmp_path))
    client = TestClient(app)
    response = client.post('/api/import', files={'file': ('sample.xlsx', SAMPLE.read_bytes())})
    assert response.status_code == 200, response.text
    project = response.json()
    assert sum(len(d.get('members',[])) or 1 for d in project['defects']) == 61
    d = next(d for d in project['defects'] if d['sourceId'] == '91199328')
    assert abs(d['result']['pressureMpa'] - 13.5950631787) < 1e-8
    assert d['result']['status'] == 'provisional'
    assert d['source']['fields']['osob_dlina']['cell'] == 'AL31'
    assert 'tables' not in project
    restored = client.get('/api/projects/' + project['id']).json()
    assert restored == project
    recalculated = client.post('/api/projects/' + project['id'] + '/recalculate').json()
    assert recalculated['defects'] == project['defects']
    export = client.get('/api/projects/' + project['id'] + '/export')
    wb = load_workbook(BytesIO(export.content), data_only=True)
    assert wb['Результаты'].max_row == len(project['defects'])+1
    row = next(row for row in wb['Результаты'].values if row[0]=='91199328')
    assert isinstance(row[7], float)
    wb.close()


def test_invalid_book_is_not_saved(tmp_path, monkeypatch):
    monkeypatch.setenv('VTD_DATA_DIR', str(tmp_path))
    client = TestClient(app)
    response = client.post('/api/import', files={'file': ('bad.xlsx', b'not a workbook')})
    assert response.status_code == 422
    assert client.get('/api/projects').json() == []


def test_desktop_session_requires_token(monkeypatch):
    monkeypatch.setenv('VTD_SESSION_TOKEN', 'test-secret')
    client = TestClient(app)
    assert client.get('/api/health').status_code == 403
    assert client.get('/api/health', headers={'X-VTD-Session': 'test-secret'}).status_code == 200
