"""Локальный API: импорт, сохранённые проекты, пересчёт и экспорт."""
from io import BytesIO
import os
from pathlib import Path
import secrets
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook
from pydantic import BaseModel, Field
from .storage import get_project, list_projects, save_project
from .services.analysis import import_project, analyze_project

app = FastAPI(title='ВТД Аналитика', version='0.2.0')


@app.middleware('http')
async def local_session(request: Request, call_next):
    token = os.environ.get('VTD_SESSION_TOKEN')
    if token and request.url.path.startswith('/api/'):
        if not secrets.compare_digest(request.headers.get('X-VTD-Session',''), token):
            return JSONResponse({'detail':'Недействительный локальный сеанс'}, status_code=403)
    return await call_next(request)


@app.get('/health')
@app.get('/api/health')
def health():
    return {'status':'ok', 'mode':'local', 'excel_import_connected':True,
            'calculations_connected':True, 'version':'0.2.0'}


def public(project):
    return {k:v for k,v in project.items() if k != 'tables'}


def require_project(project_id):
    p = get_project(project_id)
    if p is None: raise HTTPException(404, 'Проект не найден')
    return p


@app.get('/api/projects')
def projects():
    return list_projects()


@app.get('/api/projects/{project_id}')
def project(project_id: str):
    return public(require_project(project_id))


@app.post('/api/import')
def import_excel(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(422, 'Поддерживается .xlsx. Сохраните старый .xls в формате .xlsx.')
    data = file.file.read(50 * 1024 * 1024 + 1)
    if not data or len(data) > 50 * 1024 * 1024:
        raise HTTPException(422, 'Файл пустой или превышает 50 МБ')
    try:
        p = import_project(data, Path(file.filename).name)
        save_project(p)
        return public(p)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(422, str(e)) from e


@app.post('/api/projects/{project_id}/recalculate')
def recalculate(project_id: str):
    p = analyze_project(require_project(project_id))
    save_project(p)
    return public(p)


@app.get('/api/projects/{project_id}/export')
def export(project_id: str):
    p = require_project(project_id)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Результаты'
    ws.append(['ID','Строка anom','Труба','Тип','Длина, мм','Ширина, мм','Глубина, мм',
               'Разрушающее давление, МПа','Категория (предварительная)','Статус','Сообщения'])
    for d in p['defects']:
        r = d['result']
        ws.append([d['sourceId'],d['source']['row'],d['pipeNumber'],d['kind'],d['lengthMm'],d['widthMm'],d['depthMm'],
                   r['pressureMpa'],r['category'],r['status'],'; '.join(r['messages'])])
        for c in ws[ws.max_row]:
            if isinstance(c.value,str): c.data_type = 's'
            if isinstance(c.value,float): c.number_format = '0.000000'
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    info = wb.create_sheet('Условия расчёта')
    for line in [p['name'],p['sha256'],*p['assumptions']]: info.append([line])
    stream = BytesIO()
    wb.save(stream)
    return Response(stream.getvalue(), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition':'attachment; filename="vtd-results.xlsx"'})


class DentAssessment(BaseModel):
    evidence: str = Field(min_length=10, max_length=2000)


@app.post('/api/projects/{project_id}/dents/{defect_id}/rm3')
def assess_dent(project_id: str, defect_id: str, assessment: DentAssessment):
    p=require_project(project_id)
    d=next((d for d in p['defects'] if d['id']==defect_id and d['kind']=='dent'),None)
    if d is None:raise HTTPException(404,'Вмятина не найдена')
    if len(assessment.evidence.strip())<10:raise HTTPException(422,'Укажите документальное основание')
    p.setdefault('dentAssessments',{})[defect_id]={'evidence':assessment.evidence.strip()}
    p=analyze_project(p)
    save_project(p)
    return public(p)


static = Path(os.environ.get('VTD_STATIC_DIR', Path(__file__).resolve().parents[2] / 'frontend/dist'))
if static.is_dir():
    app.mount('/', StaticFiles(directory=static, html=True), name='frontend')
