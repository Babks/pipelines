param([switch]$Setup)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($Setup) {
    py -3.13 -m venv .venv
    if ($LASTEXITCODE) { throw 'Не удалось создать Python окружение' }
    & .venv/Scripts/python.exe -m pip install -r backend/requirements-desktop.txt
    if ($LASTEXITCODE) { throw 'Ошибка установки Python зависимостей' }
    pnpm.cmd --dir frontend install --frozen-lockfile
    if ($LASTEXITCODE) { throw 'Ошибка установки frontend' }
    pnpm.cmd --dir frontend build
    if ($LASTEXITCODE) { throw 'Ошибка сборки frontend' }
}
& .venv/Scripts/python.exe desktop.py
exit $LASTEXITCODE
