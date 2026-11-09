import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# Veiculo -> (descricao, grupo)
VEIC = {
    "TEW0F04": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TEW0F14": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TEW0F15": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TEW0F17": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TEW0F24": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TXA3E97": ("Fiat Fiorino Furgao", "GOIANIA"),
    "TXI5B84": ("Fiat Fiorino Furgao", "86 - OW"),
    "TEU2C47": ("VW Saveiro Cs", "86 - OW"),
    "TEX0E24": ("Fiat Mobi", "GOIANIA"),
    "TEX0E56": ("Fiat Mobi", "GOIANIA"),
    "TFY9F33": ("Fiat Scudo", "GOIANIA"),
    "TEU2D25": ("VW Saveiro Cs Rb Mf", "GOIANIA"),
}

# Dia -> veiculos que rodaram (ao menos 1 viagem no Cobli, Associacao de Trechos)
RODOU = {
    1: "TEW0F04 TEW0F24 TXI5B84 TEU2C47 TFY9F33 TEW0F17 TEX0E24 TEW0F14 TEW0F15 TXA3E97",
    2: "TXI5B84 TEU2C47 TEW0F24 TEW0F17 TFY9F33 TEW0F04 TXA3E97 TEX0E24 TEW0F14 TEW0F15",
    5: "TEU2C47 TEW0F24 TEW0F14 TEW0F04 TEW0F17 TFY9F33 TXI5B84 TEX0E24 TXA3E97",
    6: "TEW0F04 TEU2C47 TEW0F17 TEW0F24 TEW0F14 TFY9F33 TXA3E97 TXI5B84 TEX0E24 TEX0E56",
    7: "TEW0F24 TEW0F14 TEW0F17 TEW0F04 TFY9F33 TXA3E97 TEW0F15 TEX0E24 TEX0E56 TEU2C47 TXI5B84",
    8: "TEU2C47 TEW0F04 TEW0F24 TEW0F14 TXA3E97 TFY9F33 TEW0F15 TEW0F17 TEX0E24 TXI5B84",
    9: "TEW0F24 TEW0F04 TXA3E97 TXI5B84 TEW0F15 TEU2C47 TFY9F33 TEW0F14 TEW0F17 TEX0E24 TEX0E56",
    13: "TEW0F24 TEW0F15 TXI5B84 TEW0F17 TXA3E97 TEW0F14 TEX0E24 TEW0F04 TEU2C47 TEX0E56 TFY9F33",
    14: "TEW0F04 TEU2C47 TEW0F15 TXI5B84 TEW0F24 TXA3E97 TEW0F17 TEX0E56 TEW0F14 TEX0E24",
    15: "TEW0F24 TXA3E97 TEW0F04 TXI5B84 TEU2C47 TEW0F15 TEX0E24 TEX0E56 TEW0F17 TEW0F14",
}

# Dia -> veiculos com checklist enviado (Cobli > Checklists > Todas as respostas)
CHECK = {
    1: "TEW0F04 TEW0F24 TXI5B84 TEW0F17 TEX0E24 TFY9F33",
    2: "TXI5B84 TEW0F17 TEW0F04 TXA3E97 TEW0F24 TEU2C47 TFY9F33",
    5: "TEU2C47 TXA3E97 TEW0F14 TXI5B84 TEW0F24 TEW0F17",
    6: "TEU2C47 TEW0F04 TFY9F33 TXA3E97 TEW0F24 TXI5B84 TEW0F14",
    7: "TXI5B84 TEW0F17 TEW0F24 TEX0E56 TEX0E24 TXA3E97 TFY9F33 TEW0F04 TEW0F14",
    8: "TXI5B84 TFY9F33 TEW0F17 TXA3E97 TEW0F04 TEW0F15 TEW0F24 TEU2C47 TEW0F14",
    9: "TEW0F24 TEW0F04 TFY9F33 TEW0F15 TXA3E97 TXI5B84 TEW0F17 TEW0F14",
    13: "TEW0F04 TEW0F24 TEW0F14 TEW0F17 TXI5B84 TXA3E97",
    14: "TEW0F04 TEW0F17 TEW0F24 TXA3E97 TEW0F14 TEU2C47 TXI5B84",
    15: "TEX0E24 TXA3E97 TEW0F04 TEW0F24 TXI5B84 TEW0F14",
}

dias = sorted(RODOU)
rodou = {d: set(RODOU[d].split()) for d in dias}
check = {d: set(CHECK[d].split()) for d in dias}
sem = {d: sorted(rodou[d] - check[d]) for d in dias}

HEAD = PatternFill("solid", fgColor="1F4E78")
BAD = PatternFill("solid", fgColor="F8CBAD")
OK = PatternFill("solid", fgColor="C6E0B4")


