"""
banco.py - Gerenciamento do banco SQLite.
Armazena configuracoes, tarefas, historico e fluxos reutilizaveis.
Nunca armazena senhas.
"""

import sqlite3
import json
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "assistente.db")


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def inicializar():
    """Cria as tabelas se nao existirem."""
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            storage_path TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessao_usuario TEXT NOT NULL,
            acao TEXT NOT NULL,
            comando_json TEXT,
            resultado TEXT,
            erro TEXT,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fluxos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            passos_json TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sessao_usuario TEXT NOT NULL,
            chave_unica TEXT NOT NULL,
            url TEXT,
            status TEXT DEFAULT 'pendente',
            detalhes TEXT,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_lanc_chave
        ON lancamentos(sessao_usuario, chave_unica)
    """)

    conn.commit()
    conn.close()


# --- Sessoes ---

def criar_sessao(usuario: str) -> str:
    """Cria sessao para o usuario e retorna o caminho do storage."""
    if not isinstance(usuario, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", usuario):
        raise ValueError("Usuario deve conter apenas letras, numeros, _ ou - (1 a 64 caracteres).")
    base = os.path.join(os.path.dirname(__file__), "sessoes")
    storage = os.path.join(base, usuario)
    os.makedirs(storage, exist_ok=True)
    conn = conectar()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessoes (usuario, storage_path) VALUES (?, ?)",
            (usuario, storage),
        )
        conn.commit()
    finally:
        conn.close()
    return storage


def listar_sessoes() -> list:
    conn = conectar()
    rows = conn.execute("SELECT usuario, storage_path, criado_em FROM sessoes").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Historico ---

def registrar_historico(usuario: str, acao: str, comando: dict | None = None,
                        resultado: str | None = None, erro: str | None = None):
    """Registra acao no historico SEM armazenar senhas."""
    # Registra metadados, nunca valores de formularios, cookies ou tokens.
    cmd_limpo = json.dumps({"acao": acao, "usuario": usuario}, ensure_ascii=False)
    resultado = "Resultado registrado; consulte a interface." if resultado else None
    erro = "Falha na execucao; consulte a interface." if erro else None

    conn = conectar()
    conn.execute(
        "INSERT INTO historico (sessao_usuario, acao, comando_json, resultado, erro) VALUES (?,?,?,?,?)",
        (usuario, acao, cmd_limpo, resultado, erro),
    )
    conn.commit()
    conn.close()


def consultar_historico(usuario: str, limite: int = 20) -> list:
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM historico WHERE sessao_usuario=? ORDER BY id DESC LIMIT ?",
        (usuario, limite),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Fluxos ---

def salvar_fluxo(nome: str, descricao: str, passos: list):
    conn = conectar()
    conn.execute(
        """INSERT INTO fluxos (nome, descricao, passos_json)
           VALUES (?, ?, ?)
           ON CONFLICT(nome) DO UPDATE SET
             descricao=excluded.descricao,
             passos_json=excluded.passos_json,
             atualizado_em=datetime('now','localtime')""",
        (nome, descricao, json.dumps(passos, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def carregar_fluxo(nome: str) -> dict | None:
    conn = conectar()
    row = conn.execute("SELECT * FROM fluxos WHERE nome=?", (nome,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["passos"] = json.loads(d["passos_json"])
        return d
    return None


def listar_fluxos() -> list:
    conn = conectar()
    rows = conn.execute("SELECT nome, descricao, criado_em, atualizado_em FROM fluxos").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Lancamentos (controle de duplicidade) ---

def lancamento_existe(usuario: str, chave: str) -> bool:
    conn = conectar()
    row = conn.execute(
        "SELECT id FROM lancamentos WHERE sessao_usuario=? AND chave_unica=?",
        (usuario, chave),
    ).fetchone()
    conn.close()
    return row is not None


def registrar_lancamento(usuario: str, chave: str, url: str = "",
                         status: str = "concluido", detalhes: str = ""):
    conn = conectar()
    conn.execute(
        """INSERT INTO lancamentos (sessao_usuario, chave_unica, url, status, detalhes)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(sessao_usuario, chave_unica) DO UPDATE SET
             status=excluded.status, detalhes=excluded.detalhes""",
        (usuario, chave, url, status, detalhes),
    )
    conn.commit()
    conn.close()


# Inicializa ao importar
inicializar()
