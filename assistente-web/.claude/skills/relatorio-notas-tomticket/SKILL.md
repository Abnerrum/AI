---
name: relatorio-notas-tomticket
description: Puxa do TomTickets todas as notas (garantia, incentivos, Store+) de um periodo com empresa, numero da NF, documento, valor, vencimento e protocolo, e gera Excel. Use quando o usuario pedir "puxa as notas de DD/MM ate DD/MM" ou planilha das notas.
---

# Relatorio de notas pelos chamados do TomTickets

A fonte e o TomTickets (NAO o Conta Azul): cada nota emitida tem um chamado com NF no titulo.

## Como puxar (aba ja logada em samsungbpo.tomticket.com)
1. Fechados: /helpdesk/arquivo?p=N (15 por pagina, mais recentes primeiro). Abertos: /helpdesk. Ir paginando via fetch em JS ate passar da data inicial.
2. Do HTML da lista tirar protocolo (#NNNNNN), titulo, data e o link /helpdesk/detalhes/{id} (o id do link nao e o protocolo).
3. Abrir cada detalhe e extrair por regex: "Numero do Documento", "Valor", "Vencimento", "Vendor/Partner Number: ASC - EMPRESA".
4. Mostrar o resultado no DOM (um <pre>) e ler com get_page_text: o retorno do javascript_tool trunca em ~1000 caracteres.
5. Dedupar protocolos repetidos (a paginacao repete linhas).

## Excel
- Modelo de script: gerar_notas_tomticket.py (raiz do projeto), roda com `venv\Scripts\python.exe -I script.py saida.xlsx`. Abas: Garantia (com total e subtotal por empresa por formula), Incentivos e Store+, Outros chamados. Salvar em C:\Users\Samsung\Downloads.

## Cuidados
- Separar garantia de incentivo/P4P/Store+/GD TA e de chamados que nao sao nota (Relatorio de Pagamentos, Sprinklr, pendencias, Reforma Tributaria).
- Sinalizar NF com chamado duplicado ou valores trocados (ex.: NF 386/387 TXM) e valores repetidos (NF 427/429 Nucleo).
- ASC 4885160 aparece no TomTickets como "AXT GOIANIA LTDA", mas e o Buriti no registro do usuario; confirmar.
- Data do chamado != data de fechamento da garantia (fechamento esta no titulo).
