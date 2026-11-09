"""Comandos seguros do Jarvis adaptados ao painel AQUILIX AI."""

import datetime
import ipaddress
import json
import os
import random
import re
import socket
import subprocess
import webbrowser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


_MESES_PT = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)
_EXTENSOES_AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma"}
_PIADAS = {
    "pt": (
        "Por que o computador foi ao médico? Porque estava com um vírus.",
        "O que o zero disse para o oito? Belo cinto!",
        "Por que o livro de matemática ficou triste? Porque tinha muitos problemas.",
    ),
    "en": (
        "Why did the computer go to the doctor? It had a virus.",
        "Why was the math book sad? It had too many problems.",
        "I told my computer I needed a break. It said: no problem, I will go to sleep.",
    ),
}


def _sem_acentos(texto: str) -> str:
    import unicodedata

    return "".join(
        caractere for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    )


def interpretar(comando: str) -> dict[str, str] | None:
    """Converte fala ou texto em uma ação conhecida, sem executar comandos arbitrários."""
    if not isinstance(comando, str):
        raise ValueError("O comando precisa ser texto.")
    texto = _sem_acentos(comando).lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    if not texto:
        return None

    ingles = bool(re.search(
        r"\b(what|tell|today|time|date|open|play|search|find|joke|"
        r"restart|reboot|shutdown|turn off|remember|note|offline|exit)\b",
        texto,
    ))
    idioma = "en" if ingles else "pt"

    if re.search(r"\b(cancelar|cancele|cancel|abort)\b", texto) and re.search(
        r"\b(desligamento|reinicio|shutdown|restart|reboot)\b", texto
    ):
        return {"acao": "cancelar_desligamento", "consulta": "", "idioma": idioma}
    if re.search(r"\b(reiniciar|reinicie|restart|reboot)\b", texto):
        return {"acao": "reiniciar", "consulta": "", "idioma": idioma}
    if re.search(r"\b(desligar|desligue|shutdown|turn off)\b", texto):
        return {"acao": "desligar", "consulta": "", "idioma": idioma}
    if "wikipedia" in texto:
        consulta = re.sub(
            r"^(.*?\b(?:pesquisar|pesquise|procure|buscar|busque|search|find)\b"
            r".*?\b(?:wikipedia|wikipedia)\b|\bwikipedia\b)",
            "",
            texto,
        ).strip(" :-")
        consulta = re.sub(r"^(sobre|about)\s+", "", consulta)
        if not consulta:
            raise ValueError("Diga o assunto que deseja pesquisar na Wikipédia.")
        return {"acao": "wikipedia", "consulta": consulta, "idioma": idioma}
    if re.search(r"\b(anote|anotar|nota|lembre|lembrete|remember|note)\b", texto):
        consulta = re.sub(
            r"^(por favor\s+)?(anote|anotar|nota|lembre|lembrete|remember|note)"
            r"(\s+para mim)?\s*[:,-]?\s*",
            "",
            texto,
        ).strip()
        if not consulta:
            raise ValueError("Diga o texto que deseja guardar na nota.")
        return {"acao": "anotar", "consulta": consulta, "idioma": idioma}
    if re.search(r"\b(hora|horas|time)\b", texto):
        return {"acao": "hora", "consulta": "", "idioma": idioma}
    if re.search(r"\b(data|date|today|hoje)\b", texto):
        return {"acao": "data", "consulta": "", "idioma": idioma}
    if re.search(r"\b(pi?ada|joke|funny)\b", texto):
        return {"acao": "piada", "consulta": "", "idioma": idioma}
    if re.search(r"\b(captura|capturar|print|screenshot|tela)\b", texto):
        return {"acao": "captura_tela", "consulta": "", "idioma": idioma}
    if re.search(r"\b(musica|music|tocar|toque|play)\b", texto):
        consulta = re.sub(
            r"^(por favor\s+|please\s+)?(toque|tocar|reproduza|reproduzir|"
            r"play)?\s*(a\s+|some\s+)?(musica|music)?\s*",
            "",
            texto,
        ).strip(" :-")
        return {"acao": "musica", "consulta": consulta, "idioma": idioma}
    if re.search(r"\b(google|pesquisar|pesquise|buscar|busque|search)\b", texto):
        consulta = re.sub(
            r"^(.*?\b(?:google|pesquisar|pesquise|buscar|busque|search)\b)",
            "",
            texto,
        ).strip(" :-")
        if not consulta:
            raise ValueError("Diga o que deseja pesquisar.")
        return {"acao": "google", "consulta": consulta, "idioma": idioma}
    if re.search(r"\b(abrir|abra|abre|open)\b", texto):
        consulta = re.sub(r"^(.*?\b(?:abrir|abra|abre|open)\b)", "", texto).strip(" :-")
        if not consulta:
            raise ValueError("Diga o site que deseja abrir.")
        return {"acao": "abrir_site", "consulta": consulta, "idioma": idioma}
    if re.search(r"\b(offline|sair|parar de ouvir|go offline|exit)\b", texto):
        return {"acao": "parar_voz", "consulta": "", "idioma": idioma}
    return None


def resposta_hora(idioma: str = "pt") -> str:
    hora = datetime.datetime.now().strftime("%H:%M")
    return f"The time is {hora}." if idioma == "en" else f"Agora são {hora}."


