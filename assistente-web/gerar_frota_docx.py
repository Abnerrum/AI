import sys
import zipfile
from xml.sax.saxutils import escape

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def run(text, bold=False, size=20, color=None):
    rpr = f'<w:sz w:val="{size}"/>'
    if bold:
        rpr = '<w:b/>' + rpr
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(text, bold=False, size=20, color=None, after=80):
    return f'<w:p><w:pPr><w:spacing w:after="{after}"/></w:pPr>{run(text, bold, size, color)}</w:p>'


def mixed(parts, after=80, bullet=False):
    runs = "".join(run(t, b) for t, b in parts)
    ind = '<w:ind w:left="360" w:hanging="200"/>' if bullet else ""
    pre = run("• ") if bullet else ""
    return f'<w:p><w:pPr><w:spacing w:after="{after}"/>{ind}</w:pPr>{pre}{runs}</w:p>'


def table(rows, widths):
    out = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>']
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        out.append(f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="999999"/>')
    out.append('</w:tblBorders></w:tblPr><w:tblGrid>')
    for w in widths:
        out.append(f'<w:gridCol w:w="{w}"/>')
    out.append('</w:tblGrid>')
    for i, r in enumerate(rows):
        out.append('<w:tr>')
        for j, c in enumerate(r):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="1F4E78"/>' if i == 0 else ""
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[j]}" w:type="dxa"/>{shade}</w:tcPr>'
                       f'{para(c, bold=(i == 0), size=17, color=("FFFFFF" if i == 0 else None), after=0)}</w:tc>')
        out.append('</w:tr>')
    out.append('</w:tbl>' + para("", after=60))
    return "".join(out)


B = []
B.append(para("Rotina Diária – Controle de Frota (Cobli)", True, 34, "1F4E78", 120))
B.append(para("Data analisada: 14/10/2026 (quarta-feira)   |   Emitido em: 15/10/2026", True, 20))
B.append(para('Fonte: Cobli – relatório Trajetos e paradas detalhado; responsáveis conforme o "Checklist do VEICULO - CSP GOIANIA" e as regras de responsáveis fixos. Critérios: uso após as 19h00 e pernoite fora dos pátios da empresa – Pátio 1 CSP (Rua 8, 440 – Setor Oeste) e Pátio 2 AXT (Rua 86, 655 – Setor Sul), Goiânia-GO.', False, 18))

B.append(para("Resumo", True, 26, "1F4E78"))
for t in [
    "10 veículos com atividade no dia (TEU2D25 e TFY9F33 na oficina, sem movimentação).",
    "4 veículos com uso após as 19h: TXI5B84, TEW0F04, TEW0F24 e TEW0F15 – todos justificados.",
    "5 pernoitaram fora dos pátios: TEW0F04, TEW0F14, TEW0F15 (Matheus), TEW0F24 e TXI5B84 – todos justificados.",
    "Nenhum veículo se movimentou entre 00h00 e 06h30 de 14/10 (primeira saída às 06:49).",
    "2 veículos na oficina: TEU2D25 (motor/retífica) e TFY9F33 – Scudo (troca de disco e pastilhas de freio).",
    "Todas as ocorrências estão justificadas.",
]:
    B.append(mixed([(t, False)], bullet=True))

B.append(para("1. Uso após as 19h00", True, 26, "1F4E78"))
B.append(table([
    ["Veículo", "Responsável", "Trajeto(s)", "Justificativa / observação"],
    ["TXI5B84 – Fiorino (VNB5)", "Reyner", "18:55→19:00 (0,9 km); 19:13→19:16 (0,7 km); 19:24→19:40 (7,3 km); 21:15→21:36 (7,3 km)", 'Justificado: veículo com o Reyner; trajetos curtos terminando no "Ponto de Pernoite e Retorno"'],
    ["TEW0F04 – Fiorino (RM3I)", "Alexandre Carvalho do Vale", "17:43→19:28 (120,5 km); 20:41→20:55 (3,5 km); 22:07→22:17 (3,5 km)", "Justificado: retorno de viagem ao interior; pernoitou na região de Pires do Rio-GO"],
    ["TEW0F24 – Fiorino (W9I3)", "João Paulo Rodrigo Silva", "19:25→19:37 (4,9 km); 19:41→19:48 (3,5 km)", "Justificado: autorização do Gero; chegou à Base de Pernoite às 19:48"],
    ["TEW0F15 – Fiorino (XV3D)", "Matheus Rodrigues Cipriano", "18:33→19:08 (10,2 km)", "Justificado: Matheus Rodrigues Cipriano; pernoitou em -16.3793, -48.9622 (Anápolis-GO, ~50 km)"],
], [1900, 1700, 3100, 3300]))

