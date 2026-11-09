import asyncio
import json
import os
import sys
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

cofre = {}
keyring_falso = types.ModuleType("keyring")
keyring_falso.get_password = lambda servico, usuario: cofre.get((servico, usuario))
keyring_falso.set_password = lambda servico, usuario, valor: cofre.__setitem__((servico, usuario), valor)
keyring_falso.delete_password = lambda servico, usuario: cofre.pop((servico, usuario), None)
with patch.dict(sys.modules, {"keyring": keyring_falso}):
    import painel


class AgentesDepartamentoTest(unittest.TestCase):
    def setUp(self):
        cofre.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        legado = self.pasta / "APRENDIZADO.md"
        legado.write_text(
            "# Aprendizado\n\n"
            "## Usuario\n- Prefere respostas curtas.\n\n"
            "## Como trabalhar\n- Confirmar antes de executar.\n\n"
            "## Fatura Clara\n- Conferir contas no Conta Azul.\n\n"
            "## Cobli\n- Consultar veiculos da frota.\n\n"
            "## COS (mapa do menu)\n- Abrir ordem de servico.\n",
            encoding="utf-8",
        )
        self.conversa_legada = self.pasta / "conversa.json"
        patches = (
            patch.object(painel, "DADOS", str(self.pasta)),
            patch.object(painel, "AGENTES_DIR", str(self.pasta / "agentes")),
            patch.object(painel, "CONVERSA", str(self.conversa_legada)),
            patch.object(painel, "CONHECIMENTO", str(legado)),
            patch.object(painel, "USO_CLAUDE", str(self.pasta / "uso.json")),
            patch.object(painel, "LIMITE_DIARIO", 150),
            patch.dict(painel.atuais, {}, clear=True),
        )
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        painel._codigo_extensao = None
        self.addCleanup(self.temp.cleanup)

    def cliente(self):
        cliente = painel.app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["ok"] = True
        return cliente

    def test_painel_local_abre_sem_login(self):
        cliente = painel.app.test_client()
        inicio = cliente.get("/")
        self.assertEqual(inicio.status_code, 200)
        html = inicio.get_data(as_text=True)
        self.assertIn("Assistente", html)
        self.assertIn('id="root"', html)
        self.assertIn("/estatico/build/painel-react.js", html)
        self.assertEqual(cliente.get("/estatico/build/painel-react.js").status_code, 200)
        self.assertEqual(cliente.get("/login").status_code, 302)
        agentes = cliente.get("/api/agentes")
        self.assertEqual(agentes.status_code, 200)
        self.assertEqual(agentes.json["perfil"], "admin")

    def test_acesso_remoto_ainda_exige_login(self):
        painel.definir_senha("senha-segura-123")
        cliente = painel.app.test_client()
        ambiente_remoto = {"REMOTE_ADDR": "192.168.1.25"}
        inicio = cliente.get("/", environ_base=ambiente_remoto)
        self.assertEqual(inicio.status_code, 302)
        self.assertEqual(inicio.location, "/login")
        api = cliente.get("/api/agentes", environ_base=ambiente_remoto)
        self.assertEqual(api.status_code, 401)

    def test_historico_lista_e_abre_conversas_somente_do_departamento(self):
        financeiro = self.pasta / "agentes" / "financeiro" / "historico"
        operacional = self.pasta / "agentes" / "operacional" / "historico"
        financeiro.mkdir(parents=True)
        operacional.mkdir(parents=True)
        conversa_financeira = {
            "session_id": "sessao-financeira",
            "mensagens": [
                {"papel": "usuario", "texto": "Conferir fatura de novembro", "hora": "06/11 10:00"},
                {"papel": "claude", "texto": "Vamos conferir.", "hora": "06/11 10:01"},
            ],
        }
        (financeiro / "2026-11-06_100000.json").write_text(
            json.dumps(conversa_financeira), encoding="utf-8"
        )
        (operacional / "2026-11-06_110000.json").write_text(
            json.dumps({"mensagens": [{"papel": "usuario", "texto": "Ordem de serviço"}]}),
            encoding="utf-8",
        )

        cliente = self.cliente()
        resposta = cliente.get("/api/historico?agente=financeiro")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json["conversas"]), 1)
        resumo = resposta.json["conversas"][0]
        self.assertEqual(resumo["titulo"], "Conferir fatura de novembro")
        self.assertEqual(resumo["data"], "06/11/2026")

        resposta = cliente.get(
            f"/api/historico/{resumo['id']}?agente=financeiro"
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["mensagens"], conversa_financeira["mensagens"])
        self.assertNotIn("session_id", resposta.json)
        self.assertEqual(
            cliente.get(f"/api/historico/{resumo['id']}.json?agente=financeiro").status_code,
            400,
        )

        rh = self.cliente()
        with rh.session_transaction() as sessao:
            sessao["perfil"] = "rh"
        self.assertEqual(
            rh.get("/api/historico?agente=financeiro").status_code,
            403,
        )

    def test_troca_senha_e_local_e_exige_senha_forte_com_1507(self):
        cliente = painel.app.test_client()
        pagina = cliente.get("/alterar-senha")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn("minlength=\"12\"", pagina.get_data(as_text=True))
        with cliente.session_transaction() as sessao:
            token = sessao["token_alterar_senha"]

        antiga = "senha-antiga-segura"
        painel.definir_senha(antiga)
        csrf = cliente.post(
            "/alterar-senha",
            data={"senha": "Aquilix!1507#segura", "repetir": "Aquilix!1507#segura"},
        )
        self.assertEqual(csrf.status_code, 400)
        self.assertTrue(painel.conferir_senha(antiga))
        with cliente.session_transaction() as sessao:
            token = sessao["token_alterar_senha"]

        invalida = cliente.post(
            "/alterar-senha",
            data={"token": token, "senha": "1507curta", "repetir": "1507curta"},
        )
        self.assertEqual(invalida.status_code, 200)
        self.assertIn("pelo menos 12", invalida.get_data(as_text=True))
        self.assertTrue(painel.conferir_senha(antiga))

        nova = "Aquilix!1507#segura"
        resposta = cliente.post(
            "/alterar-senha",
            data={"token": token, "senha": nova, "repetir": nova},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.location, "/login")
        self.assertFalse(painel.conferir_senha(antiga))
        self.assertTrue(painel.conferir_senha(nova))

    def test_troca_senha_e_bloqueada_pela_internet_mesmo_logado(self):
        painel.definir_senha("senha-segura-123")
        cliente = self.cliente()
        resposta = cliente.get(
            "/alterar-senha",
            environ_base={"REMOTE_ADDR": "192.168.1.25"},
        )
        self.assertEqual(resposta.status_code, 403)

    def test_so_perguntas_de_esclarecimento_podem_parar_para_resposta(self):
        self.assertTrue(painel._perguntar_detalhes_ao_usuario("AskUserQuestion"))
        for ferramenta in (
            "mcp__claude-in-chrome__tabs_context_mcp",
            "mcp__claude-in-chrome__click",
            "Skill",
            "Write",
            "mcp__assistente-web__submeter_formulario",
        ):
            with self.subTest(ferramenta=ferramenta):
                self.assertFalse(painel._perguntar_detalhes_ao_usuario(ferramenta))

    def test_cookie_de_sessao_pode_ser_marcado_como_secure(self):
        anterior = painel.app.config["SESSION_COOKIE_SECURE"]
        painel.app.config["SESSION_COOKIE_SECURE"] = True
        try:
            resposta = painel.app.test_client().get("/")
            self.assertIn("Secure", resposta.headers["Set-Cookie"])
        finally:
            painel.app.config["SESSION_COOKIE_SECURE"] = anterior

    def test_extensao_exige_codigo_temporario_e_token_revogavel(self):
        origem = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"
        administrador = self.cliente()
        codigo = administrador.post(
            "/api/extensao/codigo",
            headers={"X-Painel": "1"},
        )
        self.assertEqual(codigo.status_code, 200)
        self.assertEqual(codigo.json["expira_em"], 300)

        anonimo = painel.app.test_client()
        sem_codigo = anonimo.post(
            "/api/extensao/vincular",
            json={"codigo": "incorreto"},
            headers={"Origin": origem},
        )
        self.assertEqual(sem_codigo.status_code, 400)
        vinculo = anonimo.post(
            "/api/extensao/vincular",
            json={"codigo": codigo.json["codigo"]},
            headers={"Origin": origem},
        )
        self.assertEqual(vinculo.status_code, 200)
        self.assertEqual(vinculo.headers["Access-Control-Allow-Origin"], origem)
        token = vinculo.json["token"]
        cabecalhos = {"Origin": origem, "Authorization": f"Bearer {token}"}

        preflight = anonimo.options(
            "/api/agentes",
            headers={
                **cabecalhos,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,x-painel",
            },
        )
        self.assertEqual(preflight.status_code, 204)
        self.assertEqual(preflight.headers["Access-Control-Allow-Origin"], origem)

        agentes = anonimo.get("/api/agentes", headers=cabecalhos)
        self.assertEqual(agentes.status_code, 200)
        self.assertEqual(agentes.headers["Access-Control-Allow-Origin"], origem)
        self.assertEqual(len(agentes.json["agentes"]), 6)

        reutilizado = anonimo.post(
            "/api/extensao/vincular",
            json={"codigo": codigo.json["codigo"]},
            headers={"Origin": origem},
        )
        self.assertEqual(reutilizado.status_code, 400)
        revogado = anonimo.post(
            "/api/extensao/revogar",
            headers={**cabecalhos, "X-Painel": "1"},
        )
        self.assertEqual(revogado.status_code, 200)
        self.assertEqual(anonimo.get("/api/agentes", headers=cabecalhos).status_code, 401)

    def test_extensao_recusa_origem_nao_extensao(self):
        resposta = painel.app.test_client().post(
            "/api/extensao/vincular",
            json={"codigo": "qualquer"},
            headers={"Origin": "https://exemplo.com"},
        )
        self.assertEqual(resposta.status_code, 403)

    def test_pagina_de_vinculacao_abre_no_painel_local(self):
        resposta = self.cliente().get("/extensao/conectar")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Gerar código", resposta.get_data(as_text=True))

    def test_contexto_de_pagina_tem_limite_de_caracteres(self):
        resposta = self.cliente().post(
            "/api/mensagem",
            data={
                "agente": "operacional",
                "texto": "Resuma esta pagina",
                "contexto_url": "https://exemplo.com",
                "contexto_titulo": "Pagina",
                "contexto_texto": "x" * 6001,
            },
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 413)
        self.assertIn("6.000 caracteres", resposta.json["erro"])

    def test_disponibiliza_os_seis_agentes(self):
        resposta = self.cliente().get("/api/agentes")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["perfil"], "admin")
        self.assertEqual(
            [agente["id"] for agente in resposta.json["agentes"]],
            ["rh", "frotas", "financeiro", "operacional", "administrativo", "estudos"],
        )

    def test_agente_estudos_tem_conversa_e_memoria_separadas(self):
        cliente = self.cliente()
        resposta = cliente.get("/api/conversa?agente=estudos")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["agente"], "estudos")
        self.assertNotEqual(
            painel._arquivo_conversa("estudos"),
            painel._arquivo_conversa("operacional"),
        )
        self.assertNotEqual(
            painel._arquivo_memoria("estudos"),
            painel._arquivo_memoria("operacional"),
        )

    def test_login_rh_tem_acesso_exclusivo_ao_departamento(self):
        administrador = self.cliente()
        acesso_inicial = administrador.get("/api/acesso-rh")
        self.assertEqual(acesso_inicial.status_code, 200)
        self.assertFalse(acesso_inicial.json["configurado"])
        configuracao = administrador.post(
            "/api/acesso-rh",
            json={"usuario": "Equipe-Área", "senha": "senha-segura-123",
                  "repetir": "senha-segura-123"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(configuracao.status_code, 200)
        self.assertNotIn("senha-segura-123", configuracao.get_data(as_text=True))
        self.assertNotIn("senha-segura-123", cofre[(painel.COFRE_RH, "conta")])

        rh = painel.app.test_client()
        rh.environ_base["REMOTE_ADDR"] = "192.168.1.25"
        login = rh.post(
            "/login-rh",
            data={"usuario": "equipe-área", "senha": "senha-segura-123"},
        )
        self.assertEqual(login.status_code, 302)

        agentes = rh.get("/api/agentes")
        self.assertEqual(agentes.status_code, 200)
        self.assertEqual(agentes.json["perfil"], "rh")
        self.assertEqual([agente["id"] for agente in agentes.json["agentes"]], ["rh"])
        self.assertEqual(rh.get("/api/conversa").json["agente"], "rh")
        negado = rh.get("/api/conversa?agente=financeiro")
        self.assertEqual(negado.status_code, 403)
        self.assertIn("somente o departamento de RH", negado.json["erro"])
        self.assertEqual(rh.get("/api/conhecimentos?agente=operacional").status_code, 403)
        self.assertEqual(
            rh.post(
                "/api/mensagem",
                data={"agente": "frotas", "texto": "Consultar frota"},
                headers={"X-Painel": "1"},
            ).status_code,
            403,
        )
        self.assertEqual(rh.get("/api/acesso-rh").status_code, 403)
        self.assertEqual(rh.get("/api/claude-rh").status_code, 403)
        self.assertEqual(
            rh.post("/api/claude-rh/login", headers={"X-Painel": "1"}).status_code,
            403,
        )
        self.assertEqual(rh.get("/api/limite").status_code, 403)

    def test_mensagem_de_rh_exige_a_conta_claude_correta(self):
        with patch.object(painel, "_status_claude_rh", return_value={
            "instalado": True,
            "conectado": False,
            "email_esperado": painel.CLAUDE_RH_EMAIL,
        }):
            resposta = self.cliente().post(
                "/api/mensagem",
                data={"agente": "rh", "texto": "Olá"},
                headers={"X-Painel": "1"},
            )

        self.assertEqual(resposta.status_code, 503)
        self.assertIn(painel.CLAUDE_RH_EMAIL, resposta.json["erro"])

    def test_login_rh_recusa_senha_incorreta(self):
        painel.definir_acesso_rh("equipe-rh", "senha-segura-123")
        cliente = painel.app.test_client()
        cliente.environ_base["REMOTE_ADDR"] = "192.168.1.25"
        resposta = cliente.post(
            "/login-rh",
            data={"usuario": "equipe-rh", "senha": "senha-incorreta"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Login ou senha incorretos", resposta.get_data(as_text=True))

    def test_conta_claude_rh_usa_configuracao_de_autenticacao_separada(self):
        saida = json.dumps({
            "loggedIn": True,
            "email": painel.CLAUDE_RH_EMAIL,
        })
        resultado = subprocess.CompletedProcess(
            args=["claude", "auth", "status", "--json"],
            returncode=0,
            stdout=saida,
            stderr="",
        )
        with (
            patch.dict(os.environ, {
                "ANTHROPIC_API_KEY": "nao-usar",
                "CLAUDE_CODE_OAUTH_TOKEN": "nao-usar",
            }),
            patch.object(painel, "_caminho_claude", return_value="claude"),
            patch.object(painel.subprocess, "run", return_value=resultado) as executar,
        ):
            status = painel._status_claude_rh()

        self.assertTrue(status["conectado"])
        self.assertEqual(status["email_esperado"], painel.CLAUDE_RH_EMAIL)
        self.assertEqual(
            executar.call_args.kwargs["env"]["CLAUDE_CONFIG_DIR"],
            painel.CLAUDE_RH_CONFIG,
        )
        self.assertNotIn("ANTHROPIC_API_KEY", executar.call_args.kwargs["env"])

    def test_conta_claude_rh_recusa_outra_conta(self):
        resultado = subprocess.CompletedProcess(
            args=["claude", "auth", "status", "--json"],
            returncode=0,
            stdout=json.dumps({"loggedIn": True, "email": "outra-conta@example.com"}),
            stderr="",
        )
        with (
            patch.object(painel, "_caminho_claude", return_value="claude"),
            patch.object(painel.subprocess, "run", return_value=resultado),
        ):
            status = painel._status_claude_rh()

        self.assertFalse(status["conectado"])
        self.assertEqual(status["email_conectado"], "outra-conta@example.com")

    def test_login_oficial_claude_do_rh_abre_configuracao_separada(self):
        class ProcessoFalso:
            def poll(self):
                return None

        painel._login_claude_rh = None
        with (
            patch.object(painel, "_caminho_claude", return_value="claude.exe"),
            patch.object(painel.os, "makedirs"),
            patch.object(painel.subprocess, "Popen", return_value=ProcessoFalso()) as iniciar,
        ):
            self.assertTrue(painel._iniciar_login_claude_rh())

        argumentos, opcoes = iniciar.call_args
        self.assertEqual(
            argumentos[0],
            [
                "claude.exe", "auth", "login", "--claudeai",
                "--email", painel.CLAUDE_RH_EMAIL,
            ],
        )
        self.assertEqual(opcoes["env"]["CLAUDE_CONFIG_DIR"], painel.CLAUDE_RH_CONFIG)
        self.assertNotIn("ANTHROPIC_API_KEY", opcoes["env"])
        self.assertFalse(painel._iniciar_login_claude_rh())
        painel._login_claude_rh = None

    def test_memorias_departamentais_nao_compartilham_procedimentos(self):
        memoria_financeira = Path(painel._arquivo_memoria("financeiro")).read_text(encoding="utf-8")
        memoria_frotas = Path(painel._arquivo_memoria("frotas")).read_text(encoding="utf-8")
        self.assertIn("Fatura Clara", memoria_financeira)
        self.assertNotIn("Fatura Clara", memoria_frotas)
        self.assertIn("Cobli", memoria_frotas)
        self.assertNotEqual(
            painel._arquivo_memoria("financeiro"),
            painel._arquivo_memoria("frotas"),
        )

    def test_conversa_antiga_e_preservada_no_agente_operacional(self):
        self.conversa_legada.write_text(
            json.dumps({"session_id": "sessao-antiga", "mensagens": [{"texto": "historico"}]}),
            encoding="utf-8",
        )
        caminho = Path(painel._arquivo_conversa("operacional"))
        self.assertTrue(caminho.exists())
        self.assertFalse(self.conversa_legada.exists())
        self.assertEqual(painel.carregar("operacional")["session_id"], "sessao-antiga")

    def test_conversas_isoladas_e_execucoes_independentes(self):
        cliente = self.cliente()
        chamadas = []

        class ThreadFalsa:
            def __init__(self, **opcoes):
                chamadas.append(opcoes)

            def start(self):
                pass

        with patch.object(painel.threading, "Thread", ThreadFalsa):
            financeiro = cliente.post(
                "/api/mensagem",
                data={"agente": "financeiro", "texto": "Conferir uma conta"},
                headers={"X-Painel": "1"},
            )
            frotas = cliente.post(
                "/api/mensagem",
                data={"agente": "frotas", "texto": "Consultar os veiculos"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(financeiro.status_code, 200)
            self.assertEqual(frotas.status_code, 200)
            self.assertEqual(chamadas[0]["args"][3], "financeiro")
            self.assertEqual(chamadas[1]["args"][3], "frotas")

            repetida = cliente.post(
                "/api/mensagem",
                data={"agente": "financeiro", "texto": "Nao deve iniciar em paralelo"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(repetida.status_code, 409)

        conversa_financeira = cliente.get("/api/conversa?agente=financeiro").json
        conversa_frotas = cliente.get("/api/conversa?agente=frotas").json
        self.assertEqual(conversa_financeira["mensagens"][0]["texto"], "Conferir uma conta")
        self.assertEqual(conversa_frotas["mensagens"][0]["texto"], "Consultar os veiculos")
        self.assertTrue(conversa_financeira["rodando"])
        self.assertTrue(conversa_frotas["rodando"])

    def test_rejeita_departamento_inexistente(self):
        resposta = self.cliente().get("/api/conversa?agente=juridico")
        self.assertEqual(resposta.status_code, 400)

    def test_recupera_conversas_anteriores_relevantes_somente_do_agente(self):
        historico_frotas = Path(painel.AGENTES_DIR) / "frotas" / "historico"
        historico_frotas.mkdir(parents=True)
        (historico_frotas / "2026-10-20_120000.json").write_text(
            json.dumps({"mensagens": [
                {"papel": "usuario", "texto": "Como conferir abastecimento na Cobli?"},
                {"papel": "claude", "texto": "Abra a tela de abastecimento e confira placa e data."},
            ]}),
            encoding="utf-8",
        )
        historico_financeiro = Path(painel.AGENTES_DIR) / "financeiro" / "historico"
        historico_financeiro.mkdir(parents=True)
        (historico_financeiro / "2026-10-20_120001.json").write_text(
            json.dumps({"mensagens": [
                {"papel": "usuario", "texto": "Como pagar uma fatura?"},
                {"papel": "claude", "texto": "Confira a fatura no sistema financeiro."},
            ]}),
            encoding="utf-8",
        )

        trechos = painel.selecionar_conversas_anteriores(
            "Conferir abastecimento na Cobli", "frotas"
        )

        self.assertEqual(len(trechos), 1)
        self.assertIn("placa e data", trechos[0])
        self.assertEqual(
            painel.selecionar_conversas_anteriores("abastecimento Cobli", "rh"),
            [],
        )

    def test_ferramentas_nao_pedem_autorizacao_repetida(self):
        opcoes_criadas = []

        class OpcaoFalsa:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                opcoes_criadas.append(self)

        class PermissaoPermitidaFalsa:
            def __init__(self, updated_input):
                self.updated_input = updated_input

        class ClienteFalso:
            def __init__(self, options):
                self.options = options

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def query(self, mensagem):
                return None

            async def receive_response(self):
                if False:
                    yield None

        sdk_falso = types.ModuleType("claude_agent_sdk")
        sdk_falso.AssistantMessage = type("AssistantMessage", (), {})
        sdk_falso.ClaudeAgentOptions = OpcaoFalsa
        sdk_falso.ClaudeSDKClient = ClienteFalso
        sdk_falso.PermissionResultAllow = PermissaoPermitidaFalsa
        sdk_falso.PermissionResultDeny = type("PermissionResultDeny", (), {})
        sdk_falso.ResultMessage = type("ResultMessage", (), {})
        sdk_falso.SystemMessage = type("SystemMessage", (), {})
        sdk_falso.TextBlock = type("TextBlock", (), {})
        sdk_falso.ToolUseBlock = type("ToolUseBlock", (), {})
        with patch.dict(sys.modules, {"claude_agent_sdk": sdk_falso}):
            asyncio.run(painel._conversar(painel.Execucao(), [], None, "financeiro"))
            asyncio.run(painel._conversar(painel.Execucao(), [], None, "rh"))

        financeiro = opcoes_criadas[0].kwargs
        self.assertIn("MODO EXECUCAO DO PEDIDO", financeiro["system_prompt"]["append"])
        self.assertNotIn("hooks", financeiro)
        permitir = financeiro["can_use_tool"]
        escrita = asyncio.run(permitir("Write", {"file_path": "arquivo.txt"}, {}))
        self.assertIsInstance(escrita, PermissaoPermitidaFalsa)
        self.assertEqual(escrita.updated_input, {"file_path": "arquivo.txt"})

        rh = opcoes_criadas[1].kwargs
        self.assertNotIn("MODO EXECUCAO DO PEDIDO", rh["system_prompt"]["append"])
        self.assertNotIn("hooks", rh)

    def test_relatorio_web_somente_com_login_e_com_isolamento_de_conteudo(self):
        pasta_relatorios = self.pasta / "relatorios" / "financeiro"
        pasta_relatorios.mkdir(parents=True)
        (pasta_relatorios / "relatorio-2026-10-22-teste.html").write_text(
            "<!doctype html><title>Relatorio local</title>",
            encoding="utf-8",
        )
        with patch.object(painel, "RELATORIOS", str(self.pasta / "relatorios")):
            anonimo = painel.app.test_client()
            anonimo.environ_base["REMOTE_ADDR"] = "192.168.1.25"
            resposta_anonima = anonimo.get(
                "/relatorios/financeiro/relatorio-2026-10-22-teste.html"
            )
            self.assertEqual(resposta_anonima.status_code, 302)

            cliente = self.cliente()
            resposta = cliente.get(
                "/relatorios/financeiro/relatorio-2026-10-22-teste.html"
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.mimetype, "text/html")
            self.assertIn("sandbox allow-scripts", resposta.headers["Content-Security-Policy"])
            self.assertIn("connect-src 'none'", resposta.headers["Content-Security-Policy"])
            self.assertEqual(resposta.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(resposta.headers["Cache-Control"], "no-store")
            self.assertEqual(
                cliente.get("/relatorios/financeiro/../segredo.html").status_code,
                404,
            )
            self.assertEqual(
                cliente.get("/relatorios/rh/relatorio-2026-10-22-teste.html").status_code,
                404,
            )
            resposta.close()

            rh = painel.app.test_client()
            rh.environ_base["REMOTE_ADDR"] = "192.168.1.25"
            with rh.session_transaction() as sessao:
                sessao["ok"] = True
                sessao["perfil"] = "rh"
            self.assertEqual(
                rh.get("/relatorios/financeiro/relatorio-2026-10-22-teste.html").status_code,
                403,
            )

    def test_perfil_define_especialidade_memoria_e_escopo_de_permissao(self):
        opcoes_criadas = []

        class OpcaoFalsa:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                opcoes_criadas.append(self)

        class PermissaoPermitidaFalsa:
            def __init__(self, updated_input):
                self.updated_input = updated_input

        class ClienteFalso:
            def __init__(self, options):
                self.options = options

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def query(self, mensagem):
                self.mensagem = mensagem

            async def receive_response(self):
                if False:
                    yield None

        sdk_falso = types.ModuleType("claude_agent_sdk")
        sdk_falso.AssistantMessage = type("AssistantMessage", (), {})
        sdk_falso.ClaudeAgentOptions = OpcaoFalsa
        sdk_falso.ClaudeSDKClient = ClienteFalso
        sdk_falso.PermissionResultAllow = PermissaoPermitidaFalsa
        sdk_falso.PermissionResultDeny = type("PermissionResultDeny", (), {})
        sdk_falso.ResultMessage = type("ResultMessage", (), {})
        sdk_falso.SystemMessage = type("SystemMessage", (), {})
        sdk_falso.TextBlock = type("TextBlock", (), {})
        sdk_falso.ToolUseBlock = type("ToolUseBlock", (), {})
        with patch.dict(sys.modules, {"claude_agent_sdk": sdk_falso}):
            asyncio.run(painel._conversar(painel.Execucao(), [], None, "financeiro"))
            asyncio.run(painel._conversar(painel.Execucao(), [], None, "rh"))
            painel._salvar_uso_claude(painel._ler_uso_claude() | {"modelo": "haiku"})
            asyncio.run(painel._conversar(painel.Execucao(), [], None, "operacional"))

        configuracao = opcoes_criadas[0].kwargs
        orientacao = configuracao["system_prompt"]["append"]
        self.assertIn("Financeiro", orientacao)
        self.assertIn("painel_dados/agentes/financeiro/conhecimento.md", orientacao)
        self.assertIn("mensagem atual do usuario autoriza", orientacao)
        self.assertIn("nao peca autorizacao repetida", orientacao)
        self.assertIn("mensagem atual contiver um URL", orientacao)
        self.assertIn("nao pergunte esse link novamente", orientacao)
        self.assertIn("navegue imediatamente", orientacao)
        self.assertIn("endereco exato informado", orientacao)
        self.assertIn("Um erro 403", orientacao)
        self.assertIn("Nao substitua esse URL", orientacao)
        self.assertIn("Power BI ou Looker/Data Studio", orientacao)
        self.assertIn("captura visual da pagina", orientacao)
        self.assertIn("Economize tokens", orientacao)
        self.assertIn("sem repetir a pergunta", orientacao)
        self.assertIn("RELATORIOS WEB", orientacao)
        self.assertIn("relatorios/financeiro/", orientacao)
        self.assertIn("sem CDN", orientacao)
        self.assertEqual(configuracao["permission_mode"], "auto")
        self.assertEqual(configuracao["model"], "sonnet")
        self.assertEqual(configuracao["env"], {})
        self.assertNotIn("hooks", configuracao)
        permitir = configuracao["can_use_tool"]
        resultado = asyncio.run(permitir(
            "mcp__claude-in-chrome__click",
            {"text": "Abrir menu"},
            {},
        ))
        self.assertIsInstance(resultado, PermissaoPermitidaFalsa)
        self.assertEqual(resultado.updated_input, {"text": "Abrir menu"})

        rh_configuracao = opcoes_criadas[1].kwargs
        self.assertEqual(rh_configuracao["model"], "sonnet")
        self.assertEqual(
            rh_configuracao["env"]["CLAUDE_CONFIG_DIR"],
            painel.CLAUDE_RH_CONFIG,
        )

        economico = opcoes_criadas[2].kwargs
        self.assertEqual(economico["model"], "haiku")
        self.assertIn("MODO ECONOMIA", economico["system_prompt"]["append"])
        self.assertEqual(rh_configuracao["env"]["ANTHROPIC_API_KEY"], "")
        self.assertEqual(rh_configuracao["env"]["ANTHROPIC_AUTH_TOKEN"], "")
        self.assertIn(
            painel.CLAUDE_RH_EMAIL,
            rh_configuracao["system_prompt"]["append"],
        )


if __name__ == "__main__":
    unittest.main()
