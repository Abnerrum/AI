"""
executor.py - Interpreta e executa comandos JSON.

SEGURANCA:
- Aceita SOMENTE acoes previstas (whitelist).
- NAO executa codigo Python ou comandos de terminal arbitrarios.
- Trata conteudo de sites como dados, nunca como instrucoes.
- Para em caso de ambiguidade e reporta o problema.
"""

import json
import os
import re
from datetime import datetime

import banco
import credenciais
import relatorio
from navegador import Navegador

# Registro de navegadores ativos por usuario
_navegadores: dict[str, Navegador] = {}
_dados = {}
_previa = {}
_confirmar = None

def configurar_confirmacao(callback):
    global _confirmar
    _confirmar = callback

def fechar_todos():
    for usuario, nav in list(_navegadores.items()):
        try:
            nav.fechar()
        except Exception:
            pass
        finally:
            _navegadores.pop(usuario, None)

def _validar(cmd):
    if not isinstance(cmd, dict):
        raise ValueError("Comando deve ser um objeto JSON.")
    acao = cmd.get("acao")
    usuario = cmd.get("usuario", "padrao")
    params = cmd.get("params", {})
    if not isinstance(acao, str) or acao not in ACOES_PERMITIDAS:
        raise ValueError("Acao ausente ou nao permitida.")
    if not isinstance(usuario, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", usuario):
        raise ValueError("Usuario invalido: use letras, numeros, _ ou -.")
    if not isinstance(params, dict):
        raise ValueError("params deve ser um objeto JSON.")
    return acao, usuario, params


# Acoes permitidas (whitelist)
ACOES_PERMITIDAS = {
    "abrir_navegador",
    "fechar_navegador",
    "abrir_url",
    "aguardar_login",
    "extrair_tabela",
    "extrair_com_paginacao",
    "gerar_excel",
    "preencher_formulario",
    "submeter_formulario",
    "verificar_sucesso",
    "screenshot",
    "salvar_fluxo",
    "executar_fluxo",
    "listar_fluxos",
    "historico",
    "status",
    "listar_sessoes",
    "fazer_login",
    "esquecer_login",
    "listar_elementos",
    "ler_pagina",
    "clicar",
    "digitar",
    "pressionar_tecla",
    "selecionar",
    "voltar",
}


def _abrir_se_necessario(usuario: str) -> Navegador:
    if usuario not in _navegadores:
        nav = Navegador(usuario)
        try:
            nav.iniciar(headless=False)
        except Exception:
            try:
                nav.fechar()
            except Exception:
                pass
            raise
        _navegadores[usuario] = nav
    return _navegadores[usuario]


def _obter_nav(usuario: str) -> Navegador:
    """Retorna o navegador ativo do usuario."""
    if usuario not in _navegadores:
        raise RuntimeError(
            f"Navegador nao iniciado para '{usuario}'. "
            f"Execute a acao 'abrir_navegador' primeiro."
        )
    return _navegadores[usuario]


def executar(comando_json: str) -> dict:
    """
    Recebe um JSON de comando e executa a acao correspondente.

    Formato esperado:
    {
        "acao": "nome_da_acao",
        "usuario": "nome_do_usuario",
        "params": { ... }
    }

    Retorna dict com resultado ou erro.
    """
    try:
        cmd = json.loads(comando_json) if isinstance(comando_json, str) else comando_json
        acao, usuario, params = _validar(cmd)
    except (ValueError, TypeError) as e:
        return {"ok": False, "erro": str(e)}

    try:
        resultado = _despachar(acao, usuario, params)
        if isinstance(resultado, dict) and "erro" in resultado:
            return {"ok": False, "acao": acao, **resultado}
        banco.registrar_historico(usuario, acao, cmd, resultado=json.dumps(resultado, default=str))
        return {"ok": True, "acao": acao, "resultado": resultado}
    except Exception as e:
        msg_erro = str(e)
        banco.registrar_historico(usuario, acao, cmd, erro=msg_erro)
        return {"ok": False, "erro": msg_erro, "acao": acao, "tipo": type(e).__name__}


def _despachar(acao: str, usuario: str, params: dict):
    """Despacha a acao para a funcao correta."""

    # --- Navegador ---
    if acao == "abrir_navegador":
        if usuario in _navegadores:
            raise ValueError("Navegador ja aberto para este usuario.")
        nav = Navegador(usuario)
        nav.iniciar(headless=params.get("headless", False))
        _navegadores[usuario] = nav
        return {"msg": f"Navegador aberto para '{usuario}'."}

    if acao == "fechar_navegador":
        nav = _obter_nav(usuario)
        nav.fechar()
        del _navegadores[usuario]
        return {"msg": f"Navegador fechado para '{usuario}'."}

    if acao == "abrir_url":
        nav = _abrir_se_necessario(usuario)
        url = params.get("url")
        if not url:
            raise ValueError("Parametro 'url' e obrigatorio.")
        _previa.pop(usuario, None)
        return nav.abrir_url(url, params.get("esperar_ms", 3000))

    if acao == "aguardar_login":
        nav = _obter_nav(usuario)
        return nav.aguardar_login(params.get("timeout", 300))

    if acao == "screenshot":
        nav = _obter_nav(usuario)
        caminho = nav.screenshot(params.get("nome", "screenshot.png"))
        return {"arquivo": caminho}

    # --- Extracao ---
    if acao == "extrair_tabela":
        _dados.pop(usuario, None)
        nav = _obter_nav(usuario)
        dados = nav.extrair_tabela(
            params.get("seletor", "table"),
            params.get("colunas"),
        )
        _dados[usuario] = dados
        return relatorio.resumo_dados(dados) | {"dados_salvos_localmente": True}

    if acao == "extrair_com_paginacao":
        _dados.pop(usuario, None)
        nav = _obter_nav(usuario)
        dados = nav.extrair_com_paginacao(
            params.get("seletor", "table"),
            params.get("seletor_proximo"),
            params.get("max_paginas", 20),
            params.get("colunas"),
        )
        _dados[usuario] = dados
        return relatorio.resumo_dados(dados) | {"dados_salvos_localmente": True}

    # --- Relatorio ---
    if acao == "gerar_excel":
        dados = params.get("dados", _dados.get(usuario))
        if not dados:
            raise ValueError("Parametro 'dados' e obrigatorio (lista de dicts).")
        nome = params.get("nome_arquivo", f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
        if not isinstance(nome, str) or os.path.basename(nome) != nome or "/" in nome or "\\" in nome or not nome.lower().endswith(".xlsx"):
            raise ValueError("nome_arquivo deve ser um nome simples terminado em .xlsx.")
        pasta = os.path.join(os.path.dirname(__file__), "relatorios", usuario)
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome)
        caminho_final = relatorio.gerar_excel(
            dados, caminho,
            colunas=params.get("colunas"),
            titulo=params.get("titulo", "Relatorio"),
        )
        return {"arquivo": caminho_final, "registros": len(dados)}

    # --- Formularios ---
    if acao == "preencher_formulario":
        nav = _obter_nav(usuario)
        campos = params.get("campos")
        if not campos:
            raise ValueError("Parametro 'campos' e obrigatorio.")
        _previa.pop(usuario, None)
        previa = nav.preencher_formulario(campos, params.get("seletor_form", "form"))
        _previa[usuario] = {"url": nav.url_atual(), "campos": previa, "form": params.get("seletor_form", "form")}
        return {
            "previa": previa,
            "msg": "Formulario preenchido. Revise a previa e use 'submeter_formulario' para confirmar.",
        }

    if acao == "submeter_formulario":
        nav = _obter_nav(usuario)
        previa = _previa.get(usuario)
        if not previa or previa["url"] != nav.url_atual():
            raise ValueError("Preencha e revise o formulario antes de submeter.")
        chave = params.get("chave_unica")
        if not isinstance(chave, str) or not chave.strip():
            raise ValueError("chave_unica e obrigatoria para evitar reenvios.")
        if banco.lancamento_existe(usuario, chave):
            raise ValueError("Lancamento ja enviado ou com resultado incerto. Consulte o sistema antes de reenviar.")
        if not params.get("seletor_sucesso") and not params.get("texto_sucesso"):
            raise ValueError("Informe seletor_sucesso ou texto_sucesso para verificar o envio.")
        if nav.verificar_sucesso(params.get("seletor_sucesso"), params.get("texto_sucesso"))["sucesso"]:
            raise ValueError("Indicador de sucesso ja presente antes do envio. Escolha uma confirmacao especifica.")
        nav.validar_previa(previa["campos"], previa["form"])
        if _confirmar is None or not _confirmar(previa):
            raise ValueError("Envio cancelado: confirmacao local obrigatoria.")
        banco.registrar_lancamento(usuario, chave, nav.url_atual(), status="incerto")
        _previa.pop(usuario, None)
        nav.submeter_formulario(params.get("seletor_botao", "button[type=submit]"))
        resultado = nav.verificar_sucesso(params.get("seletor_sucesso"), params.get("texto_sucesso"))
        if not resultado["sucesso"]:
            raise RuntimeError("Envio sem confirmacao de sucesso. Consulte o sistema; nao repita automaticamente.")
        banco.registrar_lancamento(usuario, chave, nav.url_atual(), status="concluido")
        return resultado

    if acao == "verificar_sucesso":
        nav = _obter_nav(usuario)
        return nav.verificar_sucesso(
            params.get("seletor_sucesso"),
            params.get("texto_sucesso"),
        )

    # --- Fluxos ---
    if acao == "salvar_fluxo":
        nome = params.get("nome")
        if not nome:
            raise ValueError("Parametro 'nome' e obrigatorio.")
        passos = params.get("passos", [])
        if not isinstance(passos, list) or not passos or len(passos) > 100:
            raise ValueError("Fluxo deve conter de 1 a 100 passos.")
        for passo in passos:
            _validar(dict(passo, usuario=usuario) if isinstance(passo, dict) else passo)
            if passo["acao"] in {"salvar_fluxo", "executar_fluxo"}:
                raise ValueError("Fluxos aninhados nao sao permitidos.")
        banco.salvar_fluxo(nome, params.get("descricao", ""), params.get("passos", []))
        return {"msg": f"Fluxo '{nome}' salvo com sucesso."}

    if acao == "executar_fluxo":
        nome = params.get("nome")
        if not nome:
            raise ValueError("Parametro 'nome' e obrigatorio.")
        fluxo = banco.carregar_fluxo(nome)
        if not fluxo:
            return {"erro": f"Fluxo '{nome}' nao encontrado."}
        if any(not isinstance(p, dict) or p.get("acao") in {"executar_fluxo", "salvar_fluxo"} for p in fluxo["passos"]):
            raise ValueError("Fluxo contem passos invalidos ou aninhados.")
        resultados = []
        for i, passo in enumerate(fluxo["passos"]):
            passo["usuario"] = usuario
            res = executar(passo)
            resultados.append({"passo": i + 1, "acao": passo.get("acao"), "resultado": res})
            if "erro" in res:
                return {"erro": f"Falha no passo {i+1}", "resultados": resultados}
        return {"msg": f"Fluxo '{nome}' executado.", "passos": len(resultados), "resultados": resultados}

    if acao == "listar_fluxos":
        return {"fluxos": banco.listar_fluxos()}

    # --- Login e acoes gerais ---
    if acao == "fazer_login":
        nav = _abrir_se_necessario(usuario)
        _previa.pop(usuario, None)
        return nav.fazer_login(params.get("url"), params.get("seletor_usuario"), params.get("seletor_senha"),
                               params.get("seletor_botao"), bool(params.get("trocar", False)))

    if acao == "esquecer_login":
        site = params.get("site")
        if not isinstance(site, str) or not site:
            raise ValueError("Parametro 'site' (ex.: www.exemplo.com) e obrigatorio.")
        return {"removido": credenciais.excluir(site), "site": site}

    if acao == "listar_elementos":
        return _obter_nav(usuario).listar_elementos(int(params.get("max_itens", 60)), params.get("filtro"))

    if acao == "ler_pagina":
        return _obter_nav(usuario).ler_pagina(params.get("seletor", "body"), int(params.get("max_chars", 3000)))

    if acao in ("clicar", "pressionar_tecla", "voltar"):
        _previa.pop(usuario, None)
        nav = _obter_nav(usuario)
        if acao == "clicar":
            return nav.clicar(params.get("seletor"), params.get("texto"))
        if acao == "voltar":
            return nav.voltar()
        if not params.get("tecla"):
            raise ValueError("Parametro 'tecla' e obrigatorio (ex.: Enter, Tab, Escape).")
        return nav.pressionar_tecla(params["tecla"])

    if acao == "digitar":
        if not params.get("seletor") or "texto" not in params:
            raise ValueError("Parametros 'seletor' e 'texto' sao obrigatorios.")
        _previa.pop(usuario, None)
        return _obter_nav(usuario).digitar(params["seletor"], params["texto"], bool(params.get("enter", False)))

    if acao == "selecionar":
        if not params.get("seletor") or "valor" not in params:
            raise ValueError("Parametros 'seletor' e 'valor' sao obrigatorios.")
        _previa.pop(usuario, None)
        return _obter_nav(usuario).selecionar(params["seletor"], params["valor"])

    # --- Utilitarios ---
    if acao == "historico":
        return {"historico": banco.consultar_historico(usuario, params.get("limite", 20))}

    if acao == "status":
        nav_ativo = usuario in _navegadores
        info = {"navegador_ativo": nav_ativo, "usuario": usuario}
        if nav_ativo:
            nav = _navegadores[usuario]
            info["url_atual"] = nav.url_atual()
            info["titulo"] = nav.titulo_atual()
        return info

    if acao == "listar_sessoes":
        return {"sessoes": banco.listar_sessoes()}

    return {"erro": f"Acao '{acao}' nao implementada."}
