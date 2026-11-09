@echo off
setlocal
cd /d "%~dp0"
echo.
echo A extensao sera instalada manualmente pelo Chrome.
echo 1. Na pagina chrome://extensions, ative Modo do desenvolvedor.
echo 2. Clique em Carregar sem compactacao.
echo 3. Selecione a pasta extensao_chrome que sera aberta agora.
echo.
start "" "chrome://extensions"
start "" explorer.exe "%~dp0extensao_chrome"
pause
