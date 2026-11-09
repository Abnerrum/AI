import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import banco, executor, relatorio
import pytest
from openpyxl import load_workbook

@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(banco, 'DB_PATH', str(tmp_path / 'teste.db'))
    banco.inicializar()
    executor._navegadores.clear()
    executor._dados.clear()
    executor._previa.clear()
    executor.configurar_confirmacao(None)

@pytest.mark.parametrize('cmd', [[], None, 3, {'acao':3}, {'acao':'status','usuario':'../outro'}, {'acao':'status','params':[]}])
def test_comando_invalido(cmd):
    assert 'erro' in executor.executar(cmd)

def test_historico_nao_muta_nem_registra_segredos():
    cmd={'params':{'campos':{'#senha':'segredo'}}}
    banco.registrar_historico('abner','preencher_formulario',cmd,resultado='token privado')
    assert cmd['params']['campos']['#senha']=='segredo'
    assert 'segredo' not in str(banco.consultar_historico('abner'))
    assert 'privado' not in str(banco.consultar_historico('abner'))

def test_excel_local_e_isolamento(tmp_path):
    executor._dados['abner']=[{'Cliente':'=1+1','Status':'Pendente'}]
    assert 'erro' in executor.executar({'acao':'gerar_excel','usuario':'outro'})
    arquivo=relatorio.gerar_excel(executor._dados['abner'],str(tmp_path/'teste.xlsx'),colunas=['Status','Cliente'],titulo='Teste:/')
    w=load_workbook(arquivo)
    assert w.active['A1'].value=='Status'
    assert w.active['B2'].data_type=='s'
    assert w.active['B2'].value=="'=1+1"
    with pytest.raises(ValueError):
        relatorio.gerar_excel([{'a':1}],str(tmp_path/'erro.xlsx'),colunas=['ausente'])

def test_fluxo_sem_confirmacao_nao_envia():
    class Fake:
        def url_atual(self):return 'http://localhost/form'
        def validar_previa(self,*args):pass
        def verificar_sucesso(self,*args):return {"sucesso":False}
        def submeter_formulario(self,*args):raise AssertionError('nao deve enviar')
    executor._navegadores['abner']=Fake()
    executor._previa['abner']={'url':'http://localhost/form','form':'form','campos':{'#cliente':'A'}}
    banco.salvar_fluxo('envio','', [{'acao':'submeter_formulario','params':{'chave_unica':'x','texto_sucesso':'sucesso'}}])
    r=executor.executar({'acao':'executar_fluxo','usuario':'abner','params':{'nome':'envio'}})
    assert 'erro' in r and not banco.lancamento_existe('abner','x')

def test_resultado_incerto_bloqueia_reenvio():
    class Fake:
        envios=0
        def url_atual(self):return 'http://localhost/form'
        def validar_previa(self,*args):pass
        def submeter_formulario(self,*args):self.envios+=1
        def verificar_sucesso(self,*args):return {'sucesso':False}
    nav=Fake();executor._navegadores['abner']=nav
    prev={'url':nav.url_atual(),'form':'form','campos':{}}
    executor._previa['abner']=prev
    executor.configurar_confirmacao(lambda _: True)
    cmd={'acao':'submeter_formulario','usuario':'abner','params':{'chave_unica':'x','texto_sucesso':'sucesso'}}
    assert 'erro' in executor.executar(cmd)
    executor._previa['abner']=prev
    assert 'erro' in executor.executar(cmd)
    assert nav.envios==1

def test_fluxo_aninhado_recusado():
    r=executor.executar({'acao':'salvar_fluxo','params':{'nome':'loop','passos':[{'acao':'executar_fluxo','params':{'nome':'loop'}}]}})
    assert 'erro' in r
