"""
agendador.py - Tarefas automáticas para o painel web.
Dois tipos: horario (HH:MM + dias da semana) e arquivo (monitora pasta por novos arquivos).
"""
import fnmatch
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Callable


_arquivo_config: str | None = None
_callback: Callable[[str, str], None] | None = None
_tarefas: list[dict] = []
_trava = threading.Lock()
_thread: threading.Thread | None = None


def _tarefas_padrao() -> list[dict]:
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    return [
        {
            "id": "frota_diario",
            "nome": "Relatório de frota diário",
            "agente": "frotas",
            "mensagem": (
                "Gere o relatório de controle de frota de hoje. "
                "Siga as regras do controle_frota_cobli.md e use os dados do Cobli "
                "(Trajetos e paradas, Checklists do dia)."
            ),
            "tipo": "horario",
            "horario": "19:30",
            "dias": [1, 2, 3, 4, 5],
            "ativo": False,
            "ultimo_disparo": None,
        },
        {
            "id": "garantia_pdf",
            "nome": "Notas de garantia Samsung (PDF novo)",
            "agente": "financeiro",
            "mensagem": (
                "Novo PDF de fechamento de garantia detectado em Downloads: {arquivo}. "
                "Leia o PDF e, se for um Dados do fechamento de Garantia Samsung, "
                "prepare a emissão da nota seguindo a skill emitir-nota-garantia-samsung. "
                "Aguarde minha confirmação antes de emitir."
            ),
            "tipo": "arquivo",
            "pasta": downloads,
            "padrao": "*.pdf",
            "filtro_numerico": True,
            "ativo": False,
            "ultimo_disparo": None,
            "arquivos_vistos": [],
        },
        {
            "id": "financeiro_clara",
            "nome": "Fatura Clara nova (CSV)",
            "agente": "financeiro",
            "mensagem": (
                "Novo CSV da fatura Clara detectado em Downloads: {arquivo}. "
                "Leia o arquivo e lance todas as compras autorizadas no Conta Azul Pro "
                "seguindo a skill lancar-fatura-clara. "
                "Mostre um resumo do que vai lançar e aguarde minha confirmação."
            ),
            "tipo": "arquivo",
            "pasta": downloads,
            "padrao": "*.csv",
            "palavras_chave": ["clara", "clara-transactions", "clara_transactions"],
            "ativo": False,
            "ultimo_disparo": None,
            "arquivos_vistos": [],
        },
        {
            "id": "financeiro_localiza",
            "nome": "Fatura Localiza nova (XLS)",
            "agente": "financeiro",
            "mensagem": (
                "Nova fatura Localiza detectada em Downloads: {arquivo}. "
                "Leia as abas ALUGUEL, MULTA DE TRÂNSITO e PREFIXAÇÃO DANOS - AVARIAS. "
                "Faça uma análise financeira completa: total por placa, motorista e categoria, "
                "destaque as maiores despesas e qualquer anomalia. "
                "Depois pergunte se deve gerar o BI consolidado."
            ),
            "tipo": "arquivo",
            "pasta": downloads,
            "padrao": "*.xls",
            "palavras_chave": ["localiza", "fatura"],
            "ativo": False,
            "ultimo_disparo": None,
            "arquivos_vistos": [],
        },
        {
            "id": "financeiro_combustivel",
            "nome": "Relatório combustível novo (CSV)",
            "agente": "financeiro",
            "mensagem": (
                "Novo relatório de combustível detectado em Downloads: {arquivo}. "
                "Analise o consumo por veículo e motorista: total abastecido, custo médio por litro, "
                "placas com maior gasto, datas e postos. Destaque qualquer abastecimento suspeito "
                "(valor muito alto, fora do horário, placa sem histórico). "
                "Resuma em tabela e aponte pontos de atenção."
            ),
            "tipo": "arquivo",
            "pasta": downloads,
            "padrao": "*.csv",
            "palavras_chave": ["combustivel", "relatorio-analise-consumo", "historico_consumo", "historico-consumo"],
            "ativo": False,
            "ultimo_disparo": None,
            "arquivos_vistos": [],
        },
        {
            "id": "financeiro_resumo_semanal",
            "nome": "Resumo financeiro semanal",
            "agente": "financeiro",
            "mensagem": (
                "Faça o resumo financeiro da semana. "
                "Verifique: (1) notas de garantia Samsung emitidas e pendentes esta semana, "
                "(2) lançamentos da fatura Clara em aberto no Conta Azul Pro, "
                "(3) chamados TomTickets abertos ou aguardando resposta. "
                "Liste o que está pendente, o que foi concluído e o que precisa de ação hoje."
            ),
            "tipo": "horario",
            "horario": "08:00",
            "dias": [1],
            "ativo": False,
            "ultimo_disparo": None,
        },
    ]


def _carregar() -> list[dict]:
    if not _arquivo_config or not os.path.exists(_arquivo_config):
        return _tarefas_padrao()
    try:
        with open(_arquivo_config, encoding="utf-8") as f:
            dados = json.load(f)
        if isinstance(dados, list):
            return dados
    except (OSError, json.JSONDecodeError) as e:
        logging.warning("Agendador: não carregou agenda: %s", e)
    return _tarefas_padrao()


