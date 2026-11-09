# Documentação do sistema COS (CSP Goiânia)

Gerada em 13/10/2026 por exploração somente leitura (nenhum dado foi salvo, enviado ou alterado).
Fonte: navegação autenticada em `http://192.168.25.131:8080/COS_CSO/` (rede interna).

---

## 1. Visão geral

O **COS** é um sistema web interno de **gestão de assistência técnica autorizada Samsung**. A unidade identificada no título é **CSP Goiânia**. Ele cobre o ciclo completo de uma Ordem de Serviço (OS), do recebimento do aparelho até a entrega ao cliente, e também estoque de peças, pedidos ao fabricante, devoluções, notas fiscais e relatórios.

Ele é integrado ao **GSPN** (portal de serviços da Samsung): a tela inicial mostra o status da conexão (`Code: 10011 - Sucesso`) e o último **MOTP** (código OTP usado na integração).

### Tecnologia observada
- Aplicação Java com páginas **JSP** (`*.jsp`), servidor na porta 8080, contexto `/COS_CSO`.
- Interface em **frames**: `Principal.jsp` contém `Menu.jsp` (menu lateral) e `PaginaInicial.jsp` (área de conteúdo).
- Há **duas gerações de telas**: as antigas em JSP e as novas em caminhos `new/...` e `front/...` (provavelmente front-end moderno).
- Sessão por login (cookie). O usuário logado aparece no topo do menu, com botão **Sair**.

### Tela de login (`Entrar.jsp`)
Campos **Usuário** e **Senha** e botão **Entrar**. Há 2FA/OTP na integração GSPN (Master OTP, em Administrar).

---

## 2. Navegação

Menu lateral esquerdo, com 14 grupos que expandem e recolhem. Um selo vermelho mostra pendências (na exploração, **Gerenciamento de Pedidos** tinha 3). O ícone de casa leva à tela inicial.

Tela inicial: painel com **Último MOTP** (data/hora e código) e **GSPN conn status**.

---

## 3. Módulos e telas

Formato: **Nome da tela** — arquivo/URL.

### 3.1 Ordem de Serviço (núcleo do sistema)

**Entrada e criação**
- Entrada/Saída colmeia — `ControleColmeia.jsp` (controle de colmeia/prateleira dos aparelhos)
- Cores — `cores.html` (legenda de cores)
- Verificar Garantia pelo IMEI — `VerificarGarantiaProdutoPorIMEI.jsp`
- Agenda — `Agenda.jsp`
- Criar Ticket IQC — `CriarTicketRRR.jsp`
- **Criar Ordem de Serviço** — `CriarOrdemDeServico3.jsp`
- Consultar Cliente — `ConsultarCliente.jsp`
- **Buscar Ordem de Serviço** — `BuscarOrdemServico.jsp`
- Anexos — `GerenciarAnexos.jsp`

**Filas por etapa do fluxo** (cada uma lista as OS naquela etapa)
- Designar Técnico — `DesignarTecnico.jsp`
- OS Designada — `OrdemServicoDesignada.jsp`
- Ag. Check List — `AguardandoCheckList.jsp`
- OS Ag. Inserir Orçamento — `AguardandoInserirOrcamento.jsp`
- OS Ag. Aprovação — `OSAguardandoAprovacao.jsp`
- OS Ag. Negociação Orçamento — `OSAguardandoNegociacaoOrcamento.jsp`
- OS Ag. Peças — `OrdemServicoAguardandoPecas.jsp`
- Prontos – Entrar em Contato — `ProntosAguardandoContato.jsp`
- OS Enviar AR — `OSGerarGTIAR.jsp`

**Integração com o fabricante (GSPN)**
- Abrir OS Venda GSPN — `OSVendaAguardandoAbrirOSFabricante.jsp`
- Abrir OS Venda Externa GSPN — `OSVendaAguardandoAbrirOSFabricanteTJ.jsp`
- Abrir OS Fabricante — `AbrirOSFabricante.jsp`

**Consultas e apoio**
- Histórico — `ListarTodoHistorico.jsp`
- Cadastrar/Alterar Produto — `BuscarProduto.jsp`
- Rastreamento por Status — `RastreamentoPorStatus.jsp`
- Download Ordem Serviço — `BuscarDownloadOrdemServico.jsp`
- Liberar OS Coleta — `LiberarOSLGMassa.jsp`
- Informações de Peças — `InformacaoDePecaParaAtendimento.jsp`
- Buscar Peça Caixa — `BuscarPecaCaixa.jsp`
- Peças Solicitadas pelo Lab — `PecasRequisitadasPeloLaboratorioPaginaUsuario.jsp`
- OS Pendente Ação ASC — `OSPendenteResponsabilidadeASC.jsp`
- Histórico IQC — `HistoricoIQC.jsp`
- Flag — `OSComFlag.jsp`
- Orçamentos — `new/so/QuotationPending`
- Editar Serviço — `new/so/Service`
- Erro criação automática — `new/so/ServiceOrderCreateLog`
- Tag — `new/so/Tag`

