import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

keyring_falso = types.ModuleType("keyring")
keyring_falso.get_password = lambda servico, usuario: "segredo-teste"
keyring_falso.set_password = lambda servico, usuario, valor: None
with patch.dict(sys.modules, {"keyring": keyring_falso}):
    import painel


class CompartilharRelatoriosTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.temp.name)
        self.relatorios = self.pasta / "relatorios"
        self.compartilhamentos = self.pasta / "compartilhamentos.json"
        (self.relatorios / "operacional").mkdir(parents=True)
        (self.relatorios / "operacional" / "relatorio-teste.html").write_text(
            "<h1>Relatorio publico</h1>", encoding="utf-8"
        )
        self.patch_relatorios = patch.object(painel, "RELATORIOS", str(self.relatorios))
        self.patch_compartilhamentos = patch.object(
            painel, "COMPARTILHAMENTOS", str(self.compartilhamentos)
        )
        self.patch_relatorios.start()
        self.patch_compartilhamentos.start()
        self.addCleanup(self.patch_relatorios.stop)
        self.addCleanup(self.patch_compartilhamentos.stop)
        self.addCleanup(self.temp.cleanup)
        self.cliente = painel.app.test_client()

    def administrador(self):
        with self.cliente.session_transaction() as sessao:
            sessao["ok"] = True
            sessao["perfil"] = "admin"

    def test_link_publico_acessa_somente_relatorio_e_pode_ser_revogado(self):
        self.administrador()
        criado = self.cliente.post(
            "/api/compartilhamentos",
            json={"agente": "operacional", "nome": "relatorio-teste.html"},
            headers={"X-Painel": "1", "X-Forwarded-Proto": "https"},
        )
        self.assertEqual(criado.status_code, 200)
        token = criado.json["token"]
        self.assertEqual(len(token), 43)
        self.assertEqual(
            criado.json["url"], f"https://localhost/compartilhado/{token}"
        )
        lista = self.cliente.get("/api/compartilhamentos")
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(lista.json["compartilhamentos"][0]["token"], token)

        anonimo = painel.app.test_client()
        anonimo.environ_base["REMOTE_ADDR"] = "192.168.1.25"
        resposta = anonimo.get(f"/compartilhado/{token}")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Relatorio publico", resposta.get_data(as_text=True))
        self.assertIn("sandbox", resposta.headers["Content-Security-Policy"])
        self.assertEqual(resposta.headers["Cache-Control"], "no-store")
        resposta.close()
        self.assertEqual(anonimo.get("/").status_code, 302)

        sem_cabecalho = self.cliente.delete(
            "/api/compartilhamentos", json={"token": token}
        )
        self.assertEqual(sem_cabecalho.status_code, 403)
        revogado = self.cliente.delete(
            "/api/compartilhamentos",
            json={"token": token},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(revogado.status_code, 200)
        self.assertEqual(anonimo.get(f"/compartilhado/{token}").status_code, 404)

    def test_nao_cria_link_para_arquivo_inexistente_ou_departamento_nao_permitido(self):
        self.administrador()
        inexistente = self.cliente.post(
            "/api/compartilhamentos",
            json={"agente": "operacional", "nome": "ausente.html"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(inexistente.status_code, 404)
        departamento = self.cliente.post(
            "/api/compartilhamentos",
            json={"agente": "rh", "nome": "relatorio-teste.html"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(departamento.status_code, 400)

    def test_perfil_rh_nao_pode_listar_ou_criar_links_publicos(self):
        with self.cliente.session_transaction() as sessao:
            sessao["ok"] = True
            sessao["perfil"] = "rh"
        self.assertEqual(self.cliente.get("/api/compartilhamentos").status_code, 403)
        resposta = self.cliente.post(
            "/api/compartilhamentos",
            json={"agente": "operacional", "nome": "relatorio-teste.html"},
            headers={"X-Painel": "1"},
        )
        self.assertEqual(resposta.status_code, 403)


if __name__ == "__main__":
    unittest.main()
