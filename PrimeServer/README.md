# PrimeServer — MVP 0.1

Servidor local de desenvolvimento para Windows com painel Tkinter e Docker Compose, inspirado em XAMPP e Laragon.

## Requisitos
- Python 3 + Tkinter no Windows
- Docker Desktop em execução (WSL2 ativo)
- Internet para baixar imagens no primeiro uso

## Início rápido
1. Clone o repositório e entre na pasta PrimeServer:
   `git clone https://github.com/Abnerrum/AI.git`
   `cd AI\PrimeServer`
2. Abra Docker Desktop e verifique `docker compose version`.
3. Execute `INICIAR.bat` e clique em **Iniciar tudo**.
4. PHP/Laravel: http://localhost:8080
5. Python/FastAPI: http://localhost:8000 (docs em /docs)
6. Java: http://localhost:8081
7. Banco MariaDB opcional: clique **Iniciar banco** (porta local 3307).

SQLite roda como biblioteca embutida em PHP/Python, sem processo de servidor dedicado.

## Laravel
O Nginx utiliza `apps/php/public`, o diretório público do Laravel. Para criar projeto Laravel nessa pasta, faça backup/remova o index.php de exemplo e rode:
`docker compose run --rm php composer create-project laravel/laravel .`
Verifique requisitos de versão PHP do Laravel selecionado. O PHP disponibiliza Composer e PDO SQLite/MySQL.

## Segurança e limites
- Versão inicial de desenvolvimento local, sem autenticação, domínios virtuais, HTTPS, múltiplos projetos ou seleção de runtimes.
- As portas estão restritas a 127.0.0.1: não exponha os serviços diretamente à internet.
- O painel cria automaticamente um .env com senhas fortes do banco; não publique .env.
- Não use `docker compose down -v` para não perder dados do MariaDB.

## Diagnóstico
```powershell
docker compose config
docker compose ps
docker compose logs --tail 50
```

## Estrutura
- manager/app.py: painel de controle
- docker-compose.yml: serviços
- nginx/default.conf: Nginx
- apps/php: PHP 8.3
- apps/python: Python 3.12 e FastAPI
- apps/java: Java 21

Este é um MVP ainda não validado no ambiente Windows do usuário.
