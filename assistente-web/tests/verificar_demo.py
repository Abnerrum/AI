"""Teste de integracao: execute DEMO.bat antes; dados usados apenas no demo."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import banco, executor
from openpyxl import load_workbook
import threading
from werkzeug.serving import make_server
from demo_site.app import app
server=make_server('127.0.0.1', 5000, app)
threading.Thread(target=server.serve_forever, daemon=True).start()

def cmd(acao, **params):
    r=executor.executar({'acao':acao,'usuario':'teste_demo','params':params})
    assert r.get('ok'), r
    return r['resultado']

with tempfile.TemporaryDirectory() as t:
    banco.DB_PATH=str(Path(t)/'teste.db');banco.inicializar()
    try:
        cmd('abrir_navegador',headless=True)
        cmd('abrir_url',url='http://127.0.0.1:5000/login',esperar_ms=0)
        page=executor._navegadores['teste_demo'].pagina
        page.locator('#usuario').fill('admin');page.locator('#senha').fill('1234')
        page.locator('button[type=submit]').click()
        r=cmd('extrair_com_paginacao',seletor='#tabela-ordens',seletor_proximo='#btn-proximo',max_paginas=10)
        assert r['total']==67, r
        # Prova que a ultima pagina nao e clicada e todas as 67 linhas sao preservadas.
        r=cmd('gerar_excel',nome_arquivo='teste_demo.xlsx')
        w=load_workbook(r['arquivo']);assert w.active.max_row==68
        Path(r['arquivo']).unlink()
        cmd('abrir_url',url='http://127.0.0.1:5000/nova-ordem',esperar_ms=0)
        cmd('preencher_formulario',campos={'#cliente':'Empresa ABC Ltda','#tecnico':'Carlos Silva','#descricao':'Teste automatizado local','#valor':'350,00'},seletor_form='#form-nova-ordem')
        executor.configurar_confirmacao(lambda previa: True)
        r=cmd('submeter_formulario',chave_unica='teste-demo-1',texto_sucesso='criada com sucesso')
        assert r['sucesso']
        assert banco.lancamento_existe('teste_demo','teste-demo-1')
        print('OK: login demo, 67 registros em 7 paginas, Excel e envio verificado.')
    finally:
        executor.fechar_todos()
        server.shutdown()
