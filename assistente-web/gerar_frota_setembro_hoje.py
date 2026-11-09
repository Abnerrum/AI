"""Gera o Excel da frota (Localiza + webFrota) de 01/09 a 06/11/2026. Uso: python -I gerar_frota_setembro_hoje.py saida.xlsx"""
import sys
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

GO, ES = "09.239.487/0001-34", "39.470.597/0001-73"
# (fatura, natureza, cnpj, emissao, vencimento, status, valor) - tela Faturas da Localiza, lida em 06/11/2026
F = [
("AGMTZ 3482329","Multa de trânsito",ES,"15/10/2026","15/11/2026","A vencer",330.31),
("AGMTZ 3482323","Multa de trânsito",GO,"15/10/2026","15/11/2026","A vencer",608.57),
("AGMTZ 3482320","Prefixação de danos",GO,"15/10/2026","15/11/2026","A vencer",917.50),
("AGMTZ 3007039","Reembolso despesa serviço r/n",ES,"13/02/2026","16/03/2026","Paga",199.28),
("AGMTZ 3005550","Multa de trânsito",ES,"13/02/2026","16/03/2026","Paga",269.78),
("AFMTZ 3077021","Aluguel",ES,"13/02/2026","28/02/2026","Paga",22934.00),
("AGMTZ 3006797","Prefixação de danos",GO,"13/02/2026","16/03/2026","Paga",818.00),
("AGMTZ 3005536","Multa de trânsito",GO,"13/02/2026","16/03/2026","Paga",747.70),
("AGMTZ 3003180","Uso indevido do carro",GO,"13/02/2026","16/03/2026","Paga",409.50),
("AFMTZ 3077006","Aluguel",GO,"13/02/2026","28/02/2026","Paga",42690.00),
("AGMTZ 3062484","Multa de trânsito",ES,"16/03/2026","16/04/2026","Paga",408.91),
("AFMTZ 3158115","Aluguel",ES,"16/03/2026","30/03/2026","Paga",22934.00),
("AGMTZ 3062463","Multa de trânsito",GO,"16/03/2026","16/04/2026","Paga",878.35),
("AGMTZ 3062453","Prefixação de danos",GO,"16/03/2026","16/04/2026","Paga",650.00),
("AFMTZ 3158103","Aluguel",GO,"16/03/2026","30/03/2026","Paga",45621.86),
("AGMTZ 3115028","Multa de trânsito",ES,"15/04/2026","16/05/2026","Paga",139.13),
("AGMTZ 3114997","Prefixação de danos",ES,"15/04/2026","16/05/2026","Paga",359.00),
("AFMTZ 3240050","Aluguel",ES,"15/04/2026","30/04/2026","Paga",22934.00),
("AGMTZ 3115005","Multa de trânsito",GO,"15/04/2026","16/05/2026","Paga",1348.00),
("AFMTZ 3240045","Aluguel",GO,"15/04/2026","30/04/2026","Paga",46688.00),
("AGMTZ 3180349","Prefixação de danos",ES,"15/05/2026","15/06/2026","Paga",3117.91),
("AFMTZ 3325219","Aluguel",ES,"15/05/2026","30/05/2026","Paga",22934.00),
("AGMTZ 3180401","Multa de trânsito",GO,"15/05/2026","15/06/2026","Paga",1043.04),
("AGMTZ 3167105","Prefixação de danos",GO,"07/05/2026","07/06/2026","Paga",561.60),
("AFMTZ 3325214","Aluguel",GO,"15/05/2026","30/05/2026","Paga",46688.00),
("AGMTZ 3244243","Multa de trânsito",ES,"15/06/2026","16/07/2026","Paga",139.13),
("AFMTZ 3411669","Aluguel",ES,"15/06/2026","30/06/2026","Paga",22934.00),
("AGMTZ 3244199","Multa de trânsito",GO,"15/06/2026","16/07/2026","Paga",278.26),
("AGMTZ 3244183","Prefixação de danos",GO,"15/06/2026","05/10/2026","Paga",13147.65),
("AFMTZ 3411663","Aluguel",GO,"15/06/2026","30/06/2026","Paga",46688.00),
("AGMTZ 3302826","Prefixação de danos",ES,"15/07/2026","15/08/2026","Paga",2077.96),
("AFMTZ 3498584","Aluguel",ES,"15/07/2026","30/07/2026","Paga",24080.05),
("AGMTZ 3302818","Prefixação de danos",GO,"15/07/2026","15/08/2026","Paga",3084.30),
("AGMTZ 3302812","Multa de trânsito",GO,"15/07/2026","15/08/2026","Paga",851.83),
("AFMTZ 3498576","Aluguel",GO,"15/07/2026","30/07/2026","Paga",48459.09),
("AGMTZ 3373677","Multa de trânsito",ES,"15/08/2026","15/09/2026","Paga",712.67),
("AGMTZ 3373676","Prefixação de danos",ES,"15/08/2026","15/09/2026","Paga",670.00),
("AFMTZ 3598459","Aluguel",ES,"15/08/2026","30/08/2026","Paga",24080.05),
("AGMTZ 3373674","Prefixação de danos",GO,"15/08/2026","15/09/2026","Paga",3354.76),
("AGMTZ 3373673","Multa de trânsito",GO,"15/08/2026","15/09/2026","Paga",1486.92),
("AFMTZ 3598453","Aluguel",GO,"15/08/2026","30/08/2026","Paga",48648.82),
("AGMTZ 3432599","Multa de trânsito",ES,"15/09/2026","16/10/2026","Paga",278.26),
("AGMTZ 3432592","Prefixação de danos",ES,"15/09/2026","16/10/2026","Paga",590.00),
("AFMTZ 3695307","Aluguel",ES,"15/09/2026","30/09/2026","Paga",24080.05),
("AGMTZ 3436039","Reembolso despesa serviço r/n",GO,"16/09/2026","17/10/2026","Paga",606.00),
("AGMTZ 3432594","Multa de trânsito",GO,"15/09/2026","16/10/2026","Paga",548.04),
("AGMTZ 3432593","Pneu excedente",GO,"15/09/2026","16/10/2026","Paga",696.90),
("AFMTZ 3695303","Aluguel",GO,"15/09/2026","15/10/2026","Paga",48648.82),
("AFMTZ 3784569","Aluguel",ES,"15/10/2026","30/10/2026","Paga",24080.05),
("AFMTZ 3784565","Aluguel",GO,"15/10/2026","30/10/2026","Paga",48960.02),
]
# webFrota: totais lidos das 177 linhas (Histórico de Consumo, 01/09 a 06/11/2026)
MES = [("09/2026",91,3110.0,11072.99,3139.30),("10/2026",80,2751.4,10365.11,2108.19),("11/2026 (até 05/11)",6,210.3,718.64,173.81)]
CC = [("NUCLEO",137,4603.3,16884.49,4152.90),("AXT VIA",39,1421.9,5070.83,1268.40),("(sem centro de custo)",1,46.4,201.42,0.0)]
MOT = [("JOAO PAULO RODRIGO SILVA",32,1005.8,3683.37,913.22,10271),("RODRIGO DE SOUSA NEVES JUNIOR",24,753.3,2671.31,710.18,8970),
("LUIS EDUARDO REIS CORREA CARDOSO",21,620.3,2213.68,580.59,6697),("REYNER CEZAR MACHADO",15,601.2,2160.21,541.23,4208),
("MATHEUS RODRIGUES CIPRIANO SILVA",12,439.3,1947.13,349.98,7921),("PHILLIP BORGES NUNES",13,518.6,1836.22,484.39,4430),
("ARTHUR DE SOUSA MARTINS",13,467.6,1686.18,420.74,6035),("ALEXANDRE CARVALHO DO VALE",12,391.2,1395.51,317.60,8260),
("FREDERIKO FERREIRA DE SIQUEIRA",11,380.0,1352.88,380.06,3645),("YHAGO LUCIANO LEMES ROCHA",7,263.8,919.97,245.40,1806),
("GERWISLEY SILVEIRA ROCHA NETO",5,173.1,608.80,141.62,1762),("FERNANDO CARDOSO SOUZA",4,155.5,564.00,135.75,1532),
("HERMES DE LIMA REIS NETO",3,132.4,472.15,113.42,2867),("JOVENILDO PLÁCIDO DE OLIVEIRA",4,123.2,443.91,87.12,1961),
("(sem motorista)",1,46.4,201.42,0.0,0)]

