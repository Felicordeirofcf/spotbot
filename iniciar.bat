@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem Descobre o Python (launcher "py" ou "python")
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (python --version >nul 2>&1 && set "PY=python")
if not defined PY (
  echo.
  echo  Python nao encontrado.
  echo  Instale o Python 3.10 ou mais novo em https://www.python.org/downloads/
  echo  e marque a opcao "Add python.exe to PATH" na instalacao.
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente e instalando dependencias...
  %PY% -m venv .venv || (echo Falha ao criar o ambiente virtual & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo Falha ao instalar dependencias & pause & exit /b 1)
)
if not exist ".env" copy ".env.example" ".env" >nul

start "" http://127.0.0.1:8765
".venv\Scripts\python.exe" -m bot ui
pause
