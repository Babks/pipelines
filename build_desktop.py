"""Сборка нативного приложения на текущей ОС. Запустить после сборки frontend."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
if not (root / 'frontend/dist/index.html').exists():
    raise SystemExit('Сначала выполните pnpm --dir frontend build')
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                '--windowed', '--name', 'VTDAnalytics', '--collect-all', 'webview',
                '--add-data', f'{root / "frontend/dist"}:frontend/dist',
                '--distpath', str(root / 'release'), '--workpath', str(root / '.local/build'),
                str(root / 'desktop.py')], cwd=root, check=True)
