"""Gera o relatorio Word de Controle de Frota clonando o estilo de um relatorio anterior (modelo).

Uso: python gerar_frota_com_modelo.py modelo.docx saida.docx
Indices do modelo Controle_Frota_Cobli_2026-10-14 (usuario):
 0 titulo, 1 meta, 2 fonte, 3 'Resumo', 4 bullet, 10 titulo numerado, 13 paragrafo normal,
 16 paragrafo normal, 18 negrito ('Veiculos na oficina:'), 19 bullet da oficina, 23 italico,
 27 subtitulo ('Ocorrencias justificadas:'), 28 bullet das ocorrencias,
 tabelas: 11 (uso apos 19h), 14 (pernoite), 22 (checklist), 25 (km, com linha Total no fim).
"""
import copy
import sys
from docx import Document

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XML = '{http://www.w3.org/XML/1998/namespace}space'

d = Document(sys.argv[1])
body = d.element.body
els = list(body.iterchildren())
T = {k: copy.deepcopy(els[i]) for k, i in dict(
    title=0, meta=1, src=2, h1=3, bul=4, h2=10, norm=13, para=16, bold=18, bul2=19, ital=23, sub=27, bul3=28).items()}
TBL = {k: copy.deepcopy(els[i]) for k, i in dict(uso=11, pern=14, chk=22, km=25).items()}
sect = els[-1]
for e in els[:-1]:
    body.remove(e)


def settext(el, text):
    ts = el.findall('.//' + W + 't')
    ts[0].text = text
    ts[0].set(XML, 'preserve')
    for t in ts[1:]:
        t.text = ''


def P(kind, text):
    e = copy.deepcopy(T[kind])
    settext(e, text)
    sect.addprevious(e)


def TB(name, header, rows, total=None):
    t = copy.deepcopy(TBL[name])
    trs = t.findall(W + 'tr')
    hdr, row, last = trs[0], trs[1], trs[-1]
    for tr in trs[1:]:
        t.remove(tr)
    for c, txt in zip(hdr.findall(W + 'tc'), header):
        settext(c, txt)
    for r in rows:
        nr = copy.deepcopy(row)
        for c, txt in zip(nr.findall(W + 'tc'), r):
            settext(c, txt)
        t.append(nr)
    if total:
        nr = copy.deepcopy(last)
        for c, txt in zip(nr.findall(W + 'tc'), total):
            settext(c, txt)
        t.append(nr)
    sect.addprevious(t)


P('title', 'Rotina Diária – Controle de Frota (Cobli)')
P('meta', 'Data analisada: 14/10/2026 (quarta-feira)   |   Emitido em: 15/10/2026')
P('src', 'Fonte: Cobli – relatório Trajetos e paradas detalhado; responsáveis conforme o "Checklist do VEICULO - CSP GOIANIA" e as regras de responsáveis fixos. Critérios: uso após as 19h00 e pernoite fora dos pátios da empresa – Pátio 1 CSP (Rua 8, 440 – Setor Oeste) e Pátio 2 AXT (Rua 86, 655 – Setor Sul), Goiânia-GO.')

P('h1', 'Resumo')
for t in [
    '10 veículos com atividade no dia (TEU2D25 e TFY9F33 na oficina, sem movimentação).',
    '4 veículos com uso após as 19h: TXI5B84, TEW0F04, TEW0F24 e TEW0F15 – todos justificados.',
    '6 pernoitaram fora dos pátios: TEW0F04, TEW0F14, TEW0F15 (Matheus), TEW0F24, TEX0E56 (Gero) e TXI5B84 – todos justificados.',
    'Nenhum veículo se movimentou entre 00h00 e 06h30 de 14/10 (primeira saída às 06:49).',
    '2 veículos na oficina: TEU2D25 (motor/retífica) e TFY9F33 – Scudo (troca de disco e pastilhas de freio).',
    'As ocorrências estão justificadas. 1 a conferir: TXA3E97 parou na Rua 86, 765 (a Via 86 é no 655) – verificar se está dentro do raio de 200 m.',
]:
    P('bul', t)

