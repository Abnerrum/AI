@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo Nucleo Service - Sistema de Relatorio Web

if exist ".venv\Scripts\python.exe" goto venv_ready

where py >nul 2>nul
if not errorlevel 1 goto create_venv_with_py

where python >nul 2>nul
if errorlevel 1 goto python_missing
python -m venv .venv
if errorlevel 1 goto venv_error
goto venv_ready

:create_venv_with_py
py -m venv .venv
if errorlevel 1 goto venv_error

:venv_ready
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto dependencies_error

if defined ADMIN_PASSWORD goto launch_app
echo Digite uma senha de administrador. Ela sera usada so nesta sessao.
set /p "ADMIN_PASSWORD=Senha: "
if not defined ADMIN_PASSWORD goto password_missing

:launch_app
echo.
echo Abra: http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto app_error
goto finish

:python_missing
echo Python 3.11 ou mais recente nao foi encontrado.
echo Instale o Python e marque a opcao "Add Python to PATH".
goto fail

:venv_error
echo Nao foi possivel criar o ambiente Python.
goto fail

:dependencies_error
echo Nao foi possivel instalar as dependencias. Verifique a conexao com a internet.
goto fail

:password_missing
echo A senha nao pode ficar vazia.
goto fail

:app_error
echo O sistema foi encerrado com erro. Confira as mensagens acima.
goto fail

:fail
pause
exit /b 1

:finish
pause
endlocal
