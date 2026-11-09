---
name: emitir-nota-garantia-samsung
description: Emite no Conta Azul Pro a NFS-e de garantia Samsung (3x por semana) clonando a venda mais recente da mesma empresa a partir do PDF "Dados do fechamento de Garantia". Use quando o usuario pedir para emitir/lancar notas de garantia.
---

# Nota de garantia Samsung (Conta Azul)

Entrada: PDF "Dados do fechamento de Garantia" (nome = codigo da ASC), com Data de Fechamento, ASC, Documento Numero e "Total a receber (Valor para Emissao de NF)". Pecas em garantia ficam fora da nota.

Empresas (troca de conta pelo menu superior direito; quem troca e o usuario): Nucleo ASC 2446971 (Goiania); TXM Vitoria ASC 3192793; AXT Anapolis ASC 3178021; AXT Buriti ASC 4885160; AXT Goiania ASC 3178766. Centro de custo da obra: Nucleo/TXM/Anapolis C8201245; Buriti C820124.

## Passos
1. Servicos > Vendas de servicos > Mais filtros > Centro de custo > digitar "gara" > marcar GARANTIA SAMSUNG > Aplicar.
2. Na venda mais recente da mesma empresa: Acoes > Clonar.
3. No clone trocar so: Numero da venda = Documento Numero do PDF; valor unitario/Total = Total a receber (sair do campo com Tab para atualizar a parcela); nas Observacoes complementares da nota, data de fechamento e "Documento numero". O resto (ASC, municipio, banco, centro de custo, data, vencimento, vendedor) vem do clone.
4. Salvar (canto inferior direito) > Detalhes da venda > Nota fiscal > Emitir nota fiscal > previa > Emitir Nota Fiscal.
5. Fica "Nota Fiscal em espera" e depois "Emitida com sucesso"; conferir em Servicos > Notas fiscais de servico.

## Regras
- Emitir nota e irreversivel: confirmar com o usuario antes do clique final.
- Nunca clicar em Cancelar nota sem pedido.
- Se a prefeitura rejeitar (ex.: Buriti NFS-e 374: regime especial/aliquota, grupo IBS/CBS), nao reemitir; avisar o usuario/contador.
- Aviso "Cliente inadimplente" no clone da Anapolis pode ser ignorado.
- Em Notas fiscais de servico, Acoes: Visualizar NFS-e, Download DANFSE ("Espelho da nota" = PDF RPS-xxx), Download XML.
- Depois de emitir, seguir com a skill chamado-tomticket-garantia.