### 3.2 AEG
- SAW — `OSAguardandoSAW.jsp`
- Regras — `new/saw/Saw`

### 3.3 In Home (atendimento na casa do cliente)
- OSs — `new/ih/GerarRota`
- Planejamento de rota — `new/ih/route/index.html`
- Download SW — `ControleDownloadAnexoOS.jsp`

### 3.4 Entrega Produto
- Prontos – Entrar em Contato — `ProntosAguardandoEntrega.jsp`
- Agenda Entregas — `AgendaEntregaProduto.jsp`
- Download Entregas — `DownloadEntregaProduto.jsp`
- Auditoria de contato incorreto — `AuditoriaContato.jsp` (e download: `DownloadAuditoriaContato.jsp`)

### 3.5 Garantia
- OS Criar Garantia — `OSSemCriarGarantia.jsp`
- Relatório Garantias — `HistoricoGarantia.jsp`

### 3.6 Concierge (empréstimo de aparelho)
- Produtos de Empréstimo — `BuscarProdutoEmprestimo.jsp`
- Empréstimos — `HistoricoEmprestimo.jsp`
- OS Concierge Pendente — `OSConciergePendenteResponsabilidadeASC.jsp`

### 3.7 Gerenciamento de Pedidos
- AR AP — `ARAP.jsp`
- Histórico de Pedidos — `HistoricoPedidos.jsp`
- Comparar OS pendentes com peça entregue — `CompararOSPen...jsp`
- Comparar OS Pendente com Estoque — `CompararOSPendenteComEstoque.jsp`
- Peças Solicitadas pelo Lab — `PecasRequisitadasPeloLaboratorio.jsp`
- Saída peças — `new/inv/Requisicao`
- OS Ag. Pedir Peças — `OrcamentoAguardandoPecas.jsp`
- Pedidos por OSs — `new/partorder/SoPartOrder`

### 3.8 GSPN (consultas e ações no portal Samsung)
Verificar Garantia pelo IMEI, Buscar Delivery, Buscar NF, Balanço por Código Modelo, Buscar Dados RMA, Buscar Dados Garantia, Abrir Link GTI, Buscar Dados por IMEI, Adicionar Peça na OS, Criar Pedido Peça.

### 3.9 Estoque
- Local — `new/inv/LocalizacaoPeca`; Inserir Localização Peça
- Upload XML (NF-e) — `UploadXMLNFE.jsp`
- Inserir Peça Estoque Manualmente — `new/inv/InserirPecaEstoqueManualmente`
- Informações de Peças Cadastradas; Buscar Peça no Estoque; Informações de Notas Fiscais
- Alterar Estoque da Peça; Transferir Peças de Armazém; Histórico Transferência
- Ajustar Estoque com Balanço GSPN; Histórico Ajuste; Upload Estoque GSPN
- NF Pendente de Recebimento; Peça Pendente de Recebimento
- Inventário; Contagem (`new/inv/Contagem`)
- Downloads: Lista de Códigos de Peças, Lista de Peças em Estoque
- Peças Mais Usadas por Período; Histórico Peças
- Remessas: Gerar/Histórico Remessa de Pagamento; Gerar/Histórico Remessa Devolução de Peças
- Externo Pendentes verificação; Verificar disponibilidade de peças – MIX; Peças pendentes de análise
- Cadastros: Markup de peças (`new/part/PartCategory`), Categoria de peças (`new/part/PartCategorySaw`), Fornecedores (`front/supplier/`)

### 3.10 Devolução Peças Novas
Peças para Devolução por NF, Devolver Peças por ID, Histórico Devoluções, Atualizar Devolução para Coletada (em massa), Comparar NF devolvida com Creditada.

### 3.11 Devolução Peças Usadas
Confirmar Recebimento, Local de Armazenamento da Peça Usada, Gerar Nova Devolução, Devolução sem Uclass, Histórico Devoluções, Download Lista de Peças em Estoque, Buscar Peça no Estoque, Relatório Estoque.

### 3.12 Administrar
Editar Usuário, Acessos de Usuários (`front/authorization/user/`), Perfis (`front/authorization/role/`), Editar Técnico, Master OTP (`RegistrarOTP.jsp`), Usuário GSPN, Commala, Medição Temp/Umidade (`RegistrarTesteLaboratorio.jsp`).
Controle de acesso por **usuário e perfil (role)**.