def _salvar():
    if not _arquivo_config:
        return
    tmp = _arquivo_config + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_tarefas, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _arquivo_config)
    except OSError as e:
        logging.warning("Agendador: não salvou agenda: %s", e)
        try:
            os.remove(tmp)
        except OSError:
            pass


def iniciar(arquivo_config: str, callback: Callable[[str, str], None]):
    global _arquivo_config, _callback, _tarefas, _thread
    _arquivo_config = arquivo_config
    _callback = callback
    _tarefas = _carregar()
    _thread = threading.Thread(target=_loop, daemon=True, name="agendador")
    _thread.start()
    logging.info("Agendador iniciado com %d tarefa(s).", len(_tarefas))


def _loop():
    while True:
        time.sleep(60)
        try:
            _verificar()
        except Exception as e:
            logging.error("Agendador erro no loop: %s", e)


def _verificar():
    agora = datetime.now()
    with _trava:
        tarefas = list(_tarefas)
    for tarefa in tarefas:
        if not tarefa.get("ativo"):
            continue
        try:
            tipo = tarefa.get("tipo", "horario")
            if tipo == "horario":
                _verificar_horario(tarefa, agora)
            elif tipo == "arquivo":
                _verificar_arquivo(tarefa)
        except Exception as e:
            logging.error("Agendador tarefa %s erro: %s", tarefa.get("id"), e)


def _verificar_horario(tarefa: dict, agora: datetime):
    horario = tarefa.get("horario", "19:30")
    try:
        hora, minuto = map(int, horario.split(":"))
    except (ValueError, AttributeError):
        return
    dias = tarefa.get("dias", [1, 2, 3, 4, 5])
    if agora.isoweekday() not in dias:
        return
    if agora.hour != hora or agora.minute != minuto:
        return
    chave = agora.strftime("%Y-%m-%d %H:%M")
    if tarefa.get("ultimo_disparo") == chave:
        return
    tarefa["ultimo_disparo"] = chave
    _salvar()
    logging.info("Agendador disparando: %s", tarefa.get("nome"))
    if _callback:
        _callback(tarefa["agente"], tarefa["mensagem"])


def _verificar_arquivo(tarefa: dict):
    pasta = tarefa.get("pasta", "")
    padrao = tarefa.get("padrao", "*.pdf")
    filtro_numerico = tarefa.get("filtro_numerico", False)
    # palavras_chave: list of lowercase substrings; file name must contain at least one
    palavras_chave: list[str] = [p.lower() for p in tarefa.get("palavras_chave", [])]
    vistos: set[str] = set(tarefa.get("arquivos_vistos", []))

    try:
        nomes = os.listdir(pasta)
    except OSError:
        return

    novos = []
    agora = time.time()
    todos_vistos = set(vistos)
    for nome in nomes:
        nome_lower = nome.lower()
        if not fnmatch.fnmatch(nome_lower, padrao.lower()):
            continue
        if filtro_numerico:
            stem = os.path.splitext(nome)[0]
            if not stem.isdigit():
                continue
        if palavras_chave and not any(p in nome_lower for p in palavras_chave):
            continue
        caminho = os.path.join(pasta, nome)
        todos_vistos.add(caminho)
        if caminho in vistos:
            continue
        try:
            mtime = os.path.getmtime(caminho)
        except OSError:
            continue
        if agora - mtime > 1800:
            continue
        novos.append(caminho)

    if todos_vistos != vistos:
        tarefa["arquivos_vistos"] = list(todos_vistos)[-500:]
        _salvar()

    for caminho in novos:
        logging.info("Agendador novo arquivo: %s", caminho)
        if _callback:
            mensagem = tarefa["mensagem"].replace("{arquivo}", caminho)
            _callback(tarefa["agente"], mensagem)


def listar() -> list[dict]:
    with _trava:
        return [{k: v for k, v in t.items() if k != "arquivos_vistos"} for t in _tarefas]


def obter(tarefa_id: str) -> dict | None:
    with _trava:
        for t in _tarefas:
            if t.get("id") == tarefa_id:
                return {k: v for k, v in t.items() if k != "arquivos_vistos"}
    return None


def salvar_tarefa(tarefa: dict):
    tid = tarefa.get("id")
    with _trava:
        for i, t in enumerate(_tarefas):
            if t.get("id") == tid:
                tarefa.setdefault("arquivos_vistos", t.get("arquivos_vistos", []))
                _tarefas[i] = tarefa
                _salvar()
                return
        _tarefas.append(tarefa)
        _salvar()


def excluir_tarefa(tarefa_id: str) -> bool:
    with _trava:
        for i, t in enumerate(_tarefas):
            if t.get("id") == tarefa_id:
                _tarefas.pop(i)
                _salvar()
                return True
    return False


def executar_agora(tarefa_id: str) -> bool:
    with _trava:
        tarefa = next((t for t in _tarefas if t.get("id") == tarefa_id), None)
    if tarefa is None:
        return False
    if _callback:
        _callback(tarefa["agente"], tarefa["mensagem"])
    return True
