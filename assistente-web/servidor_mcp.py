"""
servidor_mcp.py - Liga o assistente ao Claude Code via MCP (stdio).

O Claude chama as acoes direto, sem copiar e colar JSON. Tabelas extraidas
ficam no computador; o Claude recebe so o resumo compacto.
O pedido atual do usuario autoriza somente as acoes pedidas e os passos necessarios.
Envios so podem ser feitos quando o usuario pedir explicitamente o envio.
"""

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from mcp.server.mcpserver import MCPServer

import banco
import executor
import navegador

# Playwright sync exige que todas as chamadas usem a mesma thread.
_thread = ThreadPoolExecutor(max_workers=1)
navegador.LOGIN_NO_TERMINAL = False
executor.configurar_confirmacao(lambda previa: False)

mcp = MCPServer(
    "assistente-web",
    instructions=(
        "Automacao local de navegador para fazer o que o usuario pedir num site. "
        "Login: use fazer_login; na 1a vez uma janela no PC pede usuario/senha e guarda no "
        "cofre do Windows. Nunca peca senha no chat. Codigo 2FA o usuario digita no navegador. "
        "Para achar seletores use listar_elementos (com filtro) em vez de ler HTML; para ler "
        "conteudo use ler_pagina ou extrair_tabela. Para Excel nao reenvie dados. Nao peca "
        "autorizacao repetida para ferramentas: o pedido atual autoriza exatamente a tarefa pedida "
        "e seus passos necessarios. Nunca extrapole esse escopo. Acoes de impacto, como pagar, "
        "enviar, excluir ou aprovar, so podem ser feitas se o usuario as pedir explicitamente e "
        "o alvo/conteudo estiver claro; pergunte somente se faltar um dado essencial."
    ),
)


def _compactar(resultado: dict) -> str:
    r = resultado.get("resultado")
    if isinstance(r, dict) and isinstance(r.get("resultados"), list):
        r = dict(r, resultados=[
            {"passo": p["passo"], "acao": p["acao"], "ok": "erro" not in p["resultado"],
             **({"erro": p["resultado"]["erro"]} if "erro" in p["resultado"] else {})}
            for p in r["resultados"]])
        resultado = dict(resultado, resultado=r)
    if isinstance(resultado.get("resultados"), list):
        resultado = dict(resultado, resultados=[
            {"passo": p["passo"], "acao": p["acao"], "erro": p["resultado"].get("erro")}
            for p in resultado["resultados"] if "erro" in p["resultado"]])
    return json.dumps(resultado, ensure_ascii=False, default=str)


async def _rodar(cmd: dict) -> str:
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(_thread, executor.executar, cmd)
    return _compactar(resultado)


@mcp.tool()
async def assistente(acao: str, params: dict | None = None, usuario: str = "abner") -> str:
    """Executa uma acao do assistente web local.

    Acoes e params:
    - abrir_navegador {headless?} / fechar_navegador / status
    - abrir_url {url, esperar_ms?}
    - fazer_login {url?, seletor_usuario?, seletor_senha?, seletor_botao?, trocar?}: senha do cofre do Windows
    - aguardar_login {} : depois que o usuario disser que fez login/2FA no navegador; salva a sessao
    - esquecer_login {site}
    - listar_elementos {filtro?, max_itens?}: botoes/links/campos com seletor curto [data-aw="N"]
    - ler_pagina {seletor?, max_chars?}: texto visivel
    - clicar {seletor | texto} / digitar {seletor, texto, enter?} / pressionar_tecla {tecla}
    - selecionar {seletor, valor} / voltar
    - screenshot {nome?}
    - extrair_tabela {seletor, colunas?}
    - extrair_com_paginacao {seletor, seletor_proximo, max_paginas?, colunas?}
    - gerar_excel {nome_arquivo (.xlsx), colunas?, titulo?} usa a ultima extracao
    - preencher_formulario {seletor_form?, campos: {seletor: valor}} mostra previa, nao envia
    - verificar_sucesso {seletor_sucesso?, texto_sucesso?}
    - salvar_fluxo {nome, descricao?, passos: [{acao, params}]} / executar_fluxo {nome} / listar_fluxos
    - historico {limite?} / listar_sessoes
    Para enviar formulario use a ferramenta submeter_formulario.
    """
    if acao == "submeter_formulario":
        return json.dumps({"ok": False, "erro": "Use a ferramenta submeter_formulario."})
    return await _rodar({"acao": acao, "usuario": usuario, "params": params or {}})


@mcp.tool()
async def submeter_formulario(chave_unica: str, seletor_botao: str = "button[type=submit]",
                              texto_sucesso: str | None = None, seletor_sucesso: str | None = None,
                              confirmar: bool = False, usuario: str = "abner") -> str:
    """Envia o formulario preenchido. Com confirmar=false so devolve a previa.
    Use confirmar=true se o pedido atual solicitar explicitamente o envio deste formulario,
    com alvo e conteudo claros; esse pedido ja e a autorizacao. Se o usuario pediu apenas
    para preparar ou preencher, nao envie. chave_unica evita duplicidade; informe
    texto_sucesso ou seletor_sucesso."""
    if not confirmar:
        previa = executor._previa.get(usuario)
        if not previa:
            return json.dumps({"ok": False, "erro": "Nada preenchido. Use preencher_formulario antes."})
        return json.dumps({"ok": True, "previa": previa,
                           "msg": "Previa exibida. Envie somente se o pedido atual solicitou explicitamente este envio."},
                          ensure_ascii=False)
    executor.configurar_confirmacao(lambda previa: True)
    try:
        params = {"chave_unica": chave_unica, "seletor_botao": seletor_botao,
                  "texto_sucesso": texto_sucesso, "seletor_sucesso": seletor_sucesso}
        return await _rodar({"acao": "submeter_formulario", "usuario": usuario,
                             "params": {k: v for k, v in params.items() if v is not None}})
    finally:
        executor.configurar_confirmacao(lambda previa: False)


if __name__ == "__main__":
    banco.inicializar()
    try:
        mcp.run("stdio")
    finally:
        _thread.submit(executor.fechar_todos).result(timeout=30)
