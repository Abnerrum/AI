# ativar_inicio_automatico.ps1 - Registra o painel web para iniciar automaticamente ao ligar o Windows
# Executar com: powershell -ExecutionPolicy Bypass -File ativar_inicio_automatico.ps1

$Pasta = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Pasta "venv\Scripts\pythonw.exe"
$Script = Join-Path $Pasta "painel.py"

if (-not (Test-Path $Python)) {
    Write-Host "ERRO: venv\Scripts\pythonw.exe nao encontrado. Execute o INICIAR.bat primeiro." -ForegroundColor Red
    exit 1
}

$NomeTarefa = "Assistente Nucleo - Painel Web"
$Acao = New-ScheduledTaskAction -Execute "`"$Python`"" -Argument "`"$Script`" --sem-navegador" -WorkingDirectory $Pasta
$Gatilho = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
$Configuracoes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

try {
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $NomeTarefa -Action $Acao -Trigger $Gatilho -Settings $Configuracoes -Principal $Principal -Force | Out-Null
    Write-Host "Tarefa registrada com sucesso: '$NomeTarefa'" -ForegroundColor Green
    Write-Host "O painel web vai iniciar automaticamente quando voce fizer login no Windows." -ForegroundColor Cyan
    Write-Host "Para desativar: schtasks /Delete /TN `"$NomeTarefa`" /F" -ForegroundColor Yellow
} catch {
    Write-Host "ERRO ao registrar a tarefa: $_" -ForegroundColor Red
    exit 1
}
