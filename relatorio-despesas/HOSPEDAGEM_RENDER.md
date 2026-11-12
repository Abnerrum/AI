# Publicação no Render — Núcleo Service / Despesas

O código foi enviado à ramificação isolada do GitHub:
**https://github.com/Abnerrum/AI/tree/deploy/nucleo-despesas-web/relatorio-despesas**

A ramificação `main` do repositório AI não foi alterada.

## Recursos
- PostgreSQL gratuito criado no Render: https://dashboard.render.com/d/dpg-dbqthaijnfac73ap5e10-a
- Banco de dados: `nucleo_relatorio_despesas_db` — região Virginia, gratuito (expira em 12/12/2026).
- **Web Service ainda não publicado.** Conclua no painel Render.

## Publicar o Web Service

1. Entre em https://dashboard.render.com/web/new e escolha **Build and deploy from a Git repository**.
2. Selecione o repositório **Abnerrum/AI**.
3. Nome: `nucleo-despesas-abner` (ou nome livre).
4. Branch: `deploy/nucleo-despesas-web`.
5. Root Directory: `relatorio-despesas`.
6. Runtime: **Python**, Plan: **Free**, Region: **Virginia**.
7. Build Command: `pip install -r requirements.txt`.
8. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
9. Environment Variables (defina apenas no Render, não no GitHub):

| Variável | Valor |
| --- | --- |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | Sua senha forte exclusiva |
| `SECRET_KEY` | Chave aleatória longa (gere com Python `import secrets; print(secrets.token_urlsafe(48))`) |
| `COOKIE_SECURE` | `1` |
| `DATABASE_URL` | **Internal Database URL** copiada da página do PostgreSQL acima (contém senha; mantenha privada). |

10. Health Check Path: `/health`.
11. Clique em **Create Web Service** e confirme o deploy com status `Live`.
12. Entre na URL `.onrender.com`, faça login com `admin`, clique **Importar Excel / CSV** e envie o arquivo Excel original.

O site **bloqueia importações e cadastros na hospedagem se o PostgreSQL não estiver configurado**, para evitar perda de dados no disco temporário do Render.

## Cuidados
- O PostgreSQL Render **Free expira após 30 dias** (no seu caso, 12/12/2026); faça backup e migre antes do vencimento.
- Para utilização financeira continuada, use PostgreSQL persistente com backups e controle de acesso adequado.
- Não adicione `.xlsx`, `.csv` financeiros ou `.db` ao GitHub; só o código deve estar no repositório.
- A página de login protege o painel, mas não substitui gestão de usuários e auditoria de produção.