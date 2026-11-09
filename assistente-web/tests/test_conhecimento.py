import json
import sys
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
with patch.dict(sys.modules, {"keyring": keyring_falso}):
    import painel


class ConhecimentoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.temp.name) / "APRENDIZADO.md"
        self.arquivo.write_text(
            "# Aprendizado\n\n"
            "## Usuario\n- Prefere respostas curtas.\n\n"
            "## Como trabalhar\n- Confirmar antes de enviar.\n\n"
            "## Fatura Clara\n- Conferir compras e categorias no Conta Azul.\n\n"
            "## Cobli\n- Consultar os dados da frota.\n",
            encoding="utf-8",
        )
        patches = (
            patch.object(painel, "CONHECIMENTO", str(self.arquivo)),
            patch.object(painel, "AGENTES_DIR", str(Path(self.temp.name) / "agentes")),
        )
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(self.temp.cleanup)

    def test_seleciona_memoria_geral_e_assunto_sem_outros_assuntos(self):
        secoes = painel.selecionar_conhecimento("Conta Azul, fatura Clara")
        ids = [secao["id"] for secao in secoes]
        self.assertIn("usuario", ids)
        self.assertIn("como-trabalhar", ids)
        self.assertIn("fatura-clara", ids)
        titulos = [secao["titulo"] for secao in secoes]
        self.assertFalse(any("garantia Samsung" in titulo for titulo in titulos))
        self.assertNotIn("cobli", ids)

    def test_nao_repete_secoes_ja_enviadas_na_conversa(self):
        usados = {
            secao["chave"]
            for secao in painel.selecionar_conhecimento("Conta Azul, fatura Clara")
        }
        secoes = painel.selecionar_conhecimento("Conta Azul, fatura Clara", usados)
        self.assertEqual(secoes, [])

    def test_nova_versao_de_secao_alterada_volta_a_ser_enviada(self):
        enviados = {
            secao["chave"]
            for secao in painel.selecionar_conhecimento("Conta Azul, fatura Clara")
        }
        self.arquivo.write_text(
            self.arquivo.read_text(encoding="utf-8").replace(
                "- Conferir compras e categorias no Conta Azul.",
                "- Conferir compras, categorias e comprovantes no Conta Azul.",
            ),
            encoding="utf-8",
        )
        novos = painel.selecionar_conhecimento("Conta Azul, fatura Clara", enviados)
        self.assertIn("fatura-clara", [secao["id"] for secao in novos])

    def test_api_consulta_e_salva_memoria_local(self):
        cliente = painel.app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["ok"] = True
        headers = {"X-Painel": "1"}

        resposta = cliente.get("/api/conhecimentos?agente=financeiro")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Fatura Clara", resposta.json["conteudo"])

        atualizado = "# Aprendizado\n\n## Frota\n- Processo atualizado.\n"
        resposta = cliente.post(
            "/api/conhecimentos",
            json={"conteudo": atualizado, "agente": "financeiro"},
            headers=headers,
        )
        self.assertEqual(resposta.status_code, 200)
        memoria_financeiro = Path(painel._arquivo_memoria("financeiro"))
        self.assertEqual(memoria_financeiro.read_text(encoding="utf-8"), atualizado)
        self.assertNotEqual(Path(painel._arquivo_memoria("frotas")), memoria_financeiro)

    def test_api_recusa_conteudo_invalido_ou_excessivo(self):
        cliente = painel.app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["ok"] = True
        headers = {"X-Painel": "1"}

        resposta = cliente.post("/api/conhecimentos", json={"conteudo": []}, headers=headers)
        self.assertEqual(resposta.status_code, 400)
        resposta = cliente.post(
            "/api/conhecimentos",
            json={"conteudo": "conhecimento", "agente": "inexistente"},
            headers=headers,
        )
        self.assertEqual(resposta.status_code, 400)
        resposta = cliente.post(
            "/api/conhecimentos",
            json={"conteudo": "x" * 250_001},
            headers=headers,
        )
        self.assertEqual(resposta.status_code, 413)

    def test_mensagem_envia_apenas_memoria_relevante_e_uma_vez(self):
        cliente = painel.app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["ok"] = True
        conversa = Path(self.temp.name) / "conversa.json"
        chamadas = []

        class ThreadFalsa:
            def __init__(self, **opcoes):
                chamadas.append(opcoes)

            def start(self):
                pass

        with (
            patch.object(painel, "CONVERSA", str(conversa)),
            patch.object(painel, "AGENTES_DIR", str(Path(self.temp.name) / "agentes")),
            patch.dict(painel.atuais, {}, clear=True),
            patch.object(painel.threading, "Thread", ThreadFalsa),
        ):
            historico = Path(painel.AGENTES_DIR) / "financeiro" / "historico"
            historico.mkdir(parents=True)
            (historico / "2026-10-20_120000.json").write_text(
                json.dumps({"mensagens": [
                    {"papel": "usuario", "texto": "Como registrar uma fatura Clara?"},
                    {"papel": "claude", "texto": "Conferir a fatura no Conta Azul."},
                ]}),
                encoding="utf-8",
            )
            resposta = cliente.post(
                "/api/mensagem",
                data={
                    "agente": "financeiro",
                    "texto": "Como lancar a fatura Clara no Conta Azul?",
                    "ensinar": "1",
                },
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 200)
            blocos = chamadas[0]["args"][1]
            memoria = "\n".join(bloco["text"] for bloco in blocos if bloco["type"] == "text")
            self.assertIn("## Fatura Clara", memoria)
            self.assertNotIn("## Notas de servico de garantia Samsung", memoria)
            contexto = "\n".join(bloco["text"] for bloco in blocos if bloco["type"] == "text")
            self.assertIn("[REFERENCIAS DE CONVERSAS ANTERIORES", contexto)
            self.assertIn("Conferir a fatura no Conta Azul", contexto)

            memoria = "\n".join(bloco["text"] for bloco in blocos if bloco["type"] == "text")
            self.assertIn("[MODO ENSINO]", memoria)
            painel.atuais["financeiro"].fim = True
            resposta = cliente.post(
                "/api/mensagem",
                data={"agente": "financeiro", "texto": "Qual o proximo passo?"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(chamadas[1]["args"][2], [])


if __name__ == "__main__":
    unittest.main()
