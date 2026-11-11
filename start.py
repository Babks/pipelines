"""Start the local UI and API after installing dependencies (Windows/Linux)."""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser


def main() -> int:
    # argparse читает аргументы командной строки; --no-browser запрещает только автоматическое открытие браузера.
    parser = argparse.ArgumentParser(description="ВТД Аналитика — локальный запуск")
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    # Абсолютная папка start.py: запуск не зависит от текущей директории терминала.
    root = Path(__file__).resolve().parent
    # На Windows и Linux разные пути Python внутри venv; pathlib собирает корректный путь.
    interpreter = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    vite = root / 'frontend/node_modules/vite/bin/vite.js'
    # Поиск node в PATH, а не скачивание или установка Node.js.
    node = shutil.which('node')
    if not interpreter.exists() or not vite.exists() or not node:
        print('Сначала установите Node.js, создайте .venv и установите зависимости по README.md.')
        return 1
    # Проверка занятости обоих loopback-портов до запуска. Между проверкой и запуском возможна гонка с другим процессом; окончательную проверку выполняют сами серверы.
    for port in (8000, 5173):
        with socket.socket() as connection:
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                print(f'Порт {port} занят. Проверьте уже запущенное приложение.')
                return 1
    # Список только созданных этим launcher дочерних процессов для их последующей остановки.
    processes: list[subprocess.Popen] = []
    try:
        # Popen запускает процесс без shell. Аргументы передаются списком, поэтому не интерпретируются как shell-команды. cwd задаёт рабочую папку.
        processes.append(subprocess.Popen([str(interpreter), '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000'], cwd=root))
        # Popen запускает процесс без shell. Аргументы передаются списком, поэтому не интерпретируются как shell-команды. cwd задаёт рабочую папку.
        processes.append(subprocess.Popen([node, str(vite), '--host', '127.0.0.1', '--port', '5173'], cwd=root / 'frontend'))
        ready = False
        # До 60 попыток HTTP-проверки. Это не строго 30 секунд: сетевые тайм-ауты добавляются к паузам.
        for _ in range(60):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError('Один из сервисов завершился при запуске; смотрите сообщение выше.')
            try:
                # Проверяем HTTP-доступность адреса; здесь JSON health не анализируется, в отличие от frontend ServiceStatus.
                with urllib.request.urlopen('http://127.0.0.1:5173', timeout=1):
                    pass
                # Проверяем HTTP-доступность адреса; здесь JSON health не анализируется, в отличие от frontend ServiceStatus.
                with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1):
                    pass
                ready = True
                break
            except OSError:
                time.sleep(.5)
        if not ready:
            raise RuntimeError('Сервисы не запустились в отведённое время.')
        print('ВТД Аналитика: http://127.0.0.1:5173 — Ctrl+C для остановки', flush=True)
        if not args.no_browser:
            webbrowser.open('http://127.0.0.1:5173')
        # poll() возвращает None, пока процесс работает; выход одного сервиса приводит к остановке второго через finally.
        while all(p.poll() is None for p in processes):
            time.sleep(.5)
        raise RuntimeError('Один из сервисов завершился; второй будет остановлен.')
    # Ctrl+C завершает launcher с кодом 0; блок finally всё равно выполняется.
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    # Гарантированная попытка убрать дочерние процессы после ошибки или остановки. terminate, ожидание до 5 секунд, затем kill при зависании.
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# Этот блок выполняется при запуске файла, но не при его импорте. SystemExit передаёт код завершения в оболочку.
if __name__ == '__main__':
    raise SystemExit(main())