### 3.13 Relatórios
Produção por Técnico, Relatório OS, Relatório Estoque, Relatório Orçamentos (`new/report/...`).

### 3.14 Nota Fiscal
OS Ag. Emitir NF — `OSAguardandoEmitirNF2.jsp`.

### 3.15 Posto Coleta (versão reduzida para postos parceiros)
Criar OS, Buscar OS, Buscar Dados por IMEI, Rastreamento por Status, Orçamentos, Remessa (`new/cp/Coletas`), Informações de Peças Cadastradas.

---

## 4. Telas principais em detalhe

### 4.1 Buscar Ordem de Serviço
Filtros: **OS Interna, OS Fabricante, OS Manual, CPF/CNPJ, Modelo, Tipo de Atendimento, Serial, IMEI, intervalo de datas** (com escolha do tipo de data), **Status, Tipo de Serviço, Seguro**. Botão **Buscar**.
Resultado em tabela: Nº, Entrada, OS/Fabricante, Atendimento, Status/Motivo, Cliente, Produto, Serial, Editar.

Valores das listas:
- **Tipo de data:** Entrada, Designado, Análise, Pronto, Aprovação, Entrega, Check List, Previsão, U Designado
- **Status da OS:** Reconhecimento, Técnico Designado, Pendente, Pronto, Produto Entregue, Cancelada, RMA, Scrap, Empréstimo, Alteração Peças, Sem alteração
- **Tipo de atendimento:** Aprovado Balcão, Fora da Garantia, Garantia Samsung, Pedido, Venda
- **Tipo de serviço:** Balcão, Correios, In Home, Instalação inicial, Reparo de estoque
- **Seguro:** Assurant, Cardif, Contigo, Luizaseg, Care +, SIS, Zurich

### 4.2 Criar Ordem de Serviço
Botão **Salvar** no topo. Seções, em ordem:
1. **Abrir OS COS para OS GSPN (CI)**: Último MOTP, Atendimento, Agendamento, ASC Job, OS GSPN, Produto ligando? (Não/Sim), Qless (1:30), opções "Hoje" e "Reconhecimento", botão **Buscar GSPN**.
2. **Abrir OS COS para OS GSPN (IH)** (in home): OS GSPN e Buscar GSPN.
3. **Informações Gerais do Atendimento**: Qless, OS RRR, OS/TA, OS Manual, Atendimento, Serviço, Seguro, OS de retorno.
4. **Informações do Produto**: Marca, Modelo, Serial, IMEI, data da compra, operadora e **condições do produto** (checkboxes como "Arranhado" e campo "Outros", com busca de imagem).
5. **Problema Reclamado** (inclui pergunta "Defeito?" Não/Sim).
6. **Informações do Cliente**: Buscar Cliente, Nome, CPF/CNPJ, endereço, bairro/cidade/UF, telefones, e-mail. Há um pop-up pedindo para o cliente **confirmar o celular**.
7. **Entrega do Produto**: cliente aprovou entrega?, tipo (Orçamento paga pelo cliente / Concierge sem custo), valor por cidade (Goiânia R$ 20, Aparecida R$ 25, Trindade R$ 30, Senador Canedo R$ 30), forma de pagamento (dinheiro/cartão) e observação (limite de 90 caracteres).

### 4.3 Rastreamento por Status
Filtros: Ano, Atendimento, Tipo de Serviço, Status, **Técnico** (lista de técnicos cadastrados), Linha (IM, CE), Posto (Núcleo Service, Via Digital, Contigo, Via Seguro…), Seguro e Revenda (varejistas como Fujioka, Eletro Imagem, Carrefour, Via Varejo…).

### 4.4 Produção por Técnico
Lista de análises feitas por técnico no período (hoje até 7 dias atrás).

---

## 5. Fluxo de uma OS (deduzido pelo menu e pelos status)

1. **Entrada**: cliente ou posto traz o aparelho. Verifica garantia por IMEI e cria a OS (vinculada à OS do GSPN quando garantia).
2. **Reconhecimento** e entrada na colmeia.
3. **Designar técnico** → *Técnico Designado*.
4. **Check list** → análise técnica.
5. **Orçamento**: inserir, aprovação do cliente, negociação (fora de garantia ou seguro).
6. **Peças**: se faltar peça, pedido (GSPN/fornecedor) e espera chegar. Controla estoque e movimentação.
7. **Reparo** → *Pronto*.
8. **Contato com o cliente** e **entrega** (balcão, entrega local ou correios). Pode haver emissão de NF.
9. **Produto entregue**. Desvios: *Cancelada*, *RMA*, *Scrap*, *Empréstimo* (Concierge).
10. **Pós-processo**: devolução de peças usadas/novas ao fabricante e remessas de pagamento.

