"""Regressoes de inicializacao; apenas biblioteca padrao."""
import contextlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import preparar

class InicializacaoTest(unittest.TestCase):
    def test_ambiente_pronto_nao_executa_instaladores(self):
        with tempfile.TemporaryDirectory() as temp:
            chromium = Path(temp) / 'chrome'
            chromium.touch()
            navegador = types.SimpleNamespace(chromium=types.SimpleNamespace(executable_path=str(chromium)))
            api = types.ModuleType('playwright.sync_api')
            api.sync_playwright = lambda: contextlib.nullcontext(navegador)
            versoes = dict(l.split('==') for l in (ROOT/'requirements.txt').read_text().splitlines() if l.strip())
            with (
                patch.dict(sys.modules, {'playwright': types.ModuleType('playwright'), 'playwright.sync_api': api}),
                patch.object(preparar, 'version', side_effect=versoes.__getitem__),
                patch.object(preparar.importlib, 'import_module'),
                patch.object(preparar.subprocess, 'run') as run,
            ):
                preparar.preparar()
                run.assert_not_called()

    def test_dependencia_incompleta_e_reinstalada(self):
        for modulo, pacote, versao in (
            ('cryptography.exceptions', 'cryptography', '50.0.2'),
            ('pywintypes', 'pywin32', '312'),
        ):
            with self.subTest(pacote=pacote):
                with (
                    patch.object(
                        preparar.importlib,
                        'import_module',
                        side_effect=[ModuleNotFoundError(), object()],
                    ) as importar,
                    patch.object(preparar.subprocess, 'run') as run,
                ):
                    preparar.verificar_dependencia(modulo, pacote, versao)
                self.assertEqual(importar.call_count, 2)
                run.assert_called_once_with(
                    [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                     '--force-reinstall', '--no-deps', f'{pacote}=={versao}'],
                    check=True,
                )

    def test_url_abre_navegador_automaticamente(self):
        with patch.dict(sys.modules, {'keyring': types.ModuleType('keyring')}):
            import executor
        executor._navegadores.clear()
        with patch.object(executor, 'Navegador') as cls:
            cls.return_value.abrir_url.return_value = {'url': 'https://exemplo.com'}
            with patch.object(executor.banco, 'registrar_historico'):
                for _ in range(2):
                    r = executor.executar({'acao': 'abrir_url', 'params': {'url': 'https://exemplo.com'}})
                    self.assertTrue(r['ok'])
            cls.return_value.iniciar.assert_called_once_with(headless=False)
        executor._navegadores.clear()

    def test_cli_mostra_prompt_sem_excel_ou_playwright(self):
        # keyring e simulado; as bibliotecas pesadas permanecem ausentes.
        codigo = '''import sys, types, runpy
sys.modules['keyring'] = types.ModuleType('keyring')
runpy.run_path('assistente.py', run_name='__main__')
assert 'pandas' not in sys.modules
assert 'openpyxl' not in sys.modules
assert 'playwright.sync_api' not in sys.modules
'''
        r = subprocess.run([sys.executable, '-c', codigo], cwd=ROOT, input='sair\n', text=True, capture_output=True, timeout=5)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('[COMANDO]', r.stdout)

if __name__ == '__main__':
    unittest.main()
