"""
relatorio.py - Geracao de relatorios Excel com Pandas e OpenPyXL.
"""

import os
import re
from datetime import datetime


def gerar_excel(dados: list[dict], caminho: str,
                colunas: list[str] | None = None,
                titulo: str = "Relatorio",
                formatar: bool = True) -> str:
    """
    Gera um arquivo Excel a partir de uma lista de dicionarios.

    Args:
        dados: Lista de dicts com os dados.
        caminho: Caminho do arquivo .xlsx de saida.
        colunas: Lista de colunas a incluir (None = todas).
        titulo: Titulo da planilha.
        formatar: Se True, aplica formatacao visual.

    Returns:
        Caminho absoluto do arquivo gerado.
    """
    if not dados:
        raise ValueError("Nenhum dado para gerar relatorio.")

    if not isinstance(dados, list) or any(not isinstance(r, dict) for r in dados):
        raise ValueError("Dados devem ser uma lista de objetos.")
    import pandas as pd
    df = pd.DataFrame(dados)

    if colunas:
        mapa = {str(c).strip().casefold(): c for c in df.columns}
        if any(c.strip().casefold() not in mapa for c in colunas):
            raise ValueError("Coluna solicitada nao encontrada.")
        df = df[[mapa[c.strip().casefold()] for c in colunas]]
        df.columns = colunas
    titulo = re.sub(r"[\\/*?:\[\]]", "_", str(titulo)).strip("'")[:31] or "Relatorio"
    # Preserva texto externo como texto; nunca como formula Excel.
    for coluna in df.columns:
        df[coluna] = df[coluna].map(lambda v: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v)

    # Garantir diretorio
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)

    # Salvar
    df.to_excel(caminho, index=False, sheet_name=titulo[:31])

    if formatar:
        _formatar_excel(caminho, titulo)

    return os.path.abspath(caminho)


def _formatar_excel(caminho: str, titulo: str):
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    """Aplica formatacao visual ao Excel gerado."""
    wb = load_workbook(caminho)
    ws = wb.active

    # Estilos
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    borda = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    zebra_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")

    # Cabecalho
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = borda

    # Dados
    for i, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=2):
        for cell in row:
            cell.border = borda
            cell.alignment = Alignment(vertical="center")
            if i % 2 == 0:
                cell.fill = zebra_fill

    # Ajustar largura
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                val_len = len(str(cell.value or ""))
                if val_len > max_len:
                    max_len = val_len
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(caminho)


def resumo_dados(dados: list[dict]) -> dict:
    """Gera um resumo compacto dos dados para enviar ao Claude."""
    if not dados:
        return {"total": 0, "colunas": [], "amostra": []}

    import pandas as pd
    df = pd.DataFrame(dados)
    return {
        "total": len(df),
        "colunas": list(df.columns),
        "amostra": df.head(3).to_dict(orient="records"),
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