---

## 6. Observações e pontos de atenção

- Parte das telas é antiga (JSP) e parte nova (`new/`, `front/`): comportamento e visual podem variar.
- Acesso por perfil: nem todo usuário vê todos os menus.
- A integração GSPN depende de OTP; se o status deixar de ser "Sucesso", telas de GSPN podem falhar.
- Esta documentação não cobre regras de negócio internas (cálculos, validações, permissões por perfil), pois só foi feita leitura das telas. Podem ser detalhadas em uma segunda rodada, tela por tela.
- Telas `new/...` e `front/...` (Orçamentos, Editar Serviço, Tag, Saída peças, Local, Contagem, Fornecedores, Perfis, Relatórios etc.) e as telas de Relatórios não foram detalhadas, pois são carregadas dinamicamente.
- Várias filas abrem vazias até o usuário filtrar ou buscar; as colunas dos resultados só aparecem com dados.

---

## 7. Detalhe por tela (campos e botões lidos nas páginas)

Convenção: **Filtros/campos** → botões. Listas "Atendimento" nas filas têm Todos / Garantia / Orçamento.

### 7.1 Ordem de Serviço — filas e consultas
| Tela | Filtros/campos | Botões / colunas |
|---|---|---|
| Entrada/Saída colmeia | Busca de OS | Buscar OS, Retirada. Tabela: No, Data, Usuário, OS, OS GSPN, Produto, Observação |
| Agenda | Atendimento, Técnico | Atualizar |
| Criar Ticket IQC | Serial, Defeito, Apresentou Defeito?, Solução, Observação, Anexos | Upload |
| Consultar Cliente | Datas de cadastro, CPF/CNPJ, Tipo (Final/Lojista…), ID Cliente, ID Fabricante, Nome, Sobrenome, telefones, e-mail | cadastro/edição de cliente |
| Anexos | Tipo (Entrada/Retirada), Atendimento, Datas | Buscar |
| Designar Técnico | Atendimento, Tipo de serviço | Buscar, Designar |
| OS Designada | Atendimento, Tipo, Motivo, Técnico | Filtrar. Colunas: No, Entrada, OS/Fabricante, Atendimento, Produto, Motivo, Tipo Serviço, **TAT (TTL)**, Técnico, Cliente, Status, Observação, Sintoma, Reparo, Orçamento, Valor |
| Ag. Check List | Atendimento, Tipo de serviço, Produto (IM/CE), Concierge | Filtrar |
| OS Ag. Aprovação | Nome, Tipo de serviço, Seguro, Atendimento | — |
| OS Ag. Negociação Orçamento | marca "Cliente vai retornar ligação" | — |
| OS Ag. Peças | Atendimento, Tipo de serviço, Pedido efetuado | Download, Filtrar |
| Prontos – Entrar em Contato | Tipo de atendimento | Resetar, Buscar |
| OS Enviar AR | Consultar GTI, Buscar OS | Buscar, Gerar GTI |
| Abrir OS Venda GSPN | Data inicial/final | Buscar |
| Histórico (geral) | Data inicial/final | Buscar |
| Cadastrar/Alterar Produto | Concierge (Sim/Não), Alertar (Sim/Não), Marca, Linha, Produto, Código Modelo | Novo, Buscar |
| Download Ordem Serviço | mesmos filtros de Buscar OS | Download |
| Buscar Peça Caixa / Buscar Peça no Estoque | ID Peça, Modelo, Estoque, Código Peça, Fornecedor, Nota Fiscal, Status Peça, Descrição, Armazém, Referência de Uso, Nº Pedido, Delivery | Buscar |
| Peças Solicitadas pelo Lab | Ocultas, Datas, Status | Buscar (e Download na versão de Pedidos) |
| OS Pendente Ação ASC | Atendimento, Tipo de serviço, Técnico, Status | Filtrar |
| Histórico IQC | ID, Serial, Datas | Buscar |
| SAW (AEG) | Nº SAW, Categoria, Status, ID, Nº OS. Tipos: Exceção de garantia, Uso excessivo de peças, Peça estética | Buscar |

