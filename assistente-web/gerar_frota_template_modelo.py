# Receita enviada pelo usuario em 15/10/2026 para montar o relatorio Word de Controle de Frota
# a partir de um modelo (tpl.docx = o relatorio anterior), clonando os elementos dele para manter
# o estilo. Precisa de python-docx (NAO instalado no venv do projeto).
#
# Indices dos elementos do modelo (body): title=0, meta=1, src=2, h1=3, bul=4, ital=12, norm=15, bold=16;
# tabela tipo 1 = elemento 10, tabela tipo 2 = elemento 13; o ultimo elemento e o sectPr.
# Uso: P('h1', 'Resumo'); P('bul', 'texto'); TB(tbl1, [cabecalho], [[linha], ...]).
# Gravar em Controle_Frota_Cobli_AAAA-MM-DD.docx (fim de semana: Controle_Frota_Cobli_AAAA-MM-DD_a_DD.docx).

import copy
from docx import Document
d = Document('tpl.docx')
body = d.element.body
els = list(body.iterchildren())
T = {k: copy.deepcopy(els[i]) for k, i in dict(title=0,meta=1,src=2,h1=3,bul=4,ital=12,norm=15,bold=16).items()}
tbl1 = copy.deepcopy(els[10]); tbl2 = copy.deepcopy(els[13])
sect = els[-1]
for e in els[:-1]: body.remove(e)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def settext(el, text):
    ts = el.findall('.//' + W + 't')
    ts[0].text = text; ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for t in ts[1:]: t.text = ''
def P(kind, text):
    e = copy.deepcopy(T[kind]); settext(e, text); sect.addprevious(e)
def TB(tpl, header, rows):
    t = copy.deepcopy(tpl); trs = t.findall(W+'tr'); hdr, row = trs[0], trs[1]
    for tr in trs[1:]: t.remove(tr)
    for c, txt in zip(hdr.findall(W+'tc'), header): settext(c, txt)
    for r in rows:
        nr = copy.deepcopy(row)
        for c, txt in zip(nr.findall(W+'tc'), r): settext(c, txt)
        t.append(nr)
    sect.addprevious(t)
# ... conteudo ...
d.save('Controle_Frota_Cobli_AAAA-MM-DD.docx')
