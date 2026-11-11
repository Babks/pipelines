"""Нативное окно приложения. React и API обслуживаются одним локальным процессом.

Порт выделяет ОС, поэтому установленные копии не конфликтуют с портами 8000/5173.
Секрет сеанса защищает локальные API от запросов посторонних веб-страниц.
"""
from pathlib import Path
import os
import secrets
import socket
import sys
import threading
import time


def main():
    import uvicorn
    import webview
    webview.settings['ALLOW_DOWNLOADS'] = True
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    os.environ['VTD_STATIC_DIR'] = str(root / 'frontend' / 'dist')
    if not (root / 'frontend' / 'dist' / 'index.html').exists():
        raise RuntimeError('Сначала соберите frontend: pnpm --dir frontend build')
    token = secrets.token_urlsafe(32)
    os.environ['VTD_SESSION_TOKEN'] = token
    from backend.app.main import app
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_config=None, log_level='warning'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 20
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError('Не удалось запустить локальный сервис')
        time.sleep(.05)
    try:
        # Fragment не отправляется серверу и не попадает в HTTP access log.
        webview.create_window('ВТД Аналитика', f'http://127.0.0.1:{port}/#session={token}',
                              width=1600, height=960, min_size=(1100, 700))
        webview.start(private_mode=True)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()


if __name__ == '__main__':
    main()
