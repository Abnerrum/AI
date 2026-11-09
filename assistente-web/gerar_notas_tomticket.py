import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

NUC = "Nucleo Service (2446971)"
TXM = "TXM Vitoria (3192793)"
ANA = "AXT Anapolis (3178021)"
GYN = "AXT Goiania (3178766)"
B85 = "ASC 4885160 (TomTickets: AXT Goiania)"

# (empresa, NF, data do fechamento, documento, valor, vencimento, chamado, data do chamado)
garantia = [
    (NUC, 418, "16/09/2026", "3209883", 9128.55, "10/10/26", "#308239", "17/09/2026"),
    (NUC, 419, "17/09/2026", "3223469", 8485.49, "26/10/26", "#308502", "18/09/2026"),
    (NUC, 420, "21/09/2026", "3260951", 9560.31, "10/10/26", "#309104", "21/09/2026"),
    (NUC, 423, "23/09/2026", "3277982", 12987.01, "10/10/26", "#309556", "23/09/2026"),
    (NUC, 424, "24/09/2026", "3304292", 5704.94, "10/10/26", "#309902", "25/09/2026"),
    (NUC, 426, "28/09/2026", "3342679", 9233.58, "10/10/26", "#310190", "29/09/2026"),
    (NUC, 434, "05/10/2026", "3435307", 10129.67, "25/10/26", "#312804", "05/10/2026"),
    (NUC, 438, "07/10/2026", "3450452", 7412.52, "25/10/26", "#313461", "08/10/2026"),
    (NUC, 441, "08/10/2026", "3473810", 6143.50, "25/10/26", "#313753", "09/10/2026"),
    (TXM, 372, "16/09/2026", "3210402", 3987.48, "10/10/26", "#308244", "17/09/2026"),
    (TXM, 375, "17/09/2026", "3223921", 4064.60, "26/10/26", "#308500", "18/09/2026"),
    (TXM, 378, "21/09/2026", "3260633", 4065.01, "10/10/26", "#309105", "21/09/2026"),
    (TXM, 382, "23/09/2026", "3290862", 9758.20, "10/10/26", "#309563", "23/09/2026"),
    (TXM, 383, "24/09/2026", "3307005", 6968.22, "10/10/26", "#309899", "25/09/2026"),
    (TXM, 385, "28/09/2026", "3344214", 13211.03, "10/10/26", "#310193", "29/09/2026"),
    (TXM, 388, "01/10/2026", "3392372", 23221.46, "25/10/26", "#312402", "02/10/2026"),
    (TXM, 431, "01/10/2026", "3391988", 30689.84, "25/10/26", "#312409", "02/10/2026"),
    (TXM, 392, "05/10/2026", "3435110", 11601.55, "25/10/26", "#312807", "05/10/2026"),
    (TXM, 393, "07/10/2026", "3461117", 15612.77, "25/10/26", "#313463", "08/10/2026"),
    (TXM, 397, "08/10/2026", "3463599", 8249.95, "25/10/26", "#313754", "09/10/2026"),
    (ANA, 790, "16/09/2026", "3209652", 40.00, "10/10/26", "#308236", "17/09/2026"),
    (ANA, 793, "23/09/2026", "3289275", 40.00, "10/10/26", "#309560", "23/09/2026"),
    (ANA, 794, "28/09/2026", "3344612", 67.60, "25/10/26", "#311921", "30/09/2026"),
    (ANA, 797, "05/10/2026", "3433865", 87.38, "25/10/26", "#312805", "05/10/2026"),
    (ANA, 799, "07/10/2026", "3461315", 130.53, "25/10/26", "#313462", "08/10/2026"),
    (ANA, 800, "08/10/2026", "3472469", 79.10, "25/10/26", "#313745", "09/10/2026"),
    (GYN, 221, "16/09/2026", "3209653", 80.00, "10/10/26", "#308241", "17/09/2026"),
    (GYN, 224, "07/10/2026", "3450272", 40.00, "25/10/26", "#313464", "08/10/2026"),
    (GYN, 225, "08/10/2026", "3473417", 40.00, "25/10/26", "#313750", "09/10/2026"),
    (B85, 545, "17/09/2026", "3223835", 40.00, "26/10/26", "#308505", "18/09/2026"),
    (B85, 546, "21/09/2026", "3260635", 1611.98, "10/10/26", "#309101", "21/09/2026"),
    (B85, 547, "01/10/2026", "3383282", 40.00, "25/10/26", "#312404", "02/10/2026"),
]

