---
name: lancar-fatura-clara
description: Lança no Conta Azul Pro (Financeiro > Contas a pagar) as compras do CSV da fatura Clara, clonando um lançamento da Clara e trocando só descrição, valor e categoria. Use quando o usuário pedir para lançar/conferir a fatura Clara ou "clara nucleo.csv".
---

# Lançar fatura Clara no Conta Azul

Usa o Chrome do usuário (Claude in Chrome), já logado. Antes de qualquer lançamento, confirme com o usuário o que ele autorizou; ele pediu para lançar e salvar tudo e conferir depois.

## 1. Analisar o CSV (PowerShell)
- Arquivo costuma estar em `C:\Users\Samsung\Desktop\clara nucleo.csv` (separador `;`, valores com ponto decimal, datas dd/MM/yyyy). O cabeçalho NÃO bate com os dados. Colunas reais por linha: 0 data compra; 1 data autorização; 2 período de faturamento; 3 estabelecimento; 4 valor; 5 apelido do cartão; 6 titular; 7 centro (In Home/Gerencia/MIDEA); 8 status; 9 código; 10 categoria Clara; 11 comentário. Descrições com `;` deslocam colunas.
- Só `Autorizada`. Ignorar `Recusada`. Valores negativos (estornos/IOF negativo): o Conta Azul não aceita despesa negativa — avisar o usuário.
- Totais por período: fatura fechada (ex.: 09/09–08/10) e aberta (09/10–08/11). Já existe um lançamento-total "Clara - Fatura Cartão" (categoria 2.04.09.03) que cobre a fatura; os itens individuais são o detalhamento.
- Descartar o que já está lançado: abrir Contas a pagar (mês), pegar os lançamentos de 15/10 e comparar por valor (multiset). Parcelas (Samsung/Conta Azul) podem diferir em centavos — tratar como já lançadas. Gravar fila em arquivo (`id|código|valor|descrição`) no scratchpad.
- Descrição = comentário do CSV; se vazio e o estabelecimento termina em `- n/m` usar o estabelecimento; senão o nome da categoria Clara.

## 2. Mapa de categorias (Clara -> Conta Azul)
Almoço/Refeição ADM/Refeiçao almoço-janta/Janta 2.04.02.06 (padrão do modelo clonado: não mexer) | Hospedagem 2.01.22.07 | Combustível 2.01.22.02 | Assinaturas Software 2.02.03.07 (Conta Azul/CONTAAZUL 2.02.03.09; IOF idem Software) | Material OS e Ferramentas 2.04.09.02 | Transporte 2.01.10.01 | Marketing 2.01.02.08 | Material de Escritório/TI 2.01.14.01 | Cash Back 2.04.09.05 | Manutenção Predial 2.04.03.05 | Internet 2.01.11.03 | Pedágio 2.01.22.04 | Utensílios 2.04.11.02 | Material de Limpeza 2.01.21.01 | Manutenção de equipamento 2.01.17.01 | Passagens 2.01.10.02 (Despesas de viagem; palpite, confirmar).

## 3. Lançar (clonando)
Modelo: um lançamento "Almoço" R$ 70,00, 2.04.02.06, vencimento 15/10, conta "Clara - Cartão de Crédito". Alterar SOMENTE descrição, valor e (se diferente) categoria. NUNCA clicar em "Repetir lançamento?" (deixar desligado). Só mudar categoria quando for diferente da do modelo.

Nunca clique por coordenada na lista (já marcou pagamento por engano em linhas existentes). Use JS para achar linha/menu e guardas antes de salvar. Se acontecer pagamento acidental: Ações > "Voltar para em aberto" > Confirmar.

