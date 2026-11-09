"""Compartilha o painel por um hostname Cloudflare estavel."""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

PASTA = Path(__file__).resolve().parent
NOME_TUNEL = "assistente-web"
URL_LOCAL = "http://127.0.0.1:5050/login"
UUID_TUNEL = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
HOSTNAME = re.compile(
    r"(?=.{1,253}\Z)"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)"
    r"(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))+\Z"
)


def encontrar_cloudflared() -> str | None:
    candidatos = (
        shutil.which("cloudflared"),
        str(Path("C:/Program Files (x86)/cloudflared/cloudflared.exe")),
        str(Path("C:/Program Files/cloudflared/cloudflared.exe")),
        str(Path.home() / "AppData/Local/Microsoft/WinGet/Links/cloudflared.exe"),
    )
    return next((p for p in candidatos if p and Path(p).is_file()), None)


def validar_hostname(hostname: str) -> str:
    hostname = hostname.strip().lower().rstrip(".")
    if not HOSTNAME.fullmatch(hostname):
        raise ValueError(
            "Informe um endereco completo, como assistente.seudominio.com, "
            "sem https:// nem barras."
        )
    return hostname


def obter_ou_criar_tunel(executavel: str) -> str:
    lista = subprocess.run(
        [executavel, "tunnel", "list", "--output", "json"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    tunel_existente = next(
        (t for t in json.loads(lista.stdout) if t.get("name") == NOME_TUNEL),
        None,
    )
    if tunel_existente:
        return tunel_existente["id"]

    criado = subprocess.run(
        [executavel, "tunnel", "create", NOME_TUNEL],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    correspondencia = UUID_TUNEL.search(criado.stdout + "\n" + criado.stderr)
    if not correspondencia:
        raise RuntimeError("O Cloudflare criou o tunel, mas nao retornou seu identificador.")
    return correspondencia.group(0)


def criar_configuracao(hostname: str, id_tunel: str, diretorio_cloudflare: Path) -> Path:
    credenciais = diretorio_cloudflare / f"{id_tunel}.json"
    if not credenciais.is_file():
        raise FileNotFoundError(
            f"Credencial do tunel nao encontrada: {credenciais}. "
            "Verifique o login Cloudflare."
        )
    caminho = diretorio_cloudflare / "assistente-web.yml"
    caminho.write_text(
        f"tunnel: {id_tunel}\n"
        f"credentials-file: {json.dumps(credenciais.as_posix())}\n"
        "ingress:\n"
        f"  - hostname: {hostname}\n"
        "    service: http://127.0.0.1:5050\n"
        "  - service: http_status:404\n",
        encoding="utf-8",
    )
    return caminho


def obter_hostname(caminho_config: Path) -> str | None:
    if not caminho_config.is_file():
        return None
    conteudo = caminho_config.read_text(encoding="utf-8")
    encontrado = re.search(r"(?m)^\s+-\s+hostname:\s*(\S+)\s*$", conteudo)
    return encontrado.group(1) if encontrado else None


def painel_respondendo() -> bool:
    try:
        with urlopen(URL_LOCAL, timeout=2) as resposta:
            return resposta.status == 200
    except (OSError, URLError):
        return False


def aguardar_painel(processo: subprocess.Popen | None):
    for _ in range(60):
        if painel_respondendo():
            return
        if processo is not None and processo.poll() is not None:
            raise RuntimeError("O painel encerrou antes de ficar disponivel.")
        time.sleep(1)
    raise TimeoutError("O painel nao ficou disponivel em http://localhost:5050.")


def executar():
    executavel = encontrar_cloudflared()
    if not executavel:
        raise FileNotFoundError(
            "cloudflared nao encontrado. Instale-o pelo menu do INICIAR.bat "
            "ou com winget install -e --id Cloudflare.cloudflared."
        )

    diretorio_cloudflare = Path.home() / ".cloudflared"
    caminho_config = diretorio_cloudflare / "assistente-web.yml"
    hostname = obter_hostname(caminho_config)
    if not hostname:
        print(
            "Para criar um link estavel, primeiro registre um dominio e "
            "configure-o na sua conta Cloudflare."
        )
        hostname = validar_hostname(input("Endereco desejado (ex.: assistente.seudominio.com): "))
        confirmar = input(
            "Confirme que esse dominio ja esta ativo na Cloudflare (s/n): "
        ).strip().casefold()
        if confirmar != "s":
            print("Configure o dominio na Cloudflare antes de continuar.")
            return

        diretorio_cloudflare.mkdir(parents=True, exist_ok=True)
        subprocess.run([executavel, "tunnel", "login"], check=True)
        id_tunel = obter_ou_criar_tunel(executavel)
        subprocess.run(
            [executavel, "tunnel", "route", "dns", NOME_TUNEL, hostname],
            check=True,
        )
        caminho_config = criar_configuracao(hostname, id_tunel, diretorio_cloudflare)
        print(f"Endereco permanente: https://{hostname}")
    else:
        validar_hostname(hostname)
        print(f"Reutilizando endereco permanente: https://{hostname}")

    processo_painel = None
    if not painel_respondendo():
        processo_painel = subprocess.Popen(
            [sys.executable, str(PASTA / "painel.py"), "--sem-navegador"],
            cwd=PASTA,
        )

    try:
        aguardar_painel(processo_painel)
        print(
            "Painel e tunel ativos. Mantenha esta janela e o computador ligados. "
            "Pressione Ctrl+C para encerrar.",
            flush=True,
        )
        subprocess.run(
            [
                executavel, "--config", str(caminho_config),
                "tunnel", "run", NOME_TUNEL,
            ],
            check=True,
        )
    finally:
        if processo_painel is not None and processo_painel.poll() is None:
            processo_painel.terminate()
            try:
                processo_painel.wait(timeout=10)
            except subprocess.TimeoutExpired:
                processo_painel.kill()
                processo_painel.wait()


if __name__ == "__main__":
    try:
        executar()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Falha ao iniciar link permanente: {exc}", file=sys.stderr)
        sys.exit(1)
