"""Smoke tests with synthetic data. No financial data is stored in the repository."""
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy.dialects import mysql

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

    def test_xlsx_original_is_stored_and_downloadable(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "BI_GRAFICOS"
        sheet.append(["Data", "Categoria", "Descrição", "Valor (R$)"])
        sheet.append(["01/11/2026", "Combustível", "Teste fictício", 32.5])
        content = io.BytesIO()
        workbook.save(content)
        original = content.getvalue()
        response = self.c.post(
            "/api/import",
            files={"file": ("relatorio.xlsx", io.BytesIO(original),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers={"X-CSRF-Token": self.token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["resultado"]["arquivo_original_guardado"])

        stored = self.c.get("/api/excel-files").json()["arquivos"]
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["nome"], "relatorio.xlsx")
        downloaded = self.c.get(f"/api/excel-files/{stored[0]['id']}")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, original)

        repeated = self.c.post(
            "/api/import",
            files={"file": ("relatorio.xlsx", io.BytesIO(original),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers={"X-CSRF-Token": self.token},
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertTrue(repeated.json()["resultado"]["arquivo_original_ja_existia"])
        self.assertEqual(len(self.c.get("/api/excel-files").json()["arquivos"]), 1)

    def test_mysql_insert_and_excel_blob_types_compile(self):
        statement = app.mysql_insert(app.Despesa).values(
            chave="teste", categoria="Teste", valor_centavos=100
        )
        statement = statement.on_duplicate_key_update(chave=statement.inserted.chave)
        self.assertIn("ON DUPLICATE KEY UPDATE", str(statement.compile(dialect=mysql.dialect())))
        blob_type = mysql.dialect().type_compiler.process(
            app.ArquivoExcel.__table__.c.conteudo.type
        )
        self.assertEqual(blob_type, "LONGBLOB")

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
