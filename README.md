# ВТД Аналитика

Локальное настольное приложение: React + TypeScript + Ant Design в окне pywebview, FastAPI и SQLite. Браузер отдельно запускать не нужно. Рабочий интерфейс получает реальные данные из XLSX; демонстрационные компоненты первого этапа сохранены только для сравнения и не подключены к точке входа.

## Запуск Windows

Нужны Python 3.13, Node.js >=22.12, pnpm и Microsoft Edge WebView2 Runtime. Клонирование репозитория:

```powershell
git clone https://github.com/Babks/pipelines.git
cd pipelines
```

Из папки проекта:

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-desktop.txt
pnpm.cmd --dir frontend install --frozen-lockfile
pnpm.cmd --dir frontend build
.venv/Scripts/python.exe desktop.py
```

Для упаковки: `.venv/Scripts/python.exe build_desktop.py`.
Запуск сборки: `release/VTDAnalytics/VTDAnalytics.exe`. Переносите всю папку VTDAnalytics вместе с `_internal`.

## Запуск Linux

Нужен графический сеанс и системные библиотеки Qt:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-desktop.txt
.venv/bin/python -m pip install 'pywebview[qt]'
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
.venv/bin/python desktop.py
```

Сборка на Linux: `.venv/bin/python build_desktop.py`. Сборка производится на целевой ОС.

## Что работает

- Импорт XLSX с листами anom/weld, проверка колонок, привязки трубы и пропусков. Исходная книга не изменяется.
- Сохранение проектов в SQLite, повторное открытие, пересчёт и экспорт Excel.
- Реестр, поиск, совместные фильтры, сортировка, пагинация, раскрытие групп, карточки с адресами исходных ячеек.
- Одиночная коррозия, пространственная схематизация групп, прогноз с учётом новых взаимодействий.
- РМ3 в доступной области применимости с документальным основанием отсутствия вторичных повреждений. Предварительные A/B требуют РМ2 и не становятся окончательной категорией.

## Алгоритм

1. Прочитать anom/weld, сохранить значения и адреса ячеек; отобрать CORR/DENT.
2. Связать записи по участку, проходу ВТД и трубе. При неоднозначности показать ошибку.
3. Проверить входы и изолированность по осевым/окружным зазорам.
4. Для одиночной коррозии рассчитать коэффициент длины и разрушающее давление. Для группы перебрать окна, проекции и непрерывные комбинации; выбрать минимум.
5. Отдельно вычислить K_STO, допустимое давление, K_TZ и предварительную категорию; выполнить прогноз размеров.
6. Для малой вмятины проверить применимость РМ3, геометрию дуги и предварительную категорию. Недостающие исходные данные не заменять нулями.

Подробности: [алгоритм](docs/Алгоритм.md), [пространственный расчёт](docs/Расчёт_групповых_дефектов.md), [разбор кода](docs/Описание_действующего_кода.md), [проверка старого скрипта](docs/Разбор_старого_скрипта.md).

## Разработка и проверки

Backend отдельно: `.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
Frontend отдельно: `pnpm.cmd --dir frontend dev`.
На Linux замените путь Python на `.venv/bin/python`.

```powershell
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
.venv/Scripts/python.exe -m pytest tests/backend -q
pnpm.cmd --dir frontend build
pnpm.cmd --dir frontend test
pnpm.cmd --dir frontend exec playwright install chromium
pnpm.cmd --dir frontend test:e2e
```


Хранилище Windows: `%LOCALAPPDATA%/VTDAnalytics/projects.sqlite3`; Linux: `~/.local/share/vtd-analytics/projects.sqlite3` (или XDG_DATA_HOME). Переопределение: VTD_DATA_DIR.

Скрипты запуска: Windows — ./start-windows.ps1 -Setup (затем без -Setup); Linux — bash start-linux.sh --setup (затем без --setup). [Сверка методики вмятин](docs/Проверка_расчёта_вмятин.md).

## Структура репозитория

- `frontend/` — React-интерфейс, типы и тесты компонентов.
- `backend/` — API, импорт Excel, расчётные модули и SQLite.
- `docs/` — технические описания; `docs/reference/` — исходные материалы и старый скрипт.
- `tests/` — проверки Python и интеграции API.
- `desktop.py` — запуск настольного окна.
- `build_desktop.py` — сборка приложения для текущей ОС.

Зависимости, результаты сборки, локальные базы и временные файлы исключены через `.gitignore`.