# (empresa, NF, descricao, valor, chamado, data do chamado, observacao)
outras = [
    (NUC, 427, "Pay for Performance CE (CSP) - Agosto/26", 13276.80, "#312247", "01/10/2026", "Mesmo valor da NF 429: conferir duplicidade"),
    (NUC, 429, "Pay for Performance CE (CSP) - Agosto/26", 13276.80, "#312506", "02/10/2026", "Mesmo valor da NF 427: conferir duplicidade"),
    (NUC, 430, "Pay for Performance MX (CSP) - Agosto/26", 1719.40, "#312507", "02/10/2026", ""),
    (NUC, 432, "Store+ SMB - Agosto/26", 223666.44, "#312613", "05/10/2026", ""),
    (NUC, 433, "Store+ - Agosto/26", 52737.02, "#312612", "05/10/2026", ""),
    (NUC, 435, "Galaxy Diagnostic recepcao (GD TA - NPC) - Maio/26", 80.00, "#312840", "06/10/2026", ""),
    (NUC, 436, "Pay for Performance CE (CSP) - Maio/26", 1170.00, "#312839", "06/10/2026", ""),
    (NUC, 439, "Galaxy Diagnostic recepcao (GD TA - HHP) - Maio/26", 1170.00, "#313495", "08/10/2026", ""),
    (TXM, 386, "Pay for Performance CE - Agosto/26", 3592.90, "#312238", "01/10/2026", "NF 386 tem 2 chamados com valores trocados"),
    (TXM, 386, "Pay for Performance CE - Agosto/26", 2663.20, "#312229", "01/10/2026", "NF 386 tem 2 chamados com valores trocados"),
    (TXM, 387, "Pay for Performance MX - Agosto/26", 2663.20, "#312239", "01/10/2026", "NF 387 tem 2 chamados com valores trocados"),
    (TXM, 387, "Pay for Performance MX - Agosto/26", 3592.90, "#312232", "01/10/2026", "NF 387 tem 2 chamados com valores trocados"),
    (TXM, 390, "Store+ SMB - Agosto/26", 34467.78, "#312614", "05/10/2026", ""),
    (TXM, 391, "Store+ - Agosto/26", 11400.41, "#312615", "05/10/2026", ""),
]

# (chamado, data, empresa, descricao, valor)
outros = [
    ("#312105", "01/10/2026", NUC, "Subsidio de OW (SAW - Desconto Fora de Garantia) 30.09.26 (sem NF no titulo)", 14401.61),
    ("#312784", "05/10/2026", NUC, "NF pendente Incentivo P4P CE 06.2026 - 3a notificacao", None),
    ("#312780", "05/10/2026", NUC, "NF pendente Incentivo TA NPC 05.2026 - 2a notificacao", None),
    ("#310001", "28/09/2026", NUC, "Relatorio de Pagamentos Samsung", None),
    ("#310002", "28/09/2026", TXM, "Relatorio de Pagamentos Samsung", None),
    ("#310003", "28/09/2026", ANA, "Relatorio de Pagamentos Samsung", None),
    ("#310004", "28/09/2026", GYN, "Relatorio de Pagamentos Samsung", None),
    ("#310005", "28/09/2026", B85, "Relatorio de Pagamentos Samsung", None),
    ("#308886", "18/09/2026", TXM, "Whatsapp Service Administration - Sprinklr", None),
    ("#308885", "18/09/2026", TXM, "Whatsapp Service Administration - Sprinklr", None),
    ("#314702", "14/10/2026", "", "Assinatura Reforma Tributaria, Midia e Compliance / Store+ (aberto)", None),
    ("#314698", "14/10/2026", "", "Assinatura Reforma Tributaria, Midia e Compliance (aberto)", None),
]

HEAD_FILL = PatternFill("solid", fgColor="1F4E78")
SUB_FILL = PatternFill("solid", fgColor="DDEBF7")
BRL = '#,##0.00'


def estilo_cabecalho(ws, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def larguras(ws, ws_w):
    for i, w in enumerate(ws_w, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


wb = Workbook()

ws = wb.active
ws.title = "Garantia"
ws.append(["Empresa (ASC)", "NF", "Fechamento", "Documento", "Valor (R$)", "Vencimento", "Chamado", "Data do chamado"])
estilo_cabecalho(ws, 8)
for r in garantia:
    ws.append(list(r))
    ws.cell(row=ws.max_row, column=5).number_format = BRL
n = ws.max_row
ws.append([])
ws.append(["TOTAL GARANTIA", None, None, None, f"=SUM(E2:E{n})"])
tot = ws.max_row
ws.cell(row=tot, column=1).font = Font(bold=True)
ws.cell(row=tot, column=5).font = Font(bold=True)
ws.cell(row=tot, column=5).number_format = BRL
ws.append([])
ws.append(["Subtotal por empresa"])
ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
for emp in [NUC, TXM, ANA, GYN, B85]:
    ws.append([emp, None, None, None, f'=SUMIF(A2:A{n},A{ws.max_row + 1},E2:E{n})'])
    row = ws.max_row
    ws.cell(row=row, column=5).number_format = BRL
    for c in range(1, 6):
        ws.cell(row=row, column=c).fill = SUB_FILL
larguras(ws, [38, 8, 13, 12, 14, 12, 11, 15])

ws2 = wb.create_sheet("Incentivos e Store+")
ws2.append(["Empresa (ASC)", "NF", "Descricao", "Valor (R$)", "Chamado", "Data do chamado", "Observacao"])
estilo_cabecalho(ws2, 7)
for r in outras:
    ws2.append(list(r))
    ws2.cell(row=ws2.max_row, column=4).number_format = BRL
larguras(ws2, [28, 8, 52, 15, 11, 15, 46])

ws3 = wb.create_sheet("Outros chamados")
ws3.append(["Chamado", "Data", "Empresa", "Descricao", "Valor (R$)"])
estilo_cabecalho(ws3, 5)
for r in outros:
    ws3.append(list(r))
    ws3.cell(row=ws3.max_row, column=5).number_format = BRL
larguras(ws3, [11, 12, 36, 78, 14])

wb.save(sys.argv[1])
print("ok", sys.argv[1])