P('h2', '1. Uso após as 19h00')
TB('uso', ['Veículo', 'Responsável', 'Trajeto(s)', 'Justificativa / observação'], [
    ['TXI5B84 – Fiorino (VNB5)', 'Reyner', '18:55→19:00 (0,9 km); 19:13→19:16 (0,7 km); 19:24→19:40 (7,3 km); 21:15→21:36 (7,3 km)', 'Justificado: veículo com o Reyner; trajetos curtos terminando no "Ponto de Pernoite e Retorno"'],
    ['TEW0F04 – Fiorino (RM3I)', 'Alexandre Carvalho do Vale', '17:43→19:28 (120,5 km); 20:41→20:55 (3,5 km); 22:07→22:17 (3,5 km)', 'Justificado: retorno de viagem ao interior (~443 km no dia); pernoitou na região de Pires do Rio-GO'],
    ['TEW0F24 – Fiorino (W9I3)', 'João Paulo Rodrigo Silva', '19:25→19:37 (4,9 km); 19:41→19:48 (3,5 km)', 'Justificado: autorização do Gero; chegou à Base de Pernoite às 19:48'],
    ['TEW0F15 – Fiorino (XV3D)', 'Matheus Rodrigues Cipriano', '18:33→19:08 (10,2 km)', 'Justificado: Matheus Rodrigues Cipriano; pernoitou na Rua dos Albatrozes – Morada dos Pássaros (Aparecida de Goiânia-GO)'],
])

P('h2', '2. Pernoite fora dos pátios')
P('norm', 'Nenhum veículo se movimentou entre 00h00 e 06h30 de 14/10/2026.')
TB('pern', ['Veículo', 'Responsável', 'Local do pernoite', 'Distância / justificativa'], [
    ['TEW0F04 – Fiorino (RM3I)', 'Alexandre Carvalho do Vale', '-17.7728, -48.6274 – região de Pires do Rio-GO', '~172 km do CSP; parado após 22:17 – Justificado: retorno de viagem ao interior'],
    ['TEW0F14 – Fiorino (XUYY)', 'Jovenildo de Oliveira', 'Rua Amazonas, 695 – Setor Montes Belos, São Luís de Montes Belos-GO (-16.5109, -50.3700)', '~128 km do CSP; parado desde 18:05 – Justificado: viagem ao interior'],
    ['TEW0F15 – Fiorino (XV3D)', 'Matheus Rodrigues Cipriano', 'Rua dos Albatrozes – Morada dos Pássaros, Aparecida de Goiânia-GO', 'Fora da base; parado desde 19:08 – Justificado: Matheus Rodrigues Cipriano'],
    ['TEW0F24 – Fiorino (W9I3)', 'João Paulo Rodrigo Silva', 'Rua Amazonas – Setor Aeroporto Sul 2ª Etapa, Aparecida de Goiânia-GO (-16.8050, -49.3529)', '~16 km do CSP; chegou às 19:48 – Justificado: autorização do Gero'],
    ['TEX0E56 – Mobi (Q7OO)', 'Gero', 'Rua A-19 – Vila Alpes, Goiânia-GO (casa do Gero)', 'Parado desde 18:03 (até 07:10 de 15/10) – Justificado: pernoite na casa do Gero, uso autorizado'],
    ['TXI5B84 – Fiorino (VNB5)', 'Reyner', 'Rua T-38, 738 – Setor Bueno, Goiânia-GO (-16.7135, -49.2680)', '~3 km do CSP; parado após 21:36 – Justificado: veículo com o Reyner (autorizado)'],
])

P('h2', '3. Veículos regulares')
P('para', 'Pernoite na base e sem uso após as 19h: TEU2C47 – Saveiro (VNB9) – Reyner (64,5 km, 16 trajetos, parou às 17:42 na Rua 86, 655 – Via 86); TEW0F17 – Fiorino (V8BK) – Frederiko (42,0 km, 11 trajetos, parou às 17:06 na Rua 8 – Setor Oeste); TEX0E24 – Mobi (W6F1) – Luiz Eduardo (35,7 km, 5 trajetos, parou às 17:49 na Rua 8 – Setor Oeste).')
P('para', 'A conferir: TXA3E97 – Fiorino (W9HM) – Rodrigo (38,0 km, 14 trajetos): parou às 17:46 na Rua 86, 765 – Setor Sul; a Via 86 é no 655, então é preciso confirmar se fica dentro do raio de 200 m da base.')
P('para', 'TEX0E56 – Mobi (Q7OO) – Gero: 29,8 km (10 trajetos até 18:03); pernoitou na casa do Gero, Rua A-19 – Vila Alpes (ver seção 2).')
P('bold', 'Veículos na oficina:')
P('bul2', 'TEU2D25 – Saveiro (XB5R): motor de partida queimado; ruído no motor – em avaliação para retífica. Sem movimentação.')
P('bul2', 'TFY9F33 – Scudo (VNO5): troca de disco e pastilhas de freio. Sem movimentação.')

