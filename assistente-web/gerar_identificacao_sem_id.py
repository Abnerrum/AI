"""Excel de apoio: o que compoe o 'Sem identificacao' do BI e proposta de identificacao pelas regras do usuario.
Uso: python -I gerar_identificacao_sem_id.py webfrota.csv clara_novas.tsv saida.xlsx"""
import csv, sys, collections
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# Regras do usuario (controle_frota_cobli.md): responsavel fixo -> placa(s). FG = so TEU2C47 e TXI5B84.
REGRA = {
    "JOAO PAULO RODRIGO SILVA": (["TEW0F24"], "Fiorino W9I3, com autorização do Gero", "Garantia"),
    "ALEXANDRE CARVALHO DO VALE": (["TEW0F04"], "Fiorino RM3I (checklist confirmado)", "Garantia"),
    "FREDERIKO FERREIRA DE SIQUEIRA": (["TEW0F17"], "Fiorino V8BK (confirmado em 13/10)", "Garantia"),
    "JOVENILDO PLÁCIDO DE OLIVEIRA": (["TEW0F14"], "Fiorino XUYY (desde 05/10)", "Garantia"),
    "REYNER CEZAR MACHADO": (["TEU2C47", "TXI5B84"], "Saveiro e Fiorino VNB5: os dois são Fora de Garantia", "Fora de Garantia"),
}
def num(s):
    s = (s or "0").replace("R$", "").strip()
    return float(s.replace(".", "").replace(",", ".")) if "," in s else float(s or 0)

wb = Workbook(); ARIAL = "Arial"
base = Font(name=ARIAL); bold = Font(name=ARIAL, bold=True); blue = Font(name=ARIAL, color="0000FF")
hf = Font(name=ARIAL, bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="1F5F55"); BRL = "#,##0.00"
def head(ws, r, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row=r, column=i, value=c); x.font = hf; x.fill = fill; x.alignment = Alignment(horizontal="center", wrap_text=True)
def widths(ws, w):
    for i, v in enumerate(w, 1): ws.column_dimensions[get_column_letter(i)].width = v

# --- webFrota (so setembro e novembro, que e o que entrou no BI)
wf = collections.defaultdict(lambda: [0, 0.0, 0.0])
with open(sys.argv[1], encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh, delimiter=";"):
        d = r["Data/Hora"].split(" ")[0].split("/")
        if d[1] == "10": continue
        x = wf[r["Motorista"]]; x[0] += 1; x[1] += num(r["Litros"]); x[2] += num(r["ValorVenda"])

ws = wb.active; ws.title = "Resumo"
ws["A1"] = "Sem identificação no BI: o que compõe e como identificar"; ws["A1"].font = Font(name=ARIAL, bold=True, size=14)
ws["A2"] = "Base: BI_DESPESAS em 06/11/2026 (379 lançamentos). 'Sem identificação' = linha sem placa."; ws["A2"].font = base
head(ws, 4, ["Fonte", "Lançamentos", "Valor (R$)", "Como identificar", "Situação"])
tot_wf = sum(v[2] for v in wf.values()); n_wf = sum(v[0] for v in wf.values())
ident = sum(v[2] for k, v in wf.items() if k in REGRA); n_ident = sum(v[0] for k, v in wf.items() if k in REGRA)
lin = [
    ("Localiza GO - faturas de 15/09 (aluguel, multa, reembolso, pneu)", 4, 50499.76, "Precisa do demonstrativo por placa de cada fatura (PDF/Excel do portal Localiza)", "Pendente: depende de baixar os demonstrativos"),
    ("webFrota (Posto Xodo), setembro e novembro", n_wf, tot_wf, "Pelo motorista, usando as regras de responsável fixo do usuário (aba webFrota)", f"Proposta pronta: {n_ident} lançamentos / R$ {ident:,.2f} com regra"),
    ("Clara (cartão In Home), 128 lançamentos", 128, 8720.60, "Despesa por pessoa (refeição, loja, combustível): já tem responsável; placa só nos 5 abastecimentos", "Responsável já identificado"),
]
for i, l in enumerate(lin, 5):
    for j, v in enumerate(l, 1):
        c = ws.cell(row=i, column=j, value=v); c.font = blue if j == 3 else base
    ws.cell(row=i, column=3).number_format = BRL
ws.cell(row=8, column=1, value="Total Sem identificação").font = bold
ws["B8"] = "=SUM(B5:B7)"; ws["C8"] = "=SUM(C5:C7)"; ws["C8"].number_format = BRL; ws["B8"].font = bold; ws["C8"].font = bold
ws["A10"] = "Conferência: o total deve bater com R$ 71.011,99 (66.290,48 anteriores + 4.721,51 das 78 linhas novas da Clara)."; ws["A10"].font = base
widths(ws, [62, 14, 16, 78, 52])

# --- webFrota proposta
w2 = wb.create_sheet("webFrota por motorista")
head(w2, 1, ["Motorista", "Abastecimentos", "Litros", "Valor (R$)", "Placa(s) pela regra", "Regra do usuário", "Tipo de atendimento", "Confiança"])
rows = sorted(wf.items(), key=lambda kv: -kv[1][2])
for i, (m, v) in enumerate(rows, 2):
    reg = REGRA.get(m)
    vals = [m, v[0], round(v[1], 1), round(v[2], 2), " / ".join(reg[0]) if reg else "(sem regra)", reg[1] if reg else "Sem responsável fixo definido", reg[2] if reg else "Sem identificação", "Alta (regra do usuário)" if reg else "Sem base para identificar"]
    for j, x in enumerate(vals, 1):
        c = w2.cell(row=i, column=j, value=x); c.font = blue if j in (2, 3, 4) else base
    w2.cell(row=i, column=3).number_format = '#,##0.0'; w2.cell(row=i, column=4).number_format = BRL
n = len(rows) + 2
w2.cell(row=n, column=1, value="Total").font = bold
for col in "BCD": w2[f"{col}{n}"] = f"=SUM({col}2:{col}{n-1})"; w2[f"{col}{n}"].font = bold
w2[f"D{n}"].number_format = BRL
w2.cell(row=n + 2, column=1, value="Só setembro e novembro (outubro ainda está pendente de validação). Nada foi gravado no BI: depende da sua aprovação.").font = base
widths(w2, [38, 15, 12, 14, 20, 52, 20, 28]); w2.freeze_panes = "A2"

# --- Clara (novas)
w3 = wb.create_sheet("Clara novas (78)")
head(w3, 1, ["Data", "Titular", "Comércio", "Descrição", "Categoria", "Valor (R$)", "Situação", "ID origem"])
with open(sys.argv[2], encoding="utf-8") as fh:
    for i, line in enumerate(fh.read().split("\n"), 2):
        c = line.split("\t"); v = [c[1], c[7], c[8], c[9], c[4], num(c[11]), c[12], c[14]]
        for j, x in enumerate(v, 1):
            w3.cell(row=i, column=j, value=x).font = blue if j == 6 else base
        w3.cell(row=i, column=6).number_format = BRL
widths(w3, [12, 34, 32, 50, 18, 12, 22, 14]); w3.freeze_panes = "A2"
wb.save(sys.argv[3]); print("ok")
