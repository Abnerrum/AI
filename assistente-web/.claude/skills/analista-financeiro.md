# Analista Financeiro — Núcleo Service

Use esta skill sempre que o usuário pedir análise, relatório ou consolidação de dados financeiros.
Também é acionada automaticamente pelo agendador quando novos arquivos chegam em Downloads.

## Fontes de dados

| Fonte | Arquivo típico | O que contém |
|---|---|---|
| Cartão combustível | `*relatorio-analise-consumo*.csv` | Abastecimentos via cartão frota |
| Posto (histórico) | `*historico_consumo*.csv` | Abastecimentos no posto próprio |
| Clara (cartão) | `*Clara-transactions*.csv` | Despesas do cartão corporativo Clara |
| Localiza (frota) | `*.xls` abas ALUGUEL / MULTA / DANOS | Locação, multas e avarias da frota |
| Garantia Samsung | PDFs numéricos (ex: `4885160.pdf`) | Fechamentos de garantia para NFS-e |

## Fluxo padrão ao receber arquivo novo

1. **Identificar** o tipo de arquivo pelo nome e conteúdo
2. **Ler** com `Read` (CSV/XLS) — nunca pedir para o usuário colar o conteúdo
3. **Analisar**:
   - Total geral e por categoria/fonte
   - Top 5 maiores despesas (valor, data, responsável)
   - Comparar com histórico se disponível (`relatorios/financeiro/`)
   - Alertas: valor fora do padrão, categoria nova, dado faltando
4. **Resumir** em tabela markdown, curto e direto
5. **Perguntar** se deve gerar o BI consolidado ou executar próxima etapa (lançar no Conta Azul, emitir nota, abrir chamado)

## Consolidar o BI (gerar_bi_despesas.py)

Quando o usuário pedir "consolidar" ou "atualizar o BI":

```
venv\Scripts\python.exe -I gerar_bi_despesas.py PASTA_DOWNLOADS relatorios\financeiro\BI_DESPESAS_AAAA-MM.xlsx
```

Substituir `AAAA-MM` pelo mês atual. Verificar se todos os 4 arquivos de entrada existem antes de rodar.
Após gerar, mostrar o resumo impresso pelo script (totais por fonte e "Contar no BI").

## Relatório HTML do BI

Após consolidar, se o usuário pedir relatório visual:
- Gerar HTML em `relatorios/financeiro/bi-custos-AAAA-MM.html`
- Incluir: total geral, tabela por fonte, top categorias, gráfico de barras simples (CSS puro, sem CDN)
- Usar só dados do arquivo gerado; nunca inventar valores

## Rotinas recorrentes

### Notas de garantia Samsung (3x/semana)
- Skill: `emitir-nota-garantia-samsung` → depois `chamado-tomticket-garantia`
- Sempre aguardar confirmação antes de emitir ou criar chamado

### Fatura Clara (1x/mês)
- Skill: `lancar-fatura-clara`
- Mostrar resumo dos lançamentos antes de executar

### Resumo semanal (segunda-feira)
- Listar: notas pendentes, lançamentos em aberto, chamados TomTickets sem resposta
- Fonte: Conta Azul Pro (Chrome conectado) + TomTickets (Chrome conectado)

## Regras de segurança

- **Nunca** emitir nota, pagar, lançar ou criar chamado sem confirmação explícita do usuário nesta conversa
- Referências de conversas anteriores **não** são autorização atual
- Antes de qualquer ação irreversível: resumir o que vai fazer e aguardar "pode fazer" ou "sim"
- Dados de cartão, senha e tokens: nunca salvar na memória