def dt(s):
    d, m, a = s.split("/"); return date(int(a), int(m), int(d))

wb = Workbook()
ARIAL = "Arial"
head_fill = PatternFill("solid", fgColor="1F5F55")
blue = Font(name=ARIAL, color="0000FF"); base = Font(name=ARIAL); bold = Font(name=ARIAL, bold=True)
hfont = Font(name=ARIAL, bold=True, color="FFFFFF")
BRL = '#,##0.00'

def header(ws, row, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row=row, column=i, value=c); x.font = hfont; x.fill = head_fill; x.alignment = Alignment(horizontal="center", wrap_text=True)

def widths(ws, w):
    for i, v in enumerate(w, 1): ws.column_dimensions[get_column_letter(i)].width = v

# --- Localiza Faturas
wl = wb.active; wl.title = "Localiza Faturas"
header(wl, 1, ["Fatura", "Natureza", "Região", "CNPJ", "Emissão", "Vencimento", "Status", "Valor (R$)", "No período (01/09 a 06/11)?"])
for i, r in enumerate(F, 2):
    reg = "GO" if r[2] == GO else "ES (TXM)"
    vals = [r[0], r[1], reg, r[2], dt(r[3]), dt(r[4]), r[5], r[6]]
    for j, v in enumerate(vals, 1):
        c = wl.cell(row=i, column=j, value=v); c.font = blue if j == 8 else base
    wl.cell(row=i, column=5).number_format = "dd/mm/yyyy"; wl.cell(row=i, column=6).number_format = "dd/mm/yyyy"
    wl.cell(row=i, column=8).number_format = BRL
    c = wl.cell(row=i, column=9, value=f'=IF(AND(E{i}>=DATE(2026,9,1),E{i}<=DATE(2026,11,6)),"Sim","Não")'); c.font = base
