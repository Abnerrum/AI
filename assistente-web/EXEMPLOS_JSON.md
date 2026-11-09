# Exemplos de Comandos JSON

Copie e cole estes comandos no terminal do assistente.

---

## 1. Abrir navegador e acessar site

```json
{"acao": "abrir_navegador", "usuario": "abner"}
```

```json
{"acao": "abrir_url", "usuario": "abner", "params": {"url": "http://localhost:5000"}}
```

## 2. Aguardar login manual

```json
{"acao": "aguardar_login", "usuario": "abner", "params": {"timeout": 120}}
```

## 3. Navegar para pagina com filtros

```json
{"acao": "abrir_url", "usuario": "abner", "params": {"url": "http://localhost:5000/ordens?status=Pendente"}}
```

## 4. Extrair tabela simples

```json
{"acao": "extrair_tabela", "usuario": "abner", "params": {"seletor": "#tabela-ordens"}}
```

## 5. Extrair com filtro de colunas

```json
{"acao": "extrair_tabela", "usuario": "abner", "params": {"seletor": "#tabela-ordens", "colunas": ["Numero", "Cliente", "Status", "Tecnico"]}}
```

## 6. Extrair com paginacao

```json
{"acao": "extrair_com_paginacao", "usuario": "abner", "params": {"seletor": "#tabela-ordens", "seletor_proximo": "#btn-proximo", "max_paginas": 10, "colunas": ["Numero", "Cliente", "Status", "Tecnico"]}}
```

## 7. Gerar Excel a partir de dados extraidos

Apos extrair, nao precisa reenviar os dados (o programa guarda a ultima extracao):

```json
{"acao": "gerar_excel", "usuario": "abner", "params": {"nome_arquivo": "ordens_pendentes.xlsx", "titulo": "Ordens Pendentes"}}
```

## 8. Preencher formulario (sem submeter)

```json
{"acao": "abrir_url", "usuario": "abner", "params": {"url": "http://localhost:5000/nova-ordem"}}
```

```json
{"acao": "preencher_formulario", "usuario": "abner", "params": {"campos": {"#cliente": "Empresa ABC Ltda", "#tecnico": "Carlos Silva", "#descricao": "Troca de bateria", "#valor": "350,00"}, "seletor_form": "#form-nova-ordem"}}
```

## 9. Submeter formulario (com confirmacao)

```json
{"acao": "submeter_formulario", "usuario": "abner", "params": {"seletor_botao": "button[type=submit]", "chave_unica": "OS-ABC-2024-10-13", "texto_sucesso": "criada com sucesso"}}
```

## 10. Verificar sucesso

```json
{"acao": "verificar_sucesso", "usuario": "abner", "params": {"texto_sucesso": "criada com sucesso"}}
```

## 11. Tirar screenshot

```json
{"acao": "screenshot", "usuario": "abner", "params": {"nome": "tela_ordens.png"}}
```

## 12. Salvar fluxo reutilizavel

```json
{"acao": "salvar_fluxo", "usuario": "abner", "params": {"nome": "consulta_pendentes", "descricao": "Consulta ordens pendentes e gera Excel", "passos": [{"acao": "abrir_url", "params": {"url": "http://localhost:5000/ordens?status=Pendente"}}, {"acao": "extrair_com_paginacao", "params": {"seletor": "#tabela-ordens", "seletor_proximo": "#btn-proximo", "colunas": ["Numero", "Cliente", "Status", "Tecnico"]}}]}}
```

## 13. Executar fluxo salvo

```json
{"acao": "executar_fluxo", "usuario": "abner", "params": {"nome": "consulta_pendentes"}}
```

## 14. Listar fluxos salvos

```json
{"acao": "listar_fluxos", "usuario": "abner"}
```

## 15. Ver historico

```json
{"acao": "historico", "usuario": "abner", "params": {"limite": 10}}
```

## 16. Ver status do navegador

```json
{"acao": "status", "usuario": "abner"}
```

## 17. Fechar navegador

```json
{"acao": "fechar_navegador", "usuario": "abner"}
```

---

## Instrucoes para usar o ChatGPT como interpretador

### O que voce faz:

1. Abre o ChatGPT em chatgpt.com
2. Descreve o que quer em portugues simples
3. O ChatGPT gera o comando JSON
4. Voce cola no assistente e copia o resultado de volta

### Dica para o ChatGPT:

Cole esta instrucao no inicio da conversa com o ChatGPT:

```
Voce e meu assistente para gerar comandos JSON para um programa de automacao
web local. O programa aceita estas acoes:
abrir_navegador, fechar_navegador, abrir_url, aguardar_login, extrair_tabela,
extrair_com_paginacao, gerar_excel, preencher_formulario, submeter_formulario,
verificar_sucesso, screenshot, salvar_fluxo, executar_fluxo, listar_fluxos,
historico, status, listar_sessoes.

Formato: {"acao": "...", "usuario": "abner", "params": {...}}

Responda SOMENTE com o JSON do proximo comando. Sem explicacoes longas.
Quando eu colar o resultado, gere o proximo passo.
```

### Exemplo de conversa:

**Voce:** "Abra o GSPN e consulte as OS pendentes de hoje"

**ChatGPT:**
```json
{"acao": "abrir_navegador", "usuario": "abner"}
```

**Voce:** (cola no assistente, copia resultado) `{"ok": true, "acao": "abrir_navegador"}`

**ChatGPT:**
```json
{"acao": "abrir_url", "usuario": "abner", "params": {"url": "https://gspn.samsungcsportal.com"}}
```

E assim por diante, passo a passo.


## Correcoes desta versao

A integracao e manual com o site do ChatGPT, sem API. Nenhuma chave e necessaria.
Depois de extrair, gere Excel sem reenviar os dados: `{"acao":"gerar_excel","usuario":"abner","params":{"nome_arquivo":"relatorio.xlsx"}}`. Os dados ficam na memoria por usuario ate encerrar o programa.
O envio exige previa, chave unica, confirmacao local e texto/seletor de sucesso. Resultado incerto bloqueia reenvio; consulte o sistema.
Login agora aguarda ENTER no terminal depois do login completo.
Nao ha integracao especifica com Clara: seletores, filtros e confirmacao precisam ser configurados e validados no site real.
Fluxos salvos sao locais e compartilhados entre usuarios do programa; nao sao um sistema de controle de acesso.