P('h2', '4. Checklist do dia (14/10)')
TB('chk', ['Veículo', 'Motorista no checklist', 'Envio', 'Situação'], [
    ['TEW0F04 – Fiorino (RM3I)', 'Alexandre Carvalho do Vale', '09:29', 'Feito'],
    ['TEW0F17 – Fiorino (V8BK)', 'Frederiko Ferreira de Siqueira', '09:19', 'Feito'],
    ['TEW0F24 – Fiorino (W9I3)', 'João Paulo Rodrigo Silva', '09:02', 'Feito'],
    ['TXA3E97 – Fiorino (W9HM)', 'Rodrigo Neves Junior', '08:57', 'Feito'],
    ['TEW0F14 – Fiorino (XUYY)', 'Jovenildo de Oliveira', '08:32', 'Feito'],
    ['TEU2C47 – Saveiro (VNB9)', 'Reyner', '08:28', 'Feito'],
    ['TXI5B84 – Fiorino (VNB5)', 'Reyner', '08:27', 'Feito'],
    ['TEW0F15 – Fiorino (XV3D)', 'Matheus Rodrigues Cipriano', '—', 'Não feito (rodou 90,0 km)'],
    ['TEX0E24 – Mobi (W6F1)', '—', '—', 'Não feito (rodou 35,7 km)'],
    ['TEX0E56 – Mobi (Q7OO)', '—', '—', 'Não feito (rodou 29,8 km)'],
    ['TEU2D25 – Saveiro (XB5R)', '—', '—', 'Na oficina – sem movimentação'],
    ['TFY9F33 – Scudo (VNO5)', '—', '—', 'Na oficina – sem movimentação'],
])
P('ital', 'Todos os checklists enviados constam como "Sem conformidade".')

P('h2', '5. Quilometragem do dia')
TB('km', ['Veículo', 'Motorista', 'Trajetos', 'Distância'], [
    ['TEW0F04 – Fiorino (RM3I)', 'Alexandre Carvalho do Vale', '19', '443,5 km'],
    ['TEW0F14 – Fiorino (XUYY)', 'Jovenildo de Oliveira', '10', '180,6 km'],
    ['TEW0F24 – Fiorino (W9I3)', 'João Paulo Rodrigo Silva', '14', '138,9 km'],
    ['TEW0F15 – Fiorino (XV3D)', 'Matheus Rodrigues Cipriano', '16', '90,0 km'],
    ['TXI5B84 – Fiorino (VNB5)', 'Reyner', '15', '80,2 km'],
    ['TEU2C47 – Saveiro (VNB9)', 'Reyner', '16', '64,5 km'],
    ['TEW0F17 – Fiorino (V8BK)', 'Frederiko Ferreira de Siqueira', '11', '42,0 km'],
    ['TXA3E97 – Fiorino (W9HM)', 'Rodrigo Neves Junior', '14', '38,0 km'],
    ['TEX0E24 – Mobi (W6F1)', 'Luiz Eduardo', '5', '35,7 km'],
    ['TEX0E56 – Mobi (Q7OO)', 'Gero', '10', '29,8 km'],
], total=['Total', '', '130', '1.143,2 km (trajetos iniciados em 14/10; retornos de 15/10 ficam fora)'])

P('h2', '6. Pontos de atenção')
P('sub', 'Ocorrências justificadas:')
for t in [
    'TEW0F04 – Alexandre em viagem longa ao interior (~443 km no dia); uso após 19h e pernoite em Pires do Rio-GO justificados.',
    'TEW0F14 – Jovenildo em viagem ao interior (São Luís de Montes Belos-GO, ~181 km no dia); pernoite fora justificado.',
    'TEW0F24 – João Paulo com autorização do Gero; pernoitou na Base de Pernoite.',
    'TEX0E56 – Gero; pernoite na casa do Gero (~4,2 km do CSP) – justificado.',
    'TXI5B84 – Reyner; uso após 19h e pernoite no Ponto de Pernoite e Retorno – justificado.',
]:
    P('bul3', t)
P('sub', 'Pendências:')
P('bul3', 'TXA3E97 – Rodrigo; parou às 17:46 na Rua 86, 765 – Setor Sul. A Via 86 é no 655: conferir se está dentro dos 200 m da base. Se não estiver, vira pernoite fora e precisa de justificativa.')
P('bul3', 'TEW0F15 – Matheus Rodrigues Cipriano; rodou 90,0 km e pernoitou na Rua dos Albatrozes, Morada dos Pássaros (Aparecida de Goiânia-GO); sem checklist no dia. Confirmar que o condutor foi o Matheus (a regra geral do veículo é Gero).')
P('bul3', 'TEX0E24 (Luiz Eduardo) e TEX0E56 (Gero) – sem checklist no dia.')
P('sub', 'Oficina:')
P('bul3', 'TEU2D25 – Saveiro (XB5R): motor de partida queimado, ruído no motor – em avaliação para retífica.')
P('bul3', 'TFY9F33 – Scudo (VNO5): troca de disco e pastilhas de freio.')

d.save(sys.argv[2])
print('ok', sys.argv[2])
