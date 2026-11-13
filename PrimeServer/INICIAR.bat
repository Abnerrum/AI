@echo off
cd /d "%~dp0"
py -3 manager\app.py
if errorlevel 1 python manager\app.py
pause
