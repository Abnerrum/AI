import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import compartilhar_permanente as compartilhar


class CompartilharPermanenteTest(unittest.TestCase):
    def test_valida_hostname_completo(self):
        self.assertEqual(
            compartilhar.validar_hostname(" Assistente.Exemplo.com. "),
            "assistente.exemplo.com",
        )
        for hostname in (
            "",
            "https://assistente.exemplo.com",
            "localhost",
            "assistente.exemplo.com/caminho",
            "-assistente.exemplo.com",
        ):
            with self.subTest(hostname=hostname), self.assertRaises(ValueError):
                compartilhar.validar_hostname(hostname)

    def test_cria_configuracao_com_hostname_e_credencial(self):
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            id_tunel = "12345678-1234-1234-1234-123456789abc"
            (pasta / f"{id_tunel}.json").write_text("{}", encoding="utf-8")

            config = compartilhar.criar_configuracao(
                "assistente.exemplo.com", id_tunel, pasta,
            )

            texto = config.read_text(encoding="utf-8")
            self.assertIn(f"tunnel: {id_tunel}", texto)
            self.assertIn("hostname: assistente.exemplo.com", texto)
            self.assertIn("service: http://127.0.0.1:5050", texto)
            self.assertEqual(
                compartilhar.obter_hostname(config),
                "assistente.exemplo.com",
            )

    def test_recusa_criar_configuracao_sem_credencial(self):
        with tempfile.TemporaryDirectory() as temporario:
            with self.assertRaises(FileNotFoundError):
                compartilhar.criar_configuracao(
                    "assistente.exemplo.com",
                    "12345678-1234-1234-1234-123456789abc",
                    Path(temporario),
                )

    def test_reutiliza_tunel_existente_por_nome(self):
        id_tunel = "12345678-1234-1234-1234-123456789abc"
        resultado = type(
            "Resultado",
            (),
            {"stdout": json.dumps([{"name": "assistente-web", "id": id_tunel}])},
        )()
        with patch.object(compartilhar.subprocess, "run", return_value=resultado) as run:
            obtido = compartilhar.obter_ou_criar_tunel("cloudflared")

        self.assertEqual(obtido, id_tunel)
        self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
