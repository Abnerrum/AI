import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
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


class LimiteClaudeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        self.uso = self.pasta / "uso_claude.json"
        self.conversa = self.pasta / "conversa.json"
        self.aprendizado = self.pasta / "APRENDIZADO.md"
        self.aprendizado.write_text("# Aprendizado\n", encoding="utf-8")
        patches = (
            patch.object(painel, "USO_CLAUDE", str(self.uso)),
            patch.object(painel, "CONVERSA", str(self.conversa)),
            patch.object(painel, "CONHECIMENTO", str(self.aprendizado)),
            patch.object(painel, "AGENTES_DIR", str(self.pasta / "agentes")),
            patch.object(painel, "LIMITE_DIARIO", 1),
            patch.dict(painel.atuais, {}, clear=True),
        )
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(self.temp.cleanup)

    def cliente(self):
        cliente = painel.app.test_client()
        with cliente.session_transaction() as sessao:
            sessao["ok"] = True
        return cliente

    def test_limite_padrao_ativo_com_contagem_diaria(self):
        with patch.object(painel, "LIMITE_DIARIO", 150):
            status = painel._status_uso_claude()
        self.assertTrue(status["habilitado"])
        self.assertEqual(status["limite"], 150)
        self.assertEqual(status["mensagens"], 0)
        self.assertFalse(status["bloqueado"])

    def test_contagem_reinicia_no_dia_seguinte_e_preserva_trava(self):
        ontem = (datetime.now().date() - timedelta(days=1)).isoformat()
        self.uso.write_text(
            json.dumps({"data": ontem, "mensagens": 1, "habilitado": False, "modelo": "haiku"}),
            encoding="utf-8",
        )
        status = painel._ler_uso_claude()
        self.assertEqual(status["mensagens"], 0)
        self.assertFalse(status["habilitado"])
        self.assertEqual(status["modelo"], "haiku")
        self.assertEqual(status["data"], datetime.now().date().isoformat())

    def test_api_limite_exige_sessao_e_confirma_estado(self):
        anonimo = painel.app.test_client()
        self.assertEqual(anonimo.get("/api/limite").status_code, 401)

        cliente = self.cliente()
        status = cliente.get("/api/limite")
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json["habilitado"])
        self.assertEqual(status.json["modelo"], "sonnet")

        resposta = cliente.post(
            "/api/limite",
            json={"habilitado": False},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.json["habilitado"])

        resposta = cliente.post(
            "/api/limite",
            json={"habilitado": "false"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 400)

    def test_api_persiste_modo_economico_e_rejeita_modelos_invalidos(self):
        cliente = self.cliente()

        resposta = cliente.post(
            "/api/limite",
            json={"modelo": "haiku"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["modelo"], "haiku")
        self.assertEqual(painel._ler_uso_claude()["modelo"], "haiku")

        for modelo in ("opus", [], {}):
            resposta = cliente.post(
                "/api/limite",
                json={"modelo": modelo},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 400)

        resposta = cliente.post(
            "/api/limite",
            json={"modelo": "sonnet"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(painel._ler_uso_claude()["modelo"], "sonnet")

    def test_bloqueia_ao_atingir_teto_e_desbloquear_libera_envio(self):
        chamadas = []

        class ThreadFalsa:
            def __init__(self, **opcoes):
                chamadas.append(opcoes)

            def start(self):
                pass

        cliente = self.cliente()
        with patch.object(painel.threading, "Thread", ThreadFalsa):
            resposta = cliente.post(
                "/api/mensagem",
                data={"texto": "Primeira mensagem"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(painel._ler_uso_claude()["mensagens"], 1)

            painel.atuais["operacional"].fim = True
            resposta = cliente.post(
                "/api/mensagem",
                data={"texto": "Bloqueada"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 429)
            self.assertTrue(resposta.json["uso_claude"]["bloqueado"])
            self.assertEqual(painel._ler_uso_claude()["mensagens"], 1)

            resposta = cliente.post(
                "/api/limite",
                json={"habilitado": False},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 200)

            resposta = cliente.post(
                "/api/mensagem",
                data={"texto": "Liberada"},
                headers={"X-Painel": "1"},
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(painel._ler_uso_claude()["mensagens"], 2)
        self.assertEqual(len(chamadas), 2)

    def test_mensagem_vazia_nao_consume_cota(self):
        cliente = self.cliente()
        resposta = cliente.post("/api/mensagem", headers={"X-Painel": "1"})
        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(self.uso.exists())


if __name__ == "__main__":
    unittest.main()
