"""SQLite хранит импортированные проекты между запусками настольного приложения."""
import json
import os
from pathlib import Path
import sqlite3


def data_directory() -> Path:
    override = os.environ.get('VTD_DATA_DIR')
    base = Path(override) if override else (
        Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'VTDAnalytics'
        if os.name == 'nt' else Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'vtd-analytics')
    base.mkdir(parents=True, exist_ok=True)
    return base


def connection():
    db = sqlite3.connect(data_directory() / 'projects.sqlite3', timeout=20)
    db.execute('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL)')
    return db


def save_project(project):
    with connection() as db:
        db.execute('INSERT OR REPLACE INTO projects VALUES (?, ?, ?)',
                   (project['id'], project['name'], json.dumps(project, ensure_ascii=False, allow_nan=False)))


def list_projects():
    with connection() as db:
        return [{'id': r[0], 'name': r[1]} for r in db.execute('SELECT id,name FROM projects ORDER BY rowid DESC')]


def get_project(project_id):
    with connection() as db:
        row = db.execute('SELECT payload FROM projects WHERE id=?', (project_id,)).fetchone()
    return json.loads(row[0]) if row else None