### 7.2 Entrega, Garantia, Concierge
- **Agenda Entregas:** lista de entregas agendadas (Atualizar).
- **Auditoria de contato:** Cliente aprovou entrega?, Tipo da entrega, Valor (Goiânia R$20, Aparecida R$25, Trindade/Senador Canedo R$30), Cidade, Agendamento, Nome, Previsão de retirada.
- **Download Entregas:** períodos de criação e de conclusão → Download.
- **OS Criar Garantia:** Status (Entregue, Reparo Completo, RMA) → Buscar. **Relatório Garantias:** Status, Datas, OS.
- **Produtos de Empréstimo:** Motivo, Modelo, OS, Serial. **Empréstimos:** ID, Status, Datas, OS de Reparo, OS de Empréstimo. **OS Concierge Pendente:** Status.

### 7.3 Pedidos e GSPN
- **AR AP:** Tipo de documento, Status, Datas. **Histórico de Pedidos:** Status, "OS Ag. peças", Datas → Download, Buscar.
- **Comparar OS pendente com Estoque:** Atendimento, "Apenas em estoque" → Buscar, Download.
- **OS Ag. Pedir Peças:** botões Download peças pendentes, **Inserir Pedido**.
- **GSPN:** Buscar Delivery (código da peça, próximo mês); Buscar NF por modelo (modelo, datas, tipo de anexo: Nota Fiscal, Evidência de Serial, Ordem de Serviço, Outros); Balanço por Código Modelo (posto, OS fabricante, código modelo, versão); Buscar Dados RMA; Buscar Dados Garantia (nº da garantia); Abrir Link GTI (nº GTI); Buscar Dados por IMEI (IMEI, modelo, produção/país, IMEI 1/2/3, serial); Adicionar Peça na OS (posto, código, quantidade, OS fabricante); Criar Pedido Peça (botão Criar).

### 7.4 Estoque
- **Informações de Peças Cadastradas:** modelo, código modelo, código da peça, descrição, em estoque → Atualizar, Nova, Buscar.
- **Informações de Notas Fiscais:** NF, fornecedor, datas de entrega → *Verificar recebimento GSPN*, Buscar.
- **Alterar Estoque da Peça:** novo tipo de estoque → Salvar.
- **Transferir Peças de Armazém:** origem e destino → Salvar. **Histórico Transferência:** ID, origem, destino, datas.
- **Ajustar Estoque com Bal. GSPN** (próximo mês) e **Histórico Ajuste**.
- **Upload XML:** anexo, armazém, tipo de estoque → Enviar.
- **Upload Estoque GSPN:** botões Ajustar, Transferir Etq. Técnico, **Zerar Estoque GSPN**, Upload Todo Estoque COS para GSPN (ações sensíveis).
- **Inventário:** tipo de estoque, fornecedor, armazém.
- **Peças Mais Usadas por Período:** atendimento, mínimo, datas → Buscar, Transporte.
- **Remessa de Pagamento:** "Apenas usadas" → Gerar Lista Pagamento; histórico por ID e datas.
- **Remessa Devolução de Peças:** Gerar Lista Devolução; histórico por ID e datas.
- **Verificar disponibilidade MIX:** lista código, descrição, localização, quantidade.
- **Peças pendentes de análise**, **Peça/NF pendente de recebimento** (datas).

### 7.5 Devoluções
- **Peças novas:** Buscar peça para devolução (ID, estoque, armazém, código, fornecedor, NF, status); Devolver por ID (motivo da devolução → Verificar); Histórico (chave de acesso, nº solicitação, nº NF, volumes, status, datas); Atualizar Coletada em massa; Comparar NF devolvida com creditada (datas → Buscar, Download).
- **Peças usadas:** Confirmar Recebimento (datas, atendimento, serviço, status do reparo; colunas No, ID, Código, Descrição, Modelo, OS, Atendimento, Motivo, Data de uso, Ok); Local de armazenamento (Novo); Gerar Nova devolução (remessa GSPN → Buscar); Histórico (NF, volumes, ID, remessa, datas).

### 7.6 Administrar, Nota Fiscal, Posto Coleta
- **Editar Usuário / Editar Técnico:** cadastro com botão Novo.
- **Master OTP:** campo "Novo MOTP" → Inserir. **Medição Temp/Umidade:** Umidade e Temperatura → Inserir.
- **OS Ag. Emitir NF:** lista de OS esperando NF → Buscar.
- **Posto Coleta – Criar OS:** igual a Criar OS, com perguntas extras: Cliente possui NF?, data da compra, serial, 13º mês, valor, ASC Job, OS GSPN, Qless, produto ligando, "<> Hoje".

### 7.7 Pendências desta documentação
- "Comparar OS pend. com pç. entregue" (Gerenciamento de Pedidos): o nome do arquivo ficou truncado na leitura e não foi aberto.
- `new/...` e `front/...`: não detalhadas (item 6).