B.append(para("2. Pernoite fora dos pátios", True, 26, "1F4E78"))
B.append(para("Nenhum veículo se movimentou entre 00h00 e 06h30 de 14/10/2026.", False, 18))
B.append(table([
    ["Veículo", "Responsável", "Local do pernoite", "Distância / justificativa"],
    ["TEW0F04 – Fiorino (RM3I)", "Alexandre Carvalho do Vale", "-17.7728, -48.6274 – região de Pires do Rio-GO", "~172 km do CSP; parado após 22:17 – Justificado: retorno de viagem ao interior"],
    ["TEW0F14 – Fiorino (XUYY)", "Jovenildo de Oliveira", "-16.5109, -50.3700 – região de Iporá-GO", "~128 km do CSP; parado desde 18:05 – Justificado: viagem ao interior"],
    ["TEW0F15 – Fiorino (XV3D)", "Matheus Rodrigues Cipriano", "-16.3793, -48.9622 – região de Anápolis-GO", "~50 km do CSP; parado desde 19:08 – Justificado: Matheus Rodrigues Cipriano"],
    ["TEW0F24 – Fiorino (W9I3)", "João Paulo Rodrigo Silva", "-16.8050, -49.3529 – Base de Pernoite", "~16 km do CSP; chegou às 19:48 – Justificado: autorização do Gero"],
    ["TXI5B84 – Fiorino (VNB5)", "Reyner", "-16.7135, -49.2680 – Ponto de Pernoite e Retorno", "~3 km do CSP; parado após 21:36 – Justificado: veículo com o Reyner (autorizado)"],
], [1900, 1700, 3000, 3400]))

B.append(para("3. Veículos regulares", True, 26, "1F4E78"))
B.append(mixed([("Pernoite no pátio CSP e sem uso após as 19h: ", True),
                ("TEU2C47 – Saveiro (VNB9) – Reyner (64,5 km, 16 trajetos, último às 17:42); TXA3E97 – Fiorino (W9HM) – Rodrigo (38,0 km, 14 trajetos, último às 17:46); TEW0F17 – Fiorino (V8BK) – Frederiko (42,0 km, 11 trajetos, último às 17:06).", False)]))
B.append(mixed([("", False), ("TEX0E24 – Mobi (W6F1) – Luiz Eduardo: 35,7 km (5 trajetos até 17:49). TEX0E56 – Mobi (Q7OO) – Gero: 29,8 km (10 trajetos até 18:03).", False)]))
B.append(mixed([("Veículos na oficina:", True)]))
B.append(mixed([("TEU2D25 – Saveiro (XB5R): motor de partida queimado; ruído no motor – em avaliação para retífica. Sem movimentação.", False)], bullet=True))
B.append(mixed([("TFY9F33 – Scudo (VNO5): troca de disco e pastilhas de freio. Sem movimentação.", False)], bullet=True))

B.append(para("4. Checklist do dia (14/10)", True, 26, "1F4E78"))
B.append(table([
    ["Veículo", "Motorista", "Envio", "Situação"],
    ["TEW0F04 – Fiorino (RM3I)", "Alexandre Carvalho do Vale", "09:29", "Feito"],
    ["TEW0F17 – Fiorino (V8BK)", "Frederiko Ferreira de Siqueira", "09:19", "Feito"],
    ["TEW0F24 – Fiorino (W9I3)", "João Paulo Rodrigo Silva", "09:02", "Feito"],
    ["TXA3E97 – Fiorino (W9HM)", "Rodrigo Neves Junior", "08:57", "Feito"],
    ["TEW0F14 – Fiorino (XUYY)", "Jovenildo de Oliveira", "08:32", "Feito"],
    ["TEU2C47 – Saveiro (VNB9)", "Reyner", "08:28", "Feito"],
    ["TXI5B84 – Fiorino (VNB5)", "Reyner", "08:27", "Feito"],
    ["TEW0F15 – Fiorino (XV3D)", "Matheus Rodrigues Cipriano", "—", "Não feito (rodou 90,0 km)"],
    ["TEX0E24 – Mobi (W6F1)", "—", "—", "Não feito (rodou 35,7 km)"],
    ["TEX0E56 – Mobi (Q7OO)", "—", "—", "Não feito (rodou 29,8 km)"],
    ["TEU2D25 – Saveiro (XB5R)", "—", "—", "Na oficina – sem movimentação"],
    ["TFY9F33 – Scudo (VNO5)", "—", "—", "Na oficina – sem movimentação"],
], [2600, 3000, 1000, 3400]))
B.append(para('Todos os checklists enviados constam como "Sem conformidade".', False, 18))

