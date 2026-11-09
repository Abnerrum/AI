@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%PATH%;%USERPROFILE%\.local\bin"
call :preparar
if errorlevel 1 goto erro

:menu
echo.
echo  ===== ASSISTENTE WEB =====
echo   1 - Claude Desktop (app, plano GRATIS ou pago)
echo   2 - Claude Code (terminal, plano pago - Pro ou superior)
echo   3 - Copiar e colar JSON (claude.ai ou ChatGPT gratis, sem app)
echo   4 - Abrir site demo (teste)
echo   5 - Painel web neste PC (audio, fotos e prints)
echo   6 - Gerar link para compartilhar o painel (internet)
echo   7 - Link estavel com dominio Cloudflare (PC precisa ficar ligado)
echo   8 - Instalar extensao do Chrome (painel lateral)
echo   0 - Sair
echo.
set "opcao="
set /p opcao="Escolha: "
if "%opcao%"=="1" goto desktop
if "%opcao%"=="2" goto claude
if "%opcao%"=="3" goto copiar
if "%opcao%"=="4" goto demo
if "%opcao%"=="5" goto painel
if "%opcao%"=="6" goto painel_internet
if "%opcao%"=="7" goto painel_permanente
if "%opcao%"=="8" goto extensao_chrome
if "%opcao%"=="0" exit /b
goto menu

:desktop
echo.
echo Feche o Claude Desktop por completo (inclusive o icone perto do relogio).
pause
"venv\Scripts\python.exe" configurar_desktop.py
if errorlevel 1 (
 echo Falha ao configurar o Claude Desktop.
 pause
 goto menu
)
echo.
echo Pronto. Abra o Claude Desktop e entre com sua conta (gratis ou paga).
echo Se nao tiver o app: https://claude.ai/download
echo Numa conversa nova, peca por exemplo: "abre o site X e faz login".
pause
goto menu

:claude
where claude >nul 2>&1
if not errorlevel 1 goto claude_ok
echo Claude Code nao encontrado.
set "inst="
set /p inst="Instalar agora? (s/n): "
if /i "%inst%"=="s" powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
where claude >nul 2>&1
if not errorlevel 1 goto claude_ok
echo Feche esta janela e abra o INICIAR.bat de novo.
pause
goto menu

:claude_ok
call claude mcp remove assistente-web -s user >nul 2>&1
call claude mcp add assistente-web -s user -- "%~dp0venv\Scripts\python.exe" "%~dp0servidor_mcp.py"
if errorlevel 1 (
 echo Falha ao registrar o assistente no Claude.
 pause
 goto menu
)
echo.
echo Assistente ligado. Na primeira vez o Claude pede para entrar na sua conta paga.
echo Usando o modelo Sonnet, que gasta menos que o Opus.
echo Conectado ao seu Chrome (precisa da extensao "Claude" instalada e logada).
echo.
call claude --model sonnet --chrome
goto menu

:copiar
echo.
echo Abra https://claude.ai (ou o ChatGPT), cole o texto de PROMPT_CHATGPT.md
echo e depois cole aqui os comandos JSON que ele responder.
"venv\Scripts\python.exe" assistente.py
goto menu

:demo
start "Site demo" "%~dp0DEMO.bat"
echo Site demo em http://localhost:5000 (login admin / 1234)
goto menu

:painel
echo.
echo Abrindo o painel. Deixe esta janela aberta enquanto usar; feche para desligar.
"venv\Scripts\python.exe" painel.py
goto menu

:painel_internet
where cloudflared >nul 2>&1
if not errorlevel 1 goto painel_tunel
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\cloudflared.exe" goto painel_tunel
if exist "%ProgramFiles(x86)%\cloudflared\cloudflared.exe" goto painel_tunel
if exist "%ProgramFiles%\cloudflared\cloudflared.exe" goto painel_tunel
echo Instalando o cloudflared (tunel seguro https, so na primeira vez)...
winget install -e --id Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
:painel_tunel
echo.
echo Abrindo o painel com acesso pela internet. O link https aparece abaixo em alguns segundos.
echo O link muda cada vez que abrir. Deixe esta janela aberta; feche para desligar o acesso.
"venv\Scripts\python.exe" painel.py --internet
goto menu

:painel_permanente
echo.
echo Necessario: dominio proprio configurado na Cloudflare e computador ligado.
echo O endereco fica estavel; esta opcao inicia ou reutiliza o tunel nomeado.
"venv\Scripts\python.exe" compartilhar_permanente.py
if errorlevel 1 pause
goto menu

:extensao_chrome
call instalar_extensao_chrome.bat
goto menu

:sem_python
echo Python nao encontrado.
set "inst="
set /p inst="Instalar Python 3.13 agora? (s/n): "
if /i not "%inst%"=="s" goto erro
winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
echo Feche esta janela e abra o INICIAR.bat de novo.
pause
exit /b

:erro
echo Falha na instalacao. Confira Python 3.11 a 3.13 e a conexao com a internet.
pause
exit /b 1

:preparar
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
exit /b %errorlevel%
