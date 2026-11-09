---
name: chamado-tomticket-garantia
description: Prepara o chamado de pagamento de mao de obra de garantia no TomTickets Samsung BPO para cada nota emitida (formulario preenchido, usuario anexa XML+PDF e manda criar). Use apos emitir notas de garantia ou quando pedirem para abrir chamado da nota.
---

# Chamado TomTickets por nota de garantia

Site: https://samsungbpo.tomticket.com/helpdesk/novo (login so do usuario; se cair no login, parar e pedir para logar). Modelos completos: C:\Users\Samsung\Downloads\INSTRUCOES_TOMTICKET_SAMSUNG.md.

## Campos
- Departamento Payment BPO (101916); Tipo "Pagamento de Mao-de-obra de Servicos" (173097). Esperar ~3s apos escolher cada um.
- Numero do Documento, Valor (virgula), Vencimento (dd/mm/aa), Vendor/Partner Number (ASC), Assunto (= 1a linha da mensagem), Mensagem, Cc, anexos XML + PDF (RPS).
- Copia fixa: lidiane@gruponucleoservice.com.br, rh.financeiro@gruponucleoservice.com.br, nfservico@samsung.com.
- Preencher via JS: codproduto, codtipoassunto, campodinamico[62119]=doc, [86089]=valor, [31071]=vencimento, [33651]=vendor, titulo, mensagem, copia (selectize).
- Vencimento: fechamento ate dia 15 -> dia 25; se a nota saiu depois do dia 15 o usuario ja definiu o dia 10 do mes seguinte (ex.: 10/11/26). Perguntar se houver duvida.

## Mensagens (1a linha = Assunto)
- Nucleo: "NF {N} Prestacao de servico de Garantia Fechamento dd/mm/aaaa"
- TXM: "NF {N} Referente ao fechamento do dia dd/mm/aaaa"
- Anapolis: "NF {N} Fechamento garantia do dia dd/mm/aaaa"
- AXT Goiania/Buriti: "NF {N} Referente ao fechamento de Garantia do dia dd/mm/aaaa"
- Demais linhas: Codigo da ASC / Documento numero / Municipio / Dados bancarios / Centro de custo de mao de obra.

## Regras
- Upload de anexo so aceita pastas liberadas com /add-dir (Downloads nao esta); senao o usuario anexa.
- Nunca clicar em "Criar Chamado" sem o usuario escrever "criar". Depois de criar, informar o protocolo e anotar no APRENDIZADO.md.