Helpers JS (definir uma vez com `javascript_tool` na aba de Contas a pagar; coordenadas de tela da extensão: descrição (940,168), valor (1330,168), categoria (373,250) no frame 1568x686):
```js
const w=ms=>new Promise(r=>setTimeout(r,ms)); const vis=e=>e.offsetParent!==null; const sc=()=>window.innerWidth/1568;
const top=()=>{const el=document.elementFromPoint(940*sc(),168*sc()); return !!el&&el.tagName==='INPUT'&&el.value==='Almoço';};
window.__clone=async()=>{ const isForm=()=>[...document.querySelectorAll('input')].some(i=>vis(i)&&i.value==='70,00')&&[...document.querySelectorAll('*')].some(e=>vis(e)&&e.children.length===0&&e.textContent.trim()==='Informações do lançamento'); await w(1200); if(isForm()) throw new Error('form already open'); const find=()=>[...document.querySelectorAll('tr,[role=row]')].find(r=>{const t=r.innerText.replace(/\s+/g,' ').trim();return t.startsWith('15/10/2026')&&t.includes(' Almoço 2.04.02.06')&&t.includes(' 70,00 70,00 Em Aberto');}); let row=find(); for(const p of ['1','2','3','4']){ if(row) break; const a=[...document.querySelectorAll('a')].filter(e=>vis(e)&&e.textContent.trim()===p); if(a[0]){a[0].click(); await w(3000); row=find();} } if(!row) throw new Error('source row not found'); const b=[...row.querySelectorAll('button')].find(x=>x.textContent.trim()==='Ações'); row.scrollIntoView({block:'center'}); await w(500); b.click(); await w(900); const it=[...document.querySelectorAll('span')].filter(e=>e.textContent.trim()==='Clonar lançamento'&&vis(e)); if(it.length!==1) throw new Error('clone items '+it.length); it[0].click(); for(let i=0;i<40;i++){ if(isForm()&&top()){await w(1500); if(top()) return 'form ok';} await w(300);} throw new Error('clone form not on top'); };
const root=()=>{ let e=[...document.querySelectorAll('*')].find(x=>vis(x)&&x.children.length===0&&x.textContent.trim()==='Informações do lançamento'); while(e&&!([...e.querySelectorAll('button')].some(b=>b.textContent.trim()==='Salvar'))) e=e.parentElement; return e; };
window.__save=async(D,V,C)=>{ const r=root(); if(!r) throw new Error('no form'); const ins=[...r.querySelectorAll('input')].filter(vis); const d=ins.some(i=>i.value===D), v=ins.some(i=>i.value===V); const c=[...r.querySelectorAll('*')].some(e=>vis(e)&&e.children.length===0&&e.textContent.trim().startsWith(C)); const sb=[...r.querySelectorAll('button')].filter(x=>vis(x)&&x.textContent.trim()==='Salvar'); if(d&&v&&c&&sb.length===1){sb[0].click(); await w(2500); return 'saved '+V;} throw new Error('NOT SAVED d='+d+' v='+v+' c='+c+' sb='+sb.length); };
```
Valores >= 1000 aparecem formatados `1.884,75` no campo (passar assim ao `__save`).

Bloco por item no `browser_batch` (≤ 6 itens por chamada; lotes maiores estouram timeout mas CONTINUAM executando — esperar e auditar, nunca reenviar às cegas):
1. `javascript_tool`: `await window.__clone()`
2. `computer triple_click (940,168)` + `type <descrição>`
3. `computer triple_click (1330,168)` + `type <valor 0,00>`
4. Só se a categoria for diferente: `left_click (373,250)`, `wait 1`, `type <código ex 2.04.09.02>`, `wait 2`, `key "Down Return"`, `wait 1` (sem o `wait 1` após abrir o dropdown a categoria cai errada em "01) Aluguel Imóvel")
5. `javascript_tool`: `await window.__save('<descrição>','<valor>','<código>')` (lança erro e interrompe o lote se descrição/valor/categoria não conferem; então tirar screenshot e corrigir manualmente).

## 4. Auditoria (obrigatória no fim)
Percorrer todas as páginas (o filtro `clara` pode ter 4 páginas de 100) coletando valores das linhas de 15/10 e comparar com o esperado (baseline + fila). Conferir também linhas com categoria `01) Aluguel` (erro) e linhas `Pago` indevidas. Corrigir categoria via Ações > Editar lançamento. Duplicados: listar para o USUÁRIO apagar (não excluir dados).

## 5. Fechamento
Informar ao usuário: quantos lançados, os que ficaram fora (negativos, já lançados, categoria incerta) e duplicados a apagar.
