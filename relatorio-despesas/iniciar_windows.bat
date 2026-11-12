@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo Núcleo Service - Sistema de Relatório Web
if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    if errorlevel 1 (
        echo Instale Python 3.11+ antes de continuar.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo Não foi possível instalar as dependências. Verifique a conexão com a internet.
    pause
    exit /b 1
)
if "%ADMIN_PASSWORD%"=="" (
    echo Digite uma senha de administrador. Ela será usada só nesta sessão.
    set /p ADMIN_PASSWORD=Senha:
)
echo.
echo Abra: http://127.0.0.1:5000
python app.py
pause
