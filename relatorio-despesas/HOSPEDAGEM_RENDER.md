# Hospedar BI Financeiro da Núcleo Service no Render

## Preparação
Este pacote contém somente código e arquivos-modelo. **Não** inclui `dados/despesas.db`, arquivos reais de despesas ou `.env`.

O GitHub já tem o repositório `Abnerrum/AI` na branch `deploy/nucleo-despesas-web`. A versão nessa branch precisa ser substituída pelo **código deste pacote** (pasta `relatorio-despesas/`).

A conta Render possui o PostgreSQL `nucleo-relatorio-despesas-db`, na região Virginia. Seu plano grátis vence em 12/12/2026; faça backup ou contrate armazenamento durável antes de usar em produção.

## Publicar usando Blueprint
1. Atualize no GitHub a branch `deploy/nucleo-despesas-web` com o conteúdo deste pacote em `relatorio-despesas/`, sem enviar o banco local e as credenciais.
2. No Render, escolha **New > Blueprint** e selecione `Abnerrum/AI`, branch `deploy/nucleo-despesas-web`, Root Directory `relatorio-despesas` se disponível.
3. Confira se `render.yaml` detecta o serviço e a referência ao banco PostgreSQL já existente. **Não crie um banco adicional**.
4. Informe `ADMIN_PASSWORD` forte. `SECRET_KEY` é gerada automaticamente, `COOKIE_SECURE=1` e `DATABASE_URL` vem do banco existente.
5. Confirme o deploy e verifique `/health` e a página `/login`.

## Publicar criando Web Service manualmente
1. New > Web Service > Build and deploy from a Git repository.
2. Repository: `Abnerrum/AI`. Branch: `deploy/nucleo-despesas-web`. Root Directory: `relatorio-despesas`.
3. Runtime Python; Region Virginia; Plan Free.
4. Build: `pip install -r requirements.txt`.
5. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
6. Set `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD` forte, `SECRET_KEY` aleatória longa, `COOKIE_SECURE=1` e `DATABASE_URL` com a **Internal Database URL** do banco PostgreSQL existente. NÃO copie a URL no GitHub nem em chat público.
7. Health Check Path: `/health`. Salve e implante.

## Dados
O Render não importa os dados automaticamente. Após login, use **Importar Excel/CSV** para carregar a planilha autorizada. Se precisar manter campos não importáveis que estavam no SQLite, faça uma migração/backup antes.

## Segurança
- Sistema tem senha administrativa e cookie HTTPS. Use senha única forte e não exponha o banco ou dados de clientes.
- Configure backups. O banco grátis Render expira e não serve como armazenamento definitivo sem upgrade.
- Evite dados de produção em demonstrações públicas.