last = len(F) + 1
widths(wl, [16, 30, 10, 20, 12, 12, 10, 14, 18]); wl.freeze_panes = "A2"; wl.auto_filter.ref = f"A1:I{last}"

# --- Resumo
ws = wb.create_sheet("Resumo", 0)
ws["A1"] = "Frota - Localiza, webFrota e Alelo - 01/09/2026 a 06/11/2026"; ws["A1"].font = Font(name=ARIAL, bold=True, size=14)
ws["A2"] = "Fontes: Localiza MyFleet (faturas), Quality webFrota (consumo), Alelo Veloe Go (pedido de relatório). Lido em 06/11/2026."; ws["A2"].font = base
header(ws, 4, ["Localiza - por natureza (emissão no período)", "Faturas", "Total (R$)", "GO (R$)", "ES/TXM (R$)"])
nat = ["Aluguel", "Multa de trânsito", "Prefixação de danos", "Reembolso despesa serviço r/n", "Pneu excedente", "Uso indevido do carro"]
rng = lambda col: f"'Localiza Faturas'!${col}$2:${col}${last}"
for k, n in enumerate(nat, 5):
    ws.cell(row=k, column=1, value=n).font = base
    ws.cell(row=k, column=2, value=f'=COUNTIFS({rng("B")},A{k},{rng("I")},"Sim")').font = base
    ws.cell(row=k, column=3, value=f'=SUMIFS({rng("H")},{rng("B")},A{k},{rng("I")},"Sim")').font = base
    ws.cell(row=k, column=4, value=f'=SUMIFS({rng("H")},{rng("B")},A{k},{rng("I")},"Sim",{rng("C")},"GO")').font = base
    ws.cell(row=k, column=5, value=f'=SUMIFS({rng("H")},{rng("B")},A{k},{rng("I")},"Sim",{rng("C")},"ES (TXM)")').font = base
t = 5 + len(nat)
ws.cell(row=t, column=1, value="Total Localiza").font = bold
for col in "BCDE":
    ws[f"{col}{t}"] = f"=SUM({col}5:{col}{t-1})"; ws[f"{col}{t}"].font = bold
for r in range(5, t + 1):
    for col in "CDE": ws[f"{col}{r}"].number_format = BRL
r0 = t + 1
ws.cell(row=r0, column=1, value="A vencer em 15/11/2026 (3 faturas)").font = base
ws.cell(row=r0, column=3, value=f'=SUMIFS({rng("H")},{rng("G")},"A vencer")').font = base; ws.cell(row=r0, column=3).number_format = BRL

r1 = r0 + 3
header(ws, r1, ["webFrota - por mês", "Abastecimentos", "Litros", "Venda (R$)", "Desconto (R$)"])
for k, m in enumerate(MES, r1 + 1):
    for j, v in enumerate(m, 1):
        c = ws.cell(row=k, column=j, value=v); c.font = blue if j > 1 else base
    ws.cell(row=k, column=3).number_format = '#,##0.0'; ws.cell(row=k, column=4).number_format = BRL; ws.cell(row=k, column=5).number_format = BRL
