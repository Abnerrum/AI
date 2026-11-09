"""Junta as 4 fontes de despesa numa tabela unica (BI_DESPESAS).

Uso: python -I gerar_bi_despesas.py PASTA_ANEXOS SAIDA.xlsx
"""
import glob
import os
import sys

import pandas as pd

pasta, saida = sys.argv[1], sys.argv[2]
COLS = ["Fonte", "Data", "Mes", "Area", "Categoria", "Tipo de despesa", "Placa/Cartao",
        "Responsavel", "Fornecedor/Posto", "Descricao", "Quantidade", "Valor (R$)",
        "Situacao", "Contar no BI", "ID origem"]


def achar(padrao):
    return sorted(glob.glob(os.path.join(pasta, padrao)))[0]


def num_br(s):
    return pd.to_numeric(s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                         errors="coerce")


def linhas(df, **fixos):
    out = pd.DataFrame({c: df.get(c) for c in COLS})
    for k, v in fixos.items():
        out[k] = v
    out["Mes"] = pd.to_datetime(out["Data"]).dt.strftime("%Y-%m")
    out["Data"] = pd.to_datetime(out["Data"]).dt.strftime("%Y-%m-%d")
    return out[COLS]


# 1. Cartao combustivel (conta no BI)
c = pd.read_csv(achar("*relatorio-analise-consumo*.csv"), sep=";", encoding="cp1252", dtype=str)
comb = pd.DataFrame({
    "Data": pd.to_datetime(c["Data/ Hora transação"], format="%d/%m/%Y %H:%M:%S"),
    "Categoria": c["Tipo Mercadoria"], "Tipo de despesa": c["Mercadoria"],
    "Placa/Cartao": c["Placa"], "Responsavel": c["Nome Veículo"],
    "Fornecedor/Posto": c["Nome EC"], "Descricao": c["Cidade EC"] + "/" + c["UF EC"],
    "Quantidade": num_br(c["Qtd Mercadoria"]), "Valor (R$)": num_br(c["Valor total com desconto"]),
    "ID origem": "CC-" + c["N° autorização"],
})
comb = linhas(comb, Fonte="Cartao Combustivel", Area="Frota Nucleo", Situacao="Realizado")
comb["Contar no BI"] = "Sim"

# 2. Historico do posto (mesmo abastecimento: nao soma)
h = pd.read_csv(achar("*historico_consumo*.csv"), sep=";", encoding="utf-8", dtype=str)
h = h[h["Cupom"].notna()]
hist = pd.DataFrame({
    "Data": pd.to_datetime(h["Data/Hora"], format="%d/%m/%Y %H:%M:%S"),
    "Categoria": "Combustivel", "Tipo de despesa": h["Produto"],
    "Placa/Cartao": h["Placa"].str.replace("-", "", regex=False), "Responsavel": h["Motorista"].str.strip(),
    "Fornecedor/Posto": h["Posto"], "Quantidade": num_br(h["Quant.to "]),
    "Valor (R$)": num_br(h["Valor Venda"]), "ID origem": "PX-" + h["Cupom"],
})
hist = linhas(hist, Fonte="Posto (historico)", Area="Frota Nucleo", Situacao="Realizado")
hist["Contar no BI"] = "Nao"

# 3. Clara (so autorizadas)
cl = pd.read_csv(achar("*Clara-transactions*.csv"), dtype=str)
cl = cl[cl["Status"] == "Autorizada"]
clara = pd.DataFrame({
    "Data": pd.to_datetime(cl["Data da Transação"]), "Categoria": cl["Categoria da Compra"],
    "Tipo de despesa": cl["Grupos"], "Placa/Cartao": cl["Cartão (últimos 4)"],
    "Responsavel": cl["Titular"], "Fornecedor/Posto": cl["Comércio"], "Descricao": cl["Descrição"],
    "Valor (R$)": pd.to_numeric(cl["Valor em R$"]), "Situacao": cl["Status de Aprovação"],
    "ID origem": "CL-" + cl["ID da Transação"].str[:8],
})
clara = linhas(clara, Fonte="Clara", Area="Cartao Clara")
clara["Contar no BI"] = "Sim"

# 4. Localiza (detalhe por placa da fatura; total da fatura ja entra pelo portal)
xls = achar("*.xls")
partes = []
for aba, cat, tipo in [("ALUGUEL", "Locacao", None), ("MULTA DE TRÂNSITO", "Multas de transito", "Motivo da infração"),
                       ("PREFIXAÇÃO DANOS - AVARIAS", "Manutencao e danos", "Tipo de despesa")]:
    d = pd.read_excel(xls, sheet_name=aba, header=3, dtype=object).iloc[:, 1:]
    d = d[d["Placa"].notna() & pd.to_numeric(d["Valor total"], errors="coerce").notna()]
    ref = d["Fatura"].astype(str)
    partes.append(pd.DataFrame({
        "Data": pd.to_datetime(d["Data de emissão"]), "Categoria": cat,
        "Tipo de despesa": d[tipo] if tipo else "Aluguel", "Placa/Cartao": d["Placa"],
        "Responsavel": d["Usuário"], "Fornecedor/Posto": "Localiza", "Descricao": d["Modelo"],
        "Valor (R$)": pd.to_numeric(d["Valor total"]), "ID origem": "LZ-" + aba[:3] + "-" + ref + "-" + d["Placa"].astype(str),
    }))
loc = linhas(pd.concat(partes), Fonte="Localiza (detalhe por placa)", Area="Localiza GO", Situacao="A vencer")
loc["Contar no BI"] = "Nao"

base = pd.concat([comb, hist, clara, loc], ignore_index=True)
base["Quantidade"] = base["Quantidade"].round(2)
with pd.ExcelWriter(saida) as w:
    base.to_excel(w, sheet_name="BI_DESPESAS", index=False)
resumo = base.groupby(["Fonte", "Contar no BI"]).agg(Linhas=("Valor (R$)", "size"), Total=("Valor (R$)", "sum")).round(2)
print(resumo.to_string())
print("Total que conta no BI:", round(base.loc[base["Contar no BI"] == "Sim", "Valor (R$)"].sum(), 2))
print("Sem valor:", int(base["Valor (R$)"].isna().sum()))
