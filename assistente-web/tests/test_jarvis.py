import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import jarvis_assistente as jarvis

cofre = {}
keyring_falso = types.ModuleType("keyring")
keyring_falso.get_password = lambda servico, usuario: cofre.get((servico, usuario))
keyring_falso.set_password = lambda servico, usuario, valor: cofre.__setitem__((servico, usuario), valor)
keyring_falso.delete_password = lambda servico, usuario: cofre.pop((servico, usuario), None)
with patch.dict(sys.modules, {"keyring": keyring_falso}):
    import painel


class JarvisInterpretacaoTest(unittest.TestCase):
    def test_interpreta_comandos_em_portugues_e_ingles(self):
        casos = {
            "Que horas são?": ("hora", "pt"),
            "What time is it?": ("hora", "en"),
            "Qual é a data de hoje?": ("data", "pt"),
            "Tell me today's date": ("data", "en"),
            "Conte uma piada": ("piada", "pt"),
            "Tell me a joke": ("piada", "en"),
            "Pesquise na Wikipédia sobre inteligência artificial": ("wikipedia", "pt"),
            "Search Wikipedia about artificial intelligence": ("wikipedia", "en"),
            "Anote ligar para o fornecedor às 15h": ("anotar", "pt"),
            "Remember to call the supplier": ("anotar", "en"),
            "Tocar música": ("musica", "pt"),
            "Play music": ("musica", "en"),
            "Pesquisar no Google sobre Aquilix": ("google", "pt"),
            "Open youtube": ("abrir_site", "en"),
            "Capturar a tela": ("captura_tela", "pt"),
            "Restart the computer": ("reiniciar", "en"),
            "Desligar o computador": ("desligar", "pt"),
            "Cancelar desligamento": ("cancelar_desligamento", "pt"),
            "Parar de ouvir": ("parar_voz", "pt"),
            "Go offline": ("parar_voz", "en"),
        }
        for comando, esperado in casos.items():
            with self.subTest(comando=comando):
                resultado = jarvis.interpretar(comando)
                self.assertEqual((resultado["acao"], resultado["idioma"]), esperado)

    def test_nao_interpreta_texto_generico_como_comando(self):
        self.assertIsNone(jarvis.interpretar("Olá, você pode me ajudar?"))

    def test_pesquisa_sem_assunto_retorna_erro_util(self):
        with self.assertRaisesRegex(ValueError, "assunto"):
            jarvis.interpretar("Pesquise na Wikipédia")

    def test_site_privado_e_bloqueado(self):
        with self.assertRaisesRegex(ValueError, "rede privada"):
            jarvis.abrir_site("http://127.0.0.1")

    def test_energia_usa_argumentos_fechados_e_shell_desativado(self):
        with (
            patch.object(jarvis.os, "name", "nt"),
            patch.object(jarvis.subprocess, "Popen") as executar,
        ):
            jarvis.agendar_energia("desligar")
        executar.assert_called_once_with(
            ["shutdown", "/s", "/t", "60", "/c", "AQUILIX: desligamento confirmado localmente"],
            shell=False,
        )


class JarvisApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        self.patches = [
            patch.object(painel, "AGENTES_DIR", str(self.pasta / "agentes")),
            patch.object(painel, "ANEXOS", str(self.pasta / "anexos")),
            patch.dict(painel.atuais, {}, clear=True),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.cliente = painel.app.test_client()
        with self.cliente.session_transaction() as sessao:
            sessao["ok"] = True
            sessao["perfil"] = "admin"

    def tearDown(self):
        self.temp.cleanup()

    def test_notas_ficam_separadas_por_departamento(self):
        resposta = self.cliente.post(
            "/api/jarvis/notas",
            json={"agente": "financeiro", "texto": "Conferir a nota fiscal"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["nota"]["texto"], "Conferir a nota fiscal")
        consulta = self.cliente.get("/api/jarvis/notas?agente=operacional")
        self.assertEqual(consulta.json["notas"], [])

    def test_comando_de_energia_exige_confirmacao(self):
        with patch.object(jarvis, "agendar_energia") as agendar:
            resposta = self.cliente.post(
                "/api/jarvis",
                json={"agente": "operacional", "comando": "Shutdown this computer"},
                headers={"X-Painel": "1"},
            )
        self.assertEqual(resposta.status_code, 409)
        self.assertTrue(resposta.json["confirmacao_necessaria"])
        self.assertEqual(resposta.json["idioma"], "en")
        agendar.assert_not_called()

    def test_comando_em_ingles_retorna_idioma_para_a_interface(self):
        resposta = self.cliente.post(
            "/api/jarvis",
            json={"agente": "operacional", "comando": "What time is it?"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["idioma"], "en")
        self.assertTrue(resposta.json["resposta"].startswith("The time is "))

    def test_comando_de_pc_e_bloqueado_atraves_do_tunel(self):
        with patch.object(jarvis, "agendar_energia") as agendar:
            resposta = self.cliente.post(
                "/api/jarvis",
                json={"agente": "operacional", "comando": "Desligar o computador", "confirmado": True},
                headers={"X-Painel": "1", "Cf-Connecting-Ip": "203.0.113.15"},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )
        self.assertEqual(resposta.status_code, 403)
        agendar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