def resposta_data(idioma: str = "pt") -> str:
    hoje = datetime.date.today()
    if idioma == "en":
        return f"Today is {hoje.strftime('%B')} {hoje.day}, {hoje.year}."
    return f"Hoje é {hoje.day} de {_MESES_PT[hoje.month - 1]} de {hoje.year}."


def resposta_piadas(idioma: str = "pt") -> str:
    return random.choice(_PIADAS["en" if idioma == "en" else "pt"])


def pesquisar_wikipedia(consulta: str, idioma: str = "pt") -> str:
    if not consulta or len(consulta) > 200:
        raise ValueError("A pesquisa deve ter entre 1 e 200 caracteres.")
    lingua = "en" if idioma == "en" else "pt"
    parametros = urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": consulta,
        "gsrlimit": 1,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exchars": 1800,
        "redirects": 1,
        "format": "json",
        "formatversion": 2,
    })
    requisicao = Request(
        f"https://{lingua}.wikipedia.org/w/api.php?{parametros}",
        headers={"User-Agent": "AquilixAI/1.0 (Wikipedia search)"},
    )
    try:
        with urlopen(requisicao, timeout=8) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as erro:
        raise RuntimeError(f"Não foi possível consultar a Wikipédia: {erro}") from erro
    paginas = dados.get("query", {}).get("pages", [])
    if not paginas:
        return "Não encontrei um artigo correspondente na Wikipédia."
    pagina = paginas[0]
    extrato = pagina.get("extract", "").strip()
    if not extrato:
        return "Encontrei o artigo, mas ele não tem um resumo disponível."
    return f"{pagina.get('title', 'Wikipédia')}\n\n{extrato}"


def _abrir_externo(url: str) -> None:
    if not webbrowser.open(url, new=2):
        raise RuntimeError("Não foi possível abrir o navegador deste computador.")


def abrir_site(destino: str) -> str:
    texto = destino.strip()
    atalhos = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
    }
    if _sem_acentos(texto).lower() in atalhos:
        url = atalhos[_sem_acentos(texto).lower()]
    else:
        url = texto if "://" in texto else f"https://{texto}"
    partes = urlsplit(url)
    if (
        partes.scheme not in {"https", "http"}
        or not partes.hostname
        or partes.username is not None
        or partes.password is not None
        or len(url) > 2048
    ):
        raise ValueError("Use um endereço público que comece com http:// ou https://.")
    host = partes.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or "." not in host:
        raise ValueError("Por segurança, só é permitido abrir sites públicos.")
    try:
        enderecos = socket.getaddrinfo(host, partes.port or 443, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError) as erro:
        raise ValueError("Não consegui localizar esse site público.") from erro
    for endereco in enderecos:
        ip = ipaddress.ip_address(endereco[4][0].split("%")[0])
        if not ip.is_global:
            raise ValueError("O endereço aponta para uma rede privada e não pode ser aberto.")
    _abrir_externo(url)
    return url


def pesquisar_google(consulta: str) -> None:
    if not consulta or len(consulta) > 500:
        raise ValueError("A pesquisa deve ter entre 1 e 500 caracteres.")
    _abrir_externo(f"https://www.google.com/search?q={quote(consulta)}")


def _pasta_musicas() -> Path:
    opcoes = [
        Path.home() / "Music",
        Path.home() / "Musica",
        Path.home() / "OneDrive" / "Music",
        Path.home() / "OneDrive" / "Música",
    ]
    return next((pasta for pasta in opcoes if pasta.is_dir()), opcoes[0])


def listar_musicas() -> list[Path]:
    pasta = _pasta_musicas()
    if not pasta.is_dir():
        return []
    return sorted(
        (arquivo for arquivo in pasta.iterdir()
         if arquivo.is_file() and arquivo.suffix.lower() in _EXTENSOES_AUDIO),
        key=lambda arquivo: arquivo.name.casefold(),
    )


def tocar_musica(consulta: str = "") -> Path:
    musicas = listar_musicas()
    if consulta:
        termo = _sem_acentos(consulta).casefold()
        musicas = [
            musica for musica in musicas
            if termo in _sem_acentos(musica.stem).casefold()
        ]
    if not musicas:
        raise FileNotFoundError(
            "Não encontrei essa música na pasta Música deste computador."
            if consulta else "Não encontrei arquivos de áudio na pasta Música."
        )
    musica = random.choice(musicas)
    if os.name == "nt":
        os.startfile(str(musica))
    else:
        subprocess.Popen(["xdg-open", str(musica)])
    return musica


def agendar_energia(acao: str) -> str:
    argumentos = {
        "desligar": ["/s", "/t", "60", "/c", "AQUILIX: desligamento confirmado localmente"],
        "reiniciar": ["/r", "/t", "60", "/c", "AQUILIX: reinício confirmado localmente"],
        "cancelar_desligamento": ["/a"],
    }
    if os.name != "nt":
        raise RuntimeError("Os comandos de energia estão disponíveis somente no Windows.")
    if acao not in argumentos:
        raise ValueError("Comando de energia inválido.")
    subprocess.Popen(["shutdown", *argumentos[acao]], shell=False)
    if acao == "cancelar_desligamento":
        return "O desligamento ou reinício agendado foi cancelado."
    verbo = "desligamento" if acao == "desligar" else "reinício"
    return f"{verbo.capitalize()} agendado para daqui a 60 segundos. Use “cancelar {verbo}” para interromper."
