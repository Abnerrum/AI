"""Gera a tabela NOVAS_FONTES (mesmo esquema da BI_DESPESAS) com Localiza, webFrota e Alelo de 01/09 a 06/11/2026.
Uso: python -I gerar_novas_fontes_bi.py saida.xlsx webfrota.csv alelo.csv"""
import csv, sys
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

COLS = ["Fonte", "Data", "Mes", "Area", "Categoria", "Tipo de despesa", "Placa/Cartao", "Responsavel", "Fornecedor/Posto", "Descricao",
        "Quantidade", "Valor (R$)", "Situacao", "Contar no BI", "ID origem", "Categoria original", "Placa identificada",
        "Tipo de atendimento", "Origem da identificação", "Arquivo de origem", "Observação"]
FG = {"TEU2C47", "TXI5B84"}  # regra do usuario: unicas placas definidas como Fora de Garantia
GO, ES = "09.239.487/0001-34", "39.470.597/0001-73"
rows = []

def num(s):
    return float((s or "0").replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)

def dts(s):  # dd/mm/aaaa [hh:mm:ss] -> date
    d = s.split(" ")[0].split("/")
    return date(int(d[2]), int(d[1]), int(d[0]))

def atend(placa):
    return ("Fora de Garantia", "Regra do usuário (placa)") if placa in FG else ("Sem identificação", "")

# --- Localiza: faturas com emissao a partir de 01/09/2026 (tela Faturas, lida em 06/11/2026)
LOC = [
("AGMTZ 3482329","Multa de trânsito",ES,"15/10/2026","A vencer",330.31),("AGMTZ 3482323","Multa de trânsito",GO,"15/10/2026","A vencer",608.57),
("AGMTZ 3482320","Prefixação de danos",GO,"15/10/2026","A vencer",917.50),("AGMTZ 3432599","Multa de trânsito",ES,"15/09/2026","Paga",278.26),
("AGMTZ 3432592","Prefixação de danos",ES,"15/09/2026","Paga",590.00),("AFMTZ 3695307","Aluguel",ES,"15/09/2026","Paga",24080.05),
("AGMTZ 3436039","Reembolso despesa serviço r/n",GO,"16/09/2026","Paga",606.00),("AGMTZ 3432594","Multa de trânsito",GO,"15/09/2026","Paga",548.04),
("AGMTZ 3432593","Pneu excedente",GO,"15/09/2026","Paga",696.90),("AFMTZ 3695303","Aluguel",GO,"15/09/2026","Paga",48648.82),
("AFMTZ 3784569","Aluguel",ES,"15/10/2026","Paga",24080.05),("AFMTZ 3784565","Aluguel",GO,"15/10/2026","Paga",48960.02),
]
CAT = {"Aluguel": "Locação", "Multa de trânsito": "Infrações"}
for fat, nat, cnpj, em, sit, val in LOC:
    d = dts(em); reg = "Localiza GO" if cnpj == GO else "Localiza ES (TXM)"
    rows.append(["Localiza (faturas)", d, d.strftime("%Y-%m"), reg, CAT.get(nat, "Manutenção e danos"), nat, "", "", "LOCALIZA FLEET S/A",
                 f"Fatura {fat} - {nat}", 1, val, sit,
                 "Duplicado" if (d.month == 10 and cnpj == GO) else "Novo - validar", fat, nat, "", "Sem identificação", "",
                 "Localiza MyFleet > NFs, Faturas e Boletos (06/11/2026)",
                 "Já existe em 'Localiza (detalhe por placa)': as 3 faturas GO de 15/10 somam R$ 50.486,09, igual ao BI" if (d.month == 10 and cnpj == GO)
                 else ("CNPJ TXM (ES): confirmar se entra no BI do Núcleo" if cnpj == ES else "")])

# --- webFrota
with open(sys.argv[2], encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh, delimiter=";"):
        d = dts(r["Data/Hora"])
        rows.append(["webFrota (Quality)", d, d.strftime("%Y-%m"), "Frota Nucleo", "Combustível", "Combustível", "", r["Motorista"], r["Posto"],
                     f'Cupom {r["Cupom"]} - {r["CentroCusto"]}', num(r["Litros"]), num(r["ValorVenda"]), "Realizado",
                     "Possível duplicidade" if d.month == 10 else "Novo - validar",
                     "WF-" + r["Cupom"].replace(".", ""), "Combustível", "", "Sem identificação", "",
                     "webFrota > Relatório > Histórico Consumo (06/11/2026)",
                     "Sem placa na origem; out/2026 pode sobrepor 'Posto (historico)' (59 registros, R$ 7.453,60), comparar cupom a cupom" if d.month == 10 else "Sem placa na origem"])

# --- Alelo (somente compras aprovadas; creditos/limites e negadas ficam fora)
with open(sys.argv[3], encoding="cp1252", newline="") as fh:
    for r in csv.DictReader(fh, delimiter=";"):
        if r["Tipo Transação"] != "Compra" or r["Status Transação"] != "Aprovada":
            continue
        d = dts(r["Data/Hora Transação"]); placa = r["Placa"]; at, orig = atend(placa)
        rows.append(["Alelo Veloe (Transações)", d, d.strftime("%Y-%m"), "Frota Nucleo", "Combustível", r["Mercadoria"] or "Combustível", placa,
                     r["Nome Motorista"], r["Nome EC"], f'{r["Cidade EC"]}/{r["UF EC"]} - {r["Descrição do centro de custo"]}'.strip(" -"),
                     num(r["Qtd Mercadoria"]), num(r["Valor Total com Desconto"]), "Realizado",
                     "Duplicado" if d.month == 10 else "Novo - validar",
                     "AL-" + r["Nº Autorização"], "Combustível", placa, at, orig,
                     "Alelo Veloe Go > Relatório de Transações (06/11/2026)",
                     "Já existe na aba 'Cartao Combustivel': 36 compras, R$ 7.687,02 em out/2026, igual ao BI" if d.month == 10 else ""])

rows.sort(key=lambda x: (x[1], x[0]))
wb = Workbook(); ws = wb.active; ws.title = "NOVAS_FONTES"
ws.append(COLS)
for c in ws[1]:
    c.font = Font(name="Arial", bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F5F55")
for r in rows:
    ws.append(r)
for row in ws.iter_rows(min_row=2):
    row[1].number_format = "yyyy-mm-dd"; row[11].number_format = "#,##0.00"; row[10].number_format = "#,##0.00"
ws.freeze_panes = "A2"
wb.save(sys.argv[1])
from collections import Counter
print(len(rows), Counter(r[0] for r in rows))
