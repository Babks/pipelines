# Проверки

`tests/backend/` — pytest для API, импорта, сохранения проектов, расчёта групп, прогноза и РМ3.

Тесты frontend расположены рядом с пакетом для корректного разрешения зависимостей npm/pnpm:
- `frontend/src/__tests__/` — Vitest, фильтры, карточки трёх типов, метаданные файла.
- `frontend/e2e/` — Playwright, реальные действия в Chromium, пагинация, сортировка, фильтры, группы, сохранение выбора и Excel.

Команды из корня: `.venv/Scripts/python.exe -m pytest` (Windows), `.venv/bin/python -m pytest` (Linux).
Из frontend: `pnpm test`, `pnpm test:e2e`. Перед первым E2E: `pnpm exec playwright install chromium` (Linux: `--with-deps`).
