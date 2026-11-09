$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Encontrar-Python {
    # Versao ausente faz o py escrever no stderr; com 'Stop' isso viraria erro fatal.
    $ErrorActionPreference = 'Continue'
    $candidatos = @()
    foreach ($nome in @('python','python3')) {
        $cmd = Get-Command $nome -ErrorAction SilentlyContinue
        if ($cmd) { $candidatos += $cmd.Source }
    }
    foreach ($versao in @('313','312','311')) {
        $candidatos += "$env:LOCALAPPDATA\Programs\Python\Python$versao\python.exe"
        $candidatos += "$env:ProgramFiles\Python$versao\python.exe"
    }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($versao in @('3.13','3.12','3.11')) {
            $resultado = & $launcher.Source "-$versao" -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0) { $candidatos += $resultado }
        }
    }
    foreach ($candidato in $candidatos | Select-Object -Unique) {
        if (Test-Path $candidato) {
            & $candidato -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidato }
        }
    }
    return $null
}
try {
    $pythonLocal = Encontrar-Python
    if (-not $pythonLocal) {
        Write-Host '[1/3] Instalando Python para este usuario...'
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            throw 'Instale o Instalador de Aplicativo (App Installer) pela Microsoft Store e abra INICIAR novamente. O winget nao esta disponivel.'
        }
        & winget install --exact --id Python.Python.3.13 --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar Python. Verifique a internet e as mensagens acima.' }
        $pythonLocal = Encontrar-Python
        if (-not $pythonLocal) { throw 'Python instalado, mas nao localizado. Feche a janela e execute INICIAR novamente.' }
    }
    Write-Host '[2/3] Verificando ambiente local...'
    $venvPython = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
    $valido = $false
    if (Test-Path $venvPython) {
        & $venvPython -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' 2>$null
        $valido = $LASTEXITCODE -eq 0
    }
    if (-not $valido) {
        if (Test-Path 'venv') { Move-Item 'venv' ("venv-antigo-" + [guid]::NewGuid().ToString('N')) }
        & $pythonLocal -m venv venv
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente Python.' }
    }
    Write-Host '[3/3] Verificando bibliotecas e navegador...'
    & $venvPython preparar.py
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar dependencias. Corrija o erro mostrado e execute INICIAR para tentar novamente.' }
    exit 0
} catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
