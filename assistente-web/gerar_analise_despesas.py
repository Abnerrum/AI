"""Excel de analise financeira: onde estao as maiores despesas (01/09 a 06/11/2026).
Uso: python -I gerar_analise_despesas.py novas_fontes.xlsx saida.xlsx"""
import sys
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

src = load_workbook(sys.argv[1]).active
rows = list(src.iter_rows(values_only=True))
H = list(rows[0]); data = rows[1:]
ix = {h: i for i, h in enumerate(H)}

wb = Workbook()
ARIAL = "Arial"; base = Font(name=ARIAL); bold = Font(name=ARIAL, bold=True); blue = Font(name=ARIAL, color="0000FF")
hfill = PatternFill("solid", fgColor="1F5F55"); hfont = Font(name=ARIAL, bold=True, color="FFFFFF")
warn = PatternFill("solid", fgColor="FFF2CC"); BRL = '#,##0.00'

def head(ws, r, cols):
    for i, c in enumerate(cols, 1):
        x = ws.cell(row=r, column=i, value=c); x.font = hfont; x.fill = hfill; x.alignment = Alignment(horizontal="center", wrap_text=True)

def widths(ws, w):
    for i, v in enumerate(w, 1): ws.column_dimensions[get_column_letter(i)].width = v

# --- Dados (detalhe completo, filtravel)
wd = wb.active; wd.title = "Dados"
head(wd, 1, H)
for r in data:
    wd.append(list(r))
n = len(data) + 1
for row in wd.iter_rows(min_row=2):
    row[1].number_format = "dd/mm/yyyy"; row[10].number_format = '#,##0.00'; row[11].number_format = BRL
    for c in row: c.font = base
    if row[13].value in ("Duplicado", "Possível duplicidade"):
        for c in row: c.fill = warn
widths(wd, [24, 12, 9, 18, 18, 22, 11, 30, 34, 44, 10, 14, 14, 18, 16, 20, 11, 16, 20, 40, 60])
wd.freeze_panes = "A2"; wd.auto_filter.ref = f"A1:{get_column_letter(len(H))}{n}"
R = lambda col: f"Dados!${col}$2:${col}${n}"  # A fonte B data C mes D area E categoria F tipo G placa H resp I posto L valor N contar

# --- Ranking
ws = wb.create_sheet("Ranking", 0)
ws["A1"] = "Onde estão as maiores despesas - análise financeira (01/09 a 06/11/2026)"; ws["A1"].font = Font(name=ARIAL, bold=True, size=14)
ws["A2"] = "Só as 3 fontes novas (Localiza, webFrota, Alelo). Linhas 'Duplicado' já estão no BI e ficam fora; 'Possível duplicidade' é mostrada à parte."; ws["A2"].font = base

head(ws, 4, ["Categoria", "Valor (R$)", "% do total", "Faturas/lançamentos"])
cats = ["Locação", "Combustível", "Manutenção e danos", "Infrações"]
for k, c in enumerate(cats, 5):
    ws.cell(row=k, column=1, value=c).font = base
    ws.cell(row=k, column=2, value=f'=SUMIFS({R("L")},{R("E")},A{k},{R("N")},"Novo - validar")').font = base
    ws.cell(row=k, column=3, value=f"=B{k}/$B${5+len(cats)}").font = base
    ws.cell(row=k, column=4, value=f'=COUNTIFS({R("E")},A{k},{R("N")},"Novo - validar")').font = base
t = 5 + len(cats)
ws.cell(row=t, column=1, value="Total (novo e validável)").font = bold
ws[f"B{t}"] = f"=SUM(B5:B{t-1})"; ws[f"D{t}"] = f"=SUM(D5:D{t-1})"; ws[f"B{t}"].font = bold; ws[f"D{t}"].font = bold
for r in range(5, t + 1):
    ws[f"B{r}"].number_format = BRL; ws[f"C{r}"].number_format = "0.0%"

r1 = t + 3
head(ws, r1, ["Fonte x situação", "Linhas", "Valor (R$)"])
combos = [("Localiza (faturas)", "Novo - validar"), ("Localiza (faturas)", "Duplicado"), ("webFrota (Quality)", "Novo - validar"),
          ("webFrota (Quality)", "Possível duplicidade"), ("Alelo Veloe (Transações)", "Novo - validar"), ("Alelo Veloe (Transações)", "Duplicado")]