B.append(para("5. Quilometragem do dia", True, 26, "1F4E78"))
B.append(table([
    ["Veículo", "Motorista", "Trajetos", "Distância"],
    ["TEW0F04 – Fiorino (RM3I)", "Alexandre Carvalho do Vale", "19", "443,5 km"],
    ["TEW0F14 – Fiorino (XUYY)", "Jovenildo de Oliveira", "10", "180,6 km"],
    ["TEW0F24 – Fiorino (W9I3)", "João Paulo Rodrigo Silva", "14", "138,9 km"],
    ["TEW0F15 – Fiorino (XV3D)", "Matheus Rodrigues Cipriano", "16", "90,0 km"],
    ["TXI5B84 – Fiorino (VNB5)", "Reyner", "15", "80,2 km"],
    ["TEU2C47 – Saveiro (VNB9)", "Reyner", "16", "64,5 km"],
    ["TEW0F17 – Fiorino (V8BK)", "Frederiko Ferreira de Siqueira", "11", "42,0 km"],
    ["TXA3E97 – Fiorino (W9HM)", "Rodrigo Neves Junior", "14", "38,0 km"],
    ["TEX0E24 – Mobi (W6F1)", "Luiz Eduardo", "5", "35,7 km"],
    ["TEX0E56 – Mobi (Q7OO)", "Gero", "10", "29,8 km"],
    ["Total", "", "130", "1.143,2 km"],
], [2800, 3000, 1200, 3000]))
B.append(para("Distâncias e trajetos contam só os que começaram em 14/10. Os trajetos de retorno feitos na manhã de 15/10 (TEW0F04, TEW0F14, TEW0F24, TEW0F15 e demais) ficam fora desta soma.", False, 17))

B.append(para("6. Pontos de atenção", True, 26, "1F4E78"))
B.append(mixed([("Ocorrências justificadas:", True)]))
for t in [
    "TEW0F04 – Alexandre em viagem longa ao interior (~443 km no dia); uso após 19h e pernoite em Pires do Rio-GO justificados.",
    "TEW0F14 – Jovenildo em viagem ao interior (região de Iporá-GO, ~181 km); pernoite fora justificado.",
    "TEW0F24 – João Paulo com autorização do Gero; pernoitou na Base de Pernoite.",
    "TXI5B84 – Reyner; uso após 19h e pernoite no Ponto de Pernoite e Retorno – justificado.",
]:
    B.append(mixed([(t, False)], bullet=True))
B.append(mixed([("Pendências:", True)]))
for t in [
    "TEW0F15 – Matheus Rodrigues Cipriano; rodou 90,0 km e pernoitou em Anápolis-GO (~50 km); sem checklist no dia. Confirmar com o usuário que o condutor foi o Matheus (a regra geral do veículo é Gero).",
    "TEX0E24 (Luiz Eduardo) e TEX0E56 (Gero) – sem checklist no dia.",
]:
    B.append(mixed([(t, False)], bullet=True))
B.append(mixed([("Oficina:", True)]))
B.append(mixed([("TEU2D25 – Saveiro (XB5R): motor de partida queimado, ruído no motor – em avaliação para retífica.", False)], bullet=True))
B.append(mixed([("TFY9F33 – Scudo (VNO5): troca de disco e pastilhas de freio.", False)], bullet=True))

body = "".join(B)
doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}'
       '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900"/></w:sectPr>'
       '</w:body></w:document>')

content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '</Types>')
rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')

with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", doc)
print("ok", sys.argv[1])