tm = r1 + 1 + len(MES)
ws.cell(row=tm, column=1, value="Total webFrota").font = bold
for col in "BCDE":
    ws[f"{col}{tm}"] = f"=SUM({col}{r1+1}:{col}{tm-1})"; ws[f"{col}{tm}"].font = bold
ws[f"C{tm}"].number_format = '#,##0.0'; ws[f"D{tm}"].number_format = BRL; ws[f"E{tm}"].number_format = BRL
ws.cell(row=tm + 1, column=1, value="Conferência com a tela do webFrota: 177 abastecimentos, 6.071,62 L, R$ 22.156,74 de venda, R$ 5.421,30 de desconto, 70.365 km rodados.").font = base

r2 = tm + 4
header(ws, r2, ["webFrota - por centro de custo", "Abastecimentos", "Litros", "Venda (R$)", "Desconto (R$)"])
for k, m in enumerate(CC, r2 + 1):
    for j, v in enumerate(m, 1):
        c = ws.cell(row=k, column=j, value=v); c.font = blue if j > 1 else base
    ws.cell(row=k, column=3).number_format = '#,##0.0'; ws.cell(row=k, column=4).number_format = BRL; ws.cell(row=k, column=5).number_format = BRL

r3 = r2 + len(CC) + 3
ws.cell(row=r3, column=1, value="Alelo (Veloe Go)").font = bold
ws.cell(row=r3 + 1, column=1, value="Relatório de Transações (CSV, 01/09 a 06/11/2026) solicitado em 06/11/2026 11:09; status 'Processando' na última leitura. Os outros 13 tipos e o conteúdo ainda não foram baixados.").font = base
ws.cell(row=r3 + 2, column=1, value="Limitações: o webFrota não traz placa (só motorista, centro de custo e km); a Localiza não mostra valor por placa nas telas (só nos demonstrativos das faturas).").font = base
widths(ws, [52, 16, 16, 16, 16])

# --- webFrota Resumo
wf = wb.create_sheet("webFrota por motorista")
header(wf, 1, ["Motorista", "Abastecimentos", "Litros", "Venda (R$)", "Desconto (R$)", "Km rodados"])
for i, m in enumerate(MOT, 2):
    for j, v in enumerate(m, 1):
        c = wf.cell(row=i, column=j, value=v); c.font = blue if j > 1 else base
    wf.cell(row=i, column=3).number_format = '#,##0.0'; wf.cell(row=i, column=4).number_format = BRL; wf.cell(row=i, column=5).number_format = BRL
n = len(MOT) + 2
wf.cell(row=n, column=1, value="Total").font = bold
for col in "BCDEF":
    wf[f"{col}{n}"] = f"=SUM({col}2:{col}{n-1})"; wf[f"{col}{n}"].font = bold
wf[f"C{n}"].number_format = '#,##0.0'; wf[f"D{n}"].number_format = BRL; wf[f"E{n}"].number_format = BRL
widths(wf, [38, 16, 12, 14, 14, 14]); wf.freeze_panes = "A2"