for k, (f, s) in enumerate(combos, r1 + 1):
    ws.cell(row=k, column=1, value=f"{f} | {s}").font = base
    ws.cell(row=k, column=2, value=f'=COUNTIFS({R("A")},"{f}",{R("N")},"{s}")').font = base
    ws.cell(row=k, column=3, value=f'=SUMIFS({R("L")},{R("A")},"{f}",{R("N")},"{s}")').font = base
    ws.cell(row=k, column=3).number_format = BRL

r2 = r1 + len(combos) + 3
head(ws, r2, ["Mês (novo e validável)", "Locação", "Combustível", "Manutenção e danos", "Infrações", "Total"])
for k, m in enumerate(["2026-09", "2026-10", "2026-11"], r2 + 1):
    ws.cell(row=k, column=1, value=m).font = base
    for j, c in enumerate(["Locação", "Combustível", "Manutenção e danos", "Infrações"], 2):
        ws.cell(row=k, column=j, value=f'=SUMIFS({R("L")},{R("C")},$A{k},{R("E")},"{c}",{R("N")},"Novo - validar")').font = base
        ws.cell(row=k, column=j).number_format = BRL
    ws.cell(row=k, column=6, value=f"=SUM(B{k}:E{k})").font = bold; ws.cell(row=k, column=6).number_format = BRL

r3 = r2 + 6
head(ws, r3, ["Combustível - eficiência de preço", "Litros", "Valor (R$)", "R$ por litro"])
for k, (lab, f) in enumerate([("webFrota (Posto Xodo)", "webFrota (Quality)"), ("Alelo (rede externa)", "Alelo Veloe (Transações)")], r3 + 1):
    ws.cell(row=k, column=1, value=lab).font = base
    ws.cell(row=k, column=2, value=f'=SUMIFS({R("K")},{R("A")},"{f}")').font = base
    ws.cell(row=k, column=3, value=f'=SUMIFS({R("L")},{R("A")},"{f}")').font = base
    ws.cell(row=k, column=4, value=f"=C{k}/B{k}").font = base
    ws.cell(row=k, column=2).number_format = '#,##0.0'; ws.cell(row=k, column=3).number_format = BRL; ws.cell(row=k, column=4).number_format = BRL

ch = BarChart(); ch.type = "bar"; ch.title = "Despesa por categoria (R$)"; ch.style = 10
ch.add_data(Reference(ws, min_col=2, min_row=4, max_row=4 + len(cats)), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=4 + len(cats))); ch.legend = None; ch.height = 7; ch.width = 14
ws.add_chart(ch, "H4")
widths(ws, [44, 16, 16, 20, 14, 16])

# --- Detalhe por categoria > fonte > responsavel/placa/posto
wp = wb.create_sheet("Detalhe por origem", 1)
head(wp, 1, ["Categoria", "Fonte", "Placa / motorista / posto", "Qtd. lançamentos", "Valor (R$)", "% da categoria"])
agg = {}
for r in data:
    if r[ix["Contar no BI"]] != "Novo - validar": continue
    cat = r[ix["Categoria"]]
    key = r[ix["Placa/Cartao"]] or r[ix["Responsavel"]] or r[ix["Fornecedor/Posto"]] or "(sem identificação)"
    if cat == "Combustível" and r[ix["Fonte"]].startswith("webFrota"):
        key = f"Motorista: {r[ix['Responsavel']]}"
    elif r[ix["Placa/Cartao"]]:
        key = f"Placa {r[ix['Placa/Cartao']]}"
    a = agg.setdefault((cat, r[ix["Fonte"]], key), [0, 0.0]); a[0] += 1; a[1] += r[ix["Valor (R$)"]] or 0
tot = {}
for (cat, _, _), v in agg.items(): tot[cat] = tot.get(cat, 0) + v[1]
i = 2
for (cat, fonte, key), v in sorted(agg.items(), key=lambda kv: (-tot[kv[0][0]], kv[0][0], -kv[1][1])):
    wp.append([cat, fonte, key, v[0], round(v[1], 2), v[1] / tot[cat]])
    wp.cell(row=i, column=5).number_format = BRL; wp.cell(row=i, column=6).number_format = "0.0%"
    for c in wp[i]: c.font = base
    i += 1
widths(wp, [22, 26, 46, 16, 16, 14]); wp.freeze_panes = "A2"; wp.auto_filter.ref = f"A1:F{i-1}"

wb.save(sys.argv[2])
print("ok", len(data), "linhas;", len(agg), "grupos")