def cab(ws, n):
    for c in range(1, n + 1):
        x = ws.cell(row=1, column=c)
        x.font = Font(bold=True, color="FFFFFF")
        x.fill = HEAD
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


wb = Workbook()

# Aba 1: resumo por veiculo
ws = wb.active
ws.title = "Resumo por veiculo"
ws.append(["Placa", "Veiculo", "Grupo", "Dias que rodou", "Dias com checklist", "Dias SEM checklist", "% sem checklist", "Dias sem checklist (outubro)"])
cab(ws, 8)
linhas = []
for p, (desc, grp) in VEIC.items():
    rd = [d for d in dias if p in rodou[d]]
    ck = [d for d in rd if p in check[d]]
    sm = [d for d in rd if p not in check[d]]
    linhas.append((p, desc, grp, len(rd), len(ck), len(sm), (len(sm) / len(rd)) if rd else None,
                   ", ".join(f"{d:02d}/10" for d in sm) if rd else "Nao rodou no periodo"))
linhas.sort(key=lambda r: (-r[5], r[0]))
for r in linhas:
    ws.append(list(r))
    row = ws.max_row
    ws.cell(row=row, column=7).number_format = "0%"
    if r[5] >= 5:
        for c in range(1, 9):
            ws.cell(row=row, column=c).fill = BAD
    elif r[3] and r[5] == 0:
        for c in range(1, 9):
            ws.cell(row=row, column=c).fill = OK
ws.append([])
ws.append(["TOTAL", None, None, f"=SUM(D2:D{len(linhas)+1})", f"=SUM(E2:E{len(linhas)+1})", f"=SUM(F2:F{len(linhas)+1})",
           f"=F{len(linhas)+3}/D{len(linhas)+3}"])
t = ws.max_row
for c in range(1, 8):
    ws.cell(row=t, column=c).font = Font(bold=True)
ws.cell(row=t, column=7).number_format = "0%"
for i, w in enumerate([11, 22, 11, 14, 17, 17, 15, 48], 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# Aba 2: por dia
ws2 = wb.create_sheet("Por dia")
ws2.append(["Data", "Veiculos que rodaram", "Com checklist", "Sem checklist", "Veiculos sem checklist"])
cab(ws2, 5)
for d in dias:
    ws2.append([f"{d:02d}/10/2026", len(rodou[d]), len(rodou[d] & check[d]), len(sem[d]), ", ".join(sem[d]) or "-"])
    if sem[d]:
        ws2.cell(row=ws2.max_row, column=4).fill = BAD
for i, w in enumerate([13, 20, 15, 15, 70], 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# Aba 3: matriz placa x dia
ws3 = wb.create_sheet("Matriz")
ws3.append(["Placa"] + [f"{d:02d}/10" for d in dias])
cab(ws3, 1 + len(dias))
for p in VEIC:
    row = [p]
    for d in dias:
        if p not in rodou[d]:
            row.append("-")
        elif p in check[d]:
            row.append("OK")
        else:
            row.append("SEM")
    ws3.append(row)
    r = ws3.max_row
    for c in range(2, 2 + len(dias)):
        v = ws3.cell(row=r, column=c).value
        ws3.cell(row=r, column=c).alignment = Alignment(horizontal="center")
        if v == "SEM":
            ws3.cell(row=r, column=c).fill = BAD
        elif v == "OK":
            ws3.cell(row=r, column=c).fill = OK
ws3.column_dimensions["A"].width = 11

# Aba 4: observacoes
ws4 = wb.create_sheet("Observacoes")
for l in [
    "Periodo: 01/10/2026 a 15/10/2026 (15/10 parcial, lido por volta das 13h).",
    "Rodou = o veiculo teve ao menos 1 viagem no dia (Cobli > Operacao > Associacao de Trechos).",
    "Checklist = resposta enviada no dia (Cobli > Operacao > Checklists > Todas as respostas, 78 respostas no periodo).",
    "Dias 03, 04, 10, 11 e 12/10 (fim de semana e feriado) nao tiveram checklist e nao foram conferidos quanto a viagens.",
    "TEU2D25 nao teve viagem no periodo (aparece Indisponivel no Monitoramento).",
    "Viagens muito curtas contam como 'rodou'. Veja a coluna de viagens no Cobli antes de cobrar o motorista.",
    "Esta planilha nao identifica motorista: o Cobli nao associou motorista a varias viagens.",
]:
    ws4.append([l])
ws4.column_dimensions["A"].width = 130

wb.save(sys.argv[1])
print("ok", sum(len(v) for v in sem.values()), "ocorrencias")