# --- Alelo (Veloe Go): CSV de Transações baixado do portal (argv[2], opcional)
if len(sys.argv) > 2:
    import csv, collections
    num = lambda s: float((s or "0").replace(".", "").replace(",", ".") or 0)
    with open(sys.argv[2], encoding="cp1252", newline="") as fh:
        A = list(csv.DictReader(fh, delimiter=";"))
    compras = [r for r in A if r["Tipo Transação"] == "Compra" and r["Status Transação"] == "Aprovada"]
    negadas = [r for r in A if r["Tipo Transação"] == "Compra" and r["Status Transação"] == "Negada"]
    wa = wb.create_sheet("Alelo Compras")
    header(wa, 1, ["Data/hora", "Placa", "Modelo", "Motorista", "Mercadoria", "Qtd", "Valor (R$)", "Estabelecimento", "Cidade/UF", "Centro de custo"])
    for i, r in enumerate(compras, 2):
        d, hm = r["Data/Hora Transação"].split(" ")
        dd, mm, aa = d.split("/")
        vals = [f"{dd}/{mm}/{aa} {hm}", r["Placa"], r["Modelo Veículo"], r["Nome Motorista"], r["Mercadoria"], num(r["Qtd Mercadoria"]),
                num(r["Valor Total com Desconto"]), r["Nome EC"], f'{r["Cidade EC"]}/{r["UF EC"]}', r["Descrição do centro de custo"]]
        for j, v in enumerate(vals, 1):
            c = wa.cell(row=i, column=j, value=v); c.font = blue if j in (6, 7) else base
        wa.cell(row=i, column=6).number_format = '#,##0.00'; wa.cell(row=i, column=7).number_format = BRL
    la = len(compras) + 1
    widths(wa, [18, 10, 14, 32, 12, 10, 14, 34, 22, 20]); wa.freeze_panes = "A2"; wa.auto_filter.ref = f"A1:J{la}"

    wp = wb.create_sheet("Alelo por placa")
    header(wp, 1, ["Placa", "Compras aprovadas", "Quantidade (L/un.)", "Valor (R$)", "Set/2026 (R$)", "Out/2026 (R$)", "Nov/2026 (R$)"])
    placas = sorted({r["Placa"] for r in compras})
    for i, p in enumerate(placas, 2):
        ra = f"'Alelo Compras'!$B$2:$B${la}"; rv = f"'Alelo Compras'!$G$2:$G${la}"; rd = f"'Alelo Compras'!$A$2:$A${la}"
        wp.cell(row=i, column=1, value=p).font = base
        wp.cell(row=i, column=2, value=f"=COUNTIF({ra},A{i})").font = base
        wp.cell(row=i, column=3, value=f"=SUMIF({ra},A{i},'Alelo Compras'!$F$2:$F${la})").font = base
        wp.cell(row=i, column=4, value=f"=SUMIF({ra},A{i},{rv})").font = base
        for col, mes in ((5, "09"), (6, "10"), (7, "11")):
            wp.cell(row=i, column=col, value=f'=SUMIFS({rv},{ra},A{i},{rd},"??/{mes}/2026*")').font = base
        wp.cell(row=i, column=3).number_format = '#,##0.0'
        for col in (4, 5, 6, 7): wp.cell(row=i, column=col).number_format = BRL
    nt = len(placas) + 2
    wp.cell(row=nt, column=1, value="Total").font = bold
    for col in "BCDEFG":
        wp[f"{col}{nt}"] = f"=SUM({col}2:{col}{nt-1})"; wp[f"{col}{nt}"].font = bold
    wp[f"C{nt}"].number_format = '#,##0.0'
    for col in "DEFG": wp[f"{col}{nt}"].number_format = BRL
    widths(wp, [12, 18, 20, 14, 14, 14, 14]); wp.freeze_panes = "A2"

    # resumo do Alelo na aba Resumo
    base_row = r3 + 1
    ws.cell(row=base_row, column=1, value="Compras aprovadas (aba 'Alelo Compras')").font = base
    ws.cell(row=base_row, column=2, value=f"=COUNTA('Alelo Compras'!$A$2:$A${la})").font = base
    ws.cell(row=base_row, column=4, value=f"=SUM('Alelo Compras'!$G$2:$G${la})").font = base
    ws.cell(row=base_row, column=3, value=f"=SUM('Alelo Compras'!$F$2:$F${la})").font = base
    ws.cell(row=base_row, column=3).number_format = '#,##0.0'; ws.cell(row=base_row, column=4).number_format = BRL
    cred = sum(num(r["Valor Total com Desconto"]) for r in A if r["Tipo Transação"] == "Crédito Emergencial de Limite")
    ws.cell(row=base_row + 1, column=1, value=f"CSV Alelo: {len(A)} linhas; {len(negadas)} compras negadas (fora do total) e {sum(1 for r in A if r['Tipo Transação'] == 'Crédito Emergencial de Limite')} créditos emergenciais de limite (R$ {cred:,.2f}, não é gasto).".replace(",", "X").replace(".", ",").replace("X", ".")).font = base
    ws.cell(row=base_row + 2, column=1, value="Alelo: dados de 01/09 a 06/11/2026 do relatório de Transações; os outros 13 tipos de relatório não foram solicitados.").font = base
    ws.cell(row=base_row + 3, column=1, value="Limitações: o webFrota não traz placa (só motorista, centro de custo e km); a Localiza não mostra valor por placa nas telas.").font = base
else:
    pass

wb.save(sys.argv[1])
print("ok", sys.argv[1])
