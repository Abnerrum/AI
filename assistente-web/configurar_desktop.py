"""
configurar_desktop.py - Registra o assistente no app Claude Desktop (plano gratis ou pago).

Acrescenta "assistente-web" em mcpServers do claude_desktop_config.json,
mantendo o resto do arquivo e guardando um backup.
"""

import glob
import json
import os
import shutil
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))


def pastas_config() -> list[str]:
    candidatas = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages", "Claude_*",
                                        "LocalCache", "Roaming", "Claude"))
    candidatas.append(os.path.join(os.environ.get("APPDATA", ""), "Claude"))
    existentes = [p for p in candidatas if os.path.isdir(p)]
    return existentes or [candidatas[-1]]


def registrar(pasta_config: str) -> str:
    os.makedirs(pasta_config, exist_ok=True)
    arquivo = os.path.join(pasta_config, "claude_desktop_config.json")
    config = {}
    if os.path.exists(arquivo):
        with open(arquivo, encoding="utf-8") as f:
            texto = f.read().strip()
        config = json.loads(texto) if texto else {}
        shutil.copy2(arquivo, arquivo + ".bak")
    config.setdefault("mcpServers", {})["assistente-web"] = {
        "command": os.path.join(PASTA, "venv", "Scripts", "python.exe"),
        "args": [os.path.join(PASTA, "servidor_mcp.py")],
    }
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return arquivo


if __name__ == "__main__":
    pastas = sys.argv[1:] or pastas_config()
    for pasta in pastas:
        print("Configurado:", registrar(pasta))
