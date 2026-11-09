"""Painel privado na nuvem com a API de mensagens do Claude."""

import json
import os
import secrets
from collections import deque
from datetime import timedelta
from pathlib import Path
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, session

PASTA_WEB = Path(__file__).resolve().parent / "painel_web"
MODELO = "claude-haiku-5-5"
MAX_RESPOSTA = 512
MAX_TEXTO = 2200
MAX_MENSAGENS = 5
ARQUIVOS = {
    "aquilix-logo.png": "estatico",
    "icone.svg": "estatico",
    "painel.css": "estatico",
    "nuvem.css": "nuvem",
    "chat.js": "nuvem",
}

app = Flask(__name__, static_folder=None, template_folder=str(PASTA_WEB / "nuvem"))
app.config.update(
    SECRET_KEY=secrets.token_hex(32),
    MAX_CONTENT_LENGTH=60 * 1024,
    SESSION_COOKIE_NAME="__Host-aquilix",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=False,
)

trava = Lock()
tentativas_login = deque()
solicitacoes = deque()


def reservar(fila, janela, limite):
    agora = monotonic()
    with trava:
        while fila and agora - fila[0] >= janela:
            fila.popleft()
        if len(fila) >= limite:
            return False
        fila.append(agora)
        return True


def csrf_valido(recebido):
    esperado = session.get("csrf")
    return bool(esperado) and secrets.compare_digest(recebido.encode(), esperado.encode())


@app.after_request
def proteger_resposta(resposta):
    resposta.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; frame-ancestors 'none'; "
        "form-action 'self'; base-uri 'none'"
    )
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    if request.endpoint != "arquivo":
        resposta.headers["Cache-Control"] = "no-store"
    return resposta


@app.get("/assets/<nome>")
def arquivo(nome):
    if nome not in ARQUIVOS:
        abort(404)
    return send_from_directory(PASTA_WEB / ARQUIVOS[nome], nome)


@app.get("/healthz")
def saude():
    return {"ok": True}


@app.route("/", methods=["GET", "POST"])
def painel():
    senha = os.environ.get("AQUILIX_LOGIN_PASSWORD", "")
    pronta = 16 <= len(senha) <= 256
    erro = ""
    status = 200

    if request.method == "POST":
        if not pronta:
            abort(503)
        if not csrf_valido(request.form.get("csrf", "")):
            abort(403)
        if not reservar(tentativas_login, 60, 10):
            erro, status = "Muitas tentativas. Tente novamente em um minuto.", 429
        elif secrets.compare_digest(request.form.get("senha", "").encode(), senha.encode()):
            session.clear()
            session.permanent = True
            session["autorizado"] = True
            session["csrf"] = secrets.token_urlsafe(32)
            return redirect("/")
        else:
            erro, status = "Senha do AQUILIX incorreta.", 401

    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return render_template(
        "chat.html",
        configurado=pronta,
        autorizado=pronta and session.get("autorizado", False),
        claude_ativo=bool(os.environ.get("ANTHROPIC_API_KEY")),
        csrf=session["csrf"],
        erro=erro,
        max_texto=MAX_TEXTO,
    ), status


@app.post("/sair")
def sair():
    if not csrf_valido(request.form.get("csrf", "")):
        abort(403)
    session.clear()
    return redirect("/")


def mensagens_validas(mensagens):
    if not isinstance(mensagens, list) or len(mensagens) not in (1, 3, MAX_MENSAGENS):
        return False
    for indice, mensagem in enumerate(mensagens):
        papel = "assistant" if indice % 2 else "user"
        if not isinstance(mensagem, dict) or set(mensagem) != {"role", "content"}:
            return False
        texto = mensagem["content"]
        if mensagem["role"] != papel or not isinstance(texto, str):
            return False
        if not texto.strip() or len(texto) > MAX_TEXTO:
            return False
    return True


def responder_claude(chave, mensagens):
    requisicao = Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": MODELO,
            "max_tokens": MAX_RESPOSTA,
            "system": "Você é o AQUILIX AI. Responda em português do Brasil, com objetividade.",
            "messages": mensagens,
        }).encode(),
        headers={
            "Authorization": f"Bearer {chave}",
            "anthropic-version": "2026-10-21",
            "Content-Type": "application/json",
        },
    )
    with urlopen(requisicao, timeout=25) as resposta:
        conteudo = json.load(resposta)["content"]
    return "\n".join(bloco["text"] for bloco in conteudo if bloco["type"] == "text")


@app.post("/api/chat")
def conversar():
    if not session.get("autorizado") or not 16 <= len(os.environ.get("AQUILIX_LOGIN_PASSWORD", "")) <= 256:
        return jsonify(erro="Entre no AQUILIX para conversar."), 401
    if not csrf_valido(request.headers.get("X-Aquilix-CSRF", "")):
        return jsonify(erro="Atualize a página antes de enviar."), 403
    chave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not chave:
        return jsonify(erro="Configure a chave da API do Claude no servidor."), 503

    dados = request.get_json(silent=True)
    mensagens = dados.get("mensagens") if isinstance(dados, dict) else None
    if not mensagens_validas(mensagens):
        return jsonify(erro="Envie uma mensagem válida e curta."), 400
    if not reservar(solicitacoes, 86400, 60):
        return jsonify(erro="Limite de solicitações desta instância atingido."), 429

    try:
        texto = responder_claude(chave, mensagens)
    except HTTPError as erro:
        app.logger.warning("Claude API retornou HTTP %d", erro.code)
        if erro.code in (401, 403):
            return jsonify(erro="A Anthropic rejeitou a chave ou o acesso ao modelo."), 502
        if erro.code == 429:
            return jsonify(erro="O Claude atingiu o limite de uso. Tente mais tarde."), 429
        return jsonify(erro="O Claude não conseguiu processar a solicitação."), 502
    except (URLError, TimeoutError, ValueError, KeyError, TypeError):
        app.logger.warning("Falha ao consultar o Claude")
        return jsonify(erro="O Claude está temporariamente indisponível."), 502

    if not texto.strip():
        return jsonify(erro="O Claude não retornou uma resposta em texto."), 502
    return jsonify(resposta=texto)
