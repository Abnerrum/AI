"""Smoke tests with synthetic data. No financial data is stored in the repository."""
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["ADMIN_PASSWORD"] = "SenhaApenasParaTestes!"
os.environ["SECRET_KEY"] = "b" * 64
sys.path.insert(0, str(ROOT))
import app

class WebTests(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(app.app)
        self.assertEqual(self.c.get("/api/records").status_code, 401)
        self.c.post("/login", data={"username":"admin","password":"SenhaApenasParaTestes!"})
        html = self.c.get("/").text
        self.token = re.search(r'const CSRF_TOKEN = "([a-f0-9]+)";', html).group(1)

    def test_import_and_deduplicate(self):
        csv = ("Data;Categoria;Descrição;Valor (R$);Status BI;Tipo de atendimento\n"
               "01/11/2026;Locação;Teste fictício;1.234,56;Incluir;Garantia\n"
               "01/11/2026;Infrações;Ignorar;50,00;Não;Fora de Garantia\n").encode()
        opts = {"headers":{"X-CSRF-Token":self.token}}
        first = self.c.post("/api/import", files={"file":("base.csv", io.BytesIO(csv), "text/csv")}, **opts)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["resultado"]["novas"],1)
        second = self.c.post("/api/import", files={"file":("base.csv",io.BytesIO(csv),"text/csv")},**opts)
        self.assertEqual(second.json()["resultado"]["novas"],0)

    def test_manual_requires_csrf(self):
        data={"data":"2026-11-12","categoria":"Pedágio","descricao":"Teste", "valor":"25.60"}
        self.assertEqual(self.c.post("/api/manual",json=data).status_code,403)
        good=self.c.post("/api/manual",json=data,headers={"X-CSRF-Token":self.token})
        self.assertEqual(good.status_code,201)
        self.assertEqual(good.json()["registro"]["valor"],25.6)

    def test_logout_and_private_routes(self):
        self.assertEqual(self.c.post("/logout",data={"csrf_token":self.token},follow_redirects=False).status_code,303)
        self.assertEqual(self.c.get("/api/records").status_code,401)

if __name__ == "__main__": unittest.main()
