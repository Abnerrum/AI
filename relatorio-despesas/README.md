# BI Financeiro · Núcleo Service · Aba Despesas

Sistema web privado de relatórios com upload Excel/CSV, lançamento manual e dashboards.

## Recursos
- Login administrativo (não deixa despesas expostas sem autenticação).
- Importar Excel `.xlsx` da planilha original, preferindo `BI_GRAFICOS`, ou CSV.
- Não duplica registros já importados. Ignora `Status BI` diferente de `Incluir`.
- Cadastrar despesa manualmente; os números são armazenados no banco.
- Filtrar por categoria, Garantia/Fora de Garantia, origem, placa, situação, período e texto.
- Gráfico por categoria em ordem decrescente, evolução mensal, tabela expansível por grupos/categorias/descrições e detalhamento.
- Exportar CSV filtrado e imprimir/salvar PDF.

## Executar no Windows

Você pode executar `iniciar_windows.bat` (duplo clique). O script instala dependências e abre o servidor. É necessário Python instalado e acesso à internet na primeira execução.

**Opção manual:**
1. Instale Python 3.11 ou mais recente.
2. `python -m venv .venv`
3. `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Configure uma senha no terminal: `set ADMIN_PASSWORD=SuaSenhaForteAqui` (CMD) ou `$env:ADMIN_PASSWORD="SuaSenhaForteAqui"` (PowerShell).
6. `python app.py`
7. Acesse `http://127.0.0.1:5000` e entre com usuário `admin`.
8. Clique **Importar Excel / CSV** e selecione o arquivo original (aba `BI_GRAFICOS`).

O banco local é salvo em `dados/despesas.db`, que deve ser protegido e não está no Git.

## Hospedar no Render
1. Suba somente o **código** para um repositório GitHub. **Nunca suba arquivos `.xlsx`, CSV, JSON com dados financeiros nem o banco `.db`**.
2. Crie PostgreSQL no Render para armazenar as despesas de forma persistente.
3. Crie um Web Service Python apontando para o repositório. Comandos:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Variáveis de ambiente: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`, `COOKIE_SECURE=1` e `DATABASE_URL` (PostgreSQL).
5. Abra o link `https://SEU-SERVICO.onrender.com` e importe seu Excel após fazer login.

⚠️ Serviço Render gratuito pode hibernar após 15 minutos sem acesso. O PostgreSQL gratuito **expira em 30 dias** e não oferece backups. Para dados financeiros de produção, use um banco persistente com backups e política de acesso adequada. Sem `DATABASE_URL` persistente, dados do SQLite em hospedagem efêmera podem ser perdidos.

## Layout de entrada
São obrigatórias as colunas `Data`, `Categoria`, `Valor (R$)`. Recomendadas: `Descrição`, `Placa/Cartão`, `Tipo de atendimento`, `Origem`, `Fornecedor/Posto`, `Situação`, `ID origem`, `Status BI`. O arquivo completo pode ter outras abas, que não serão alteradas. O importador prioriza `BI_GRAFICOS`.

## Segurança
Use HTTPS, senha forte e o acesso restrito. Faça backups periódicos do banco. Dados financeiros são privados. Não publique dados de produção como demo aberta.

## Publicar o projeto pelo GitHub

1. Extraia o ZIP e crie um repositório GitHub novo, por exemplo `nucleo-relatorio-web` (mantenha privado se possível).
2. No terminal na pasta do projeto:

```bash
git init
git add .
git commit -m "Criar sistema de relatorios financeiros"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/nucleo-relatorio-web.git
git push -u origin main
```

3. Acesse https://dashboard.render.com/web/new e configure um Web Service Python usando o repositório. Também pode usar o Blueprint `render.yaml` se for a primeira implantação da pasta raiz.
4. Configure `ADMIN_PASSWORD` forte e `SECRET_KEY` aleatória. Use `COOKIE_SECURE=1` com HTTPS.
5. Depois da implantação e login, use **Importar Excel / CSV** para enviar a base privada. O código GitHub **não contém dados financeiros reais**.