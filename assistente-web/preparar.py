"""Prepara dependencias somente quando faltam ou mudaram. Sem rede no uso normal."""
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import importlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def verificar_dependencia(modulo: str, pacote: str, versao: str):
    try:
        importlib.import_module(modulo)
    except ImportError:
        print(f"Instalacao incompleta de {pacote}: reparando...", flush=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
             "--force-reinstall", "--no-deps", f"{pacote}=={versao}"],
            check=True,
        )
        importlib.import_module(modulo)


def preparar():
    requisitos = (ROOT / "requirements.txt").read_text().splitlines()
    faltando = []
    versoes = {}
    for linha in requisitos:
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        nome, esperado = linha.split("==", 1)
        versoes[nome] = esperado
        try:
            instalado = version(nome)
        except PackageNotFoundError:
            instalado = None
        if instalado != esperado:
            faltando.append(linha)
    if faltando:
        print("Primeira configuracao ou dependencias alteradas: instalando...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                        "-r", str(ROOT / "requirements.txt")], check=True)
    verificar_dependencia("cryptography.exceptions", "cryptography", versoes["cryptography"])
    verificar_dependencia("pywintypes", "pywin32", versoes["pywin32"])
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        chromium = Path(pw.chromium.executable_path)
    if not chromium.is_file():
        print("Instalando Chromium (necessario somente na primeira vez)...", flush=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    print("Ambiente pronto.", flush=True)

if __name__ == "__main__":
    try:
        preparar()
    except (subprocess.CalledProcessError, OSError, ImportError) as exc:
        print(f"Falha na preparacao: {exc}", file=sys.stderr)
        sys.exit(1)
