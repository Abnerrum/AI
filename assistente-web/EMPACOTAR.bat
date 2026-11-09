@echo off
rem Gera assistente-web.zip para levar a outro computador, sem venv, sessoes,
rem banco local e relatorios (cookies e dados ficam so neste PC).
cd /d "%~dp0"
set "destino=%~dp0..\assistente-web.zip"
powershell -NoProfile -Command ^
 "$itens = Get-ChildItem -Force | Where-Object { $_.Name -notin @('venv','node_modules','sessoes','relatorios','__pycache__','.pytest_cache') -and $_.Name -notlike 'assistente.db*' };" ^
 "Compress-Archive -Path $itens.FullName -DestinationPath '%destino%' -Force"
if errorlevel 1 (
 echo Falha ao gerar o ZIP.
) else (
 echo Pacote criado: %destino%
 echo Copie para o outro computador, extraia e clique em INICIAR.bat.
)
pause
