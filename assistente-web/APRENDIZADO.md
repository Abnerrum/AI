# Aprendizado

Memoria local com conhecimentos que o usuario ensinou. O painel consulta somente as secoes ligadas ao assunto; confirme com o usuario antes de registrar novos procedimentos.

## Usuario
- Contas a pagar do Grupo Nucleo Service. Fala portugues; prefere respostas curtas e passo a passo simples.
- Funcoes principais no COS: Estoque, Relatorios e Ordem de Servico.
- Ensina por prints (pasta Pictures\Screenshots) e por PDFs/XMLs em Downloads. Gosta que eu observe e depois replique.
- Se disser "fecha"/"para", nao fechar abas nem continuar sem confirmar qual. Ja reclamou de aba fechada sem pedir.

## Sites
- Conta Azul Pro: https://pro.contaazul.com/#/ca/visao-geral (empresa MATRIZ). Usuario ja fica logado no Chrome dele.
- COS (rede interna, COS CSP GOIANIA): http://192.168.25.131:8080/COS_CSO/Principal.jsp. Ja logado no Chrome.
- TomTickets Samsung BPO (Gi Group): https://samsungbpo.tomticket.com/helpdesk (novo chamado: /helpdesk/novo). Login e senha so o usuario.

- Cobli (frota): https://painel.cobli.co/home (app.cobli.co nao funciona). Skill de relatorio diario de frota: anthropic-skills:controle-frota-cobli.

## Como trabalhar
- Usar o Chrome do usuario (Claude in Chrome), que ja esta logado. Navegador separado (`assistente-web`) so se ele pedir ou para Excel/fluxos.
- Se a mensagem atual contiver URL, nao pedir o link de novo: navegar imediatamente para ele no Chrome. Nao reutilizar URL de conversa anterior. Erro 403 em busca HTTP nao prova que o navegador nao consegue acessar. Em dashboard Power BI/Looker, aguardar carregar e conferir graficos pela captura visual quando nao houver texto acessivel.
- Nunca pedir senha no chat. Confirmar antes de pagar, enviar, aprovar ou excluir.
- Nao observo a tela em tempo real: so vejo quando capturo. Para aprender um processo, o usuario escreve "proximo" a cada etapa ou manda prints.
- Login (clicar em Entrar) e do usuario, mesmo com senha preenchida pelo navegador. Nao digitar senha.
- Emitir nota fiscal e acao irreversivel: o classificador de permissoes bloqueia o clique ate o usuario autorizar de novo no prompt do Claude Code. Pedir confirmacao explicita antes.
- Upload de anexo (file_upload) so aceita pastas liberadas com `/add-dir`. Downloads nao esta liberada: o usuario anexa XML e PDF manualmente (ou roda `/add-dir C:\Users\Samsung\Downloads`).
- Nao clicar por coordenada em listas longas sem conferir; cliques errados ja marcaram pagamento por engano.
- Ao fechar abas, so as que eu criei e so quando pedido.

## COS (mapa do menu)
- Menu lateral em acordeao; clicar no grupo abre/fecha; telas abrem no frame da direita. JS direto na pagina e bloqueado, navegar por clique e captura.
- Grupos: Ordem de Servico, AEG, In Home, Entrega Produto, Garantia, Concierge, Gerenciamento de Pedidos, GSPN, Estoque, Devolucao Pecas Novas, Devolucao Pecas Usadas, Administrar, Relatorios, Nota Fiscal, Posto Coleta.
- Relatorios: Producao por Tecnico (analises hoje a 7 dias); Relatorio OS (aba Status COS<>GSPN; filtros data entrada, atendimento, tipo servico, "apenas diferenca na entrega"); Relatorio Estoque (abas Pecas estornadas, Status pagamento pecas, UPC pendente); Relatorio Orcamentos (abas Pagamentos/Orcamentos; Buscar e Download).
- Estoque: Local, Upload XML, Inserir Peca Manualmente, Inserir Localizacao Peca (tem Salvar), Informacoes de Pecas Cadastradas, Buscar Peca no Estoque, Informacoes de Notas Fiscais (botao Verificar recebimento GSPN), Alterar Estoque, Transferir Pecas de Armazem, Historico Transferencia/Ajuste, Comparar OS Pend. com Estoque, Ajustar com Bal. GSPN, NF/Peca Pendente de Recebimento, Upload Estoque GSPN, Inventario, Downloads de listas, Pecas Mais Usadas, Gerar Remessa Pagamento.
- Ordem de Servico: Buscar OS (OS interna/fabricante/manual, CPF/CNPJ, modelo, serial, IMEI, status, tipo servico, seguro, datas); Criar OS (Buscar GSPN CI/IH, dados do atendimento e produto, Salvar); filas por etapa: OS Designada, Ag. Check List, Ag. Inserir Orcamento, Ag. Aprovacao, Ag. Negociacao, Ag. Pecas, Prontos-Entrar em Contato.
- Outros grupos so mapeados pelo nome dos itens (GSPN, Devolucoes, Administrar, Garantia etc.), telas nao abertas.

## Fatura Clara (mensal, 1x por mes)
- Ler o CSV da Clara (Desktop), ignorar recusadas/estornos/negativos e itens ja lancados. Lancar cada compra no Conta Azul Pro > Financeiro > Contas a pagar clonando um lancamento da Clara (vencimento 15/10, conta "Clara - Cartao de Credito"), trocando so descricao, valor e categoria.
- Descricao = comentario do CSV; se vazio, nome da categoria Clara. So trocar categoria se diferente do modelo (Lanches e Refeicoes 2.04.02.06).
- Nao clicar em "Repetir lancamento" (manter desligado); escolher categoria por teclado. Nao clicar por coordenada na lista; usar JS para achar linha/Acoes e conferir descricao+valor+categoria antes de Salvar. Lotes de ate ~6 itens. Excluir lancamento e feito pelo usuario.
- Mapa categoria Clara -> Conta Azul: Almoco/Refeicao/Janta 2.04.02.06; Hospedagem 2.01.22.07; Combustivel 2.01.22.02; Software 2.02.03.07 (Conta Azul 2.02.03.09); Material OS/Ferramentas 2.04.09.02; Transporte 2.01.10.01; Marketing 2.01.02.08; Mat. Escritorio/TI 2.01.14.01; Cash Back 2.04.09.05; Manutencao Predial 2.04.03.05; Internet 2.01.11.03; Pedagio 2.01.22.04; Utensilios 2.04.11.02; Limpeza 2.01.21.01; Manut. equipamento 2.01.17.01.

## Notas de servico de garantia Samsung (3x por semana) - Conta Azul
- Entrada: PDF "Dados do fechamento de Garantia" (nome = codigo da ASC, ex.: 4885160.pdf) com Data de Fechamento, Codigo do autorizado (ASC), Documento Numero, mao de obra/frete/impostos/outros, "Total a receber (Valor para Emissao de NF)" e pecas em garantia (fora da nota).
- Empresas (troca de conta pelo menu superior direito; o usuario ja trocou, eu nao achei o botao): Nucleo Service ASC 2446971 (Goiania, CC 4430-X); TXM Vitoria ASC 3192793 (CC 4428-8); AXT Anapolis ASC 3178021 (CC 4435-0); AXT Buriti ASC 4885160; AXT Goiania ASC 3178766 (CC 4411-3). Contas BB AG. 8087-X.
- Troca de empresa no Conta Azul: o menu da conta (canto superior direito) NAO tem seletor de empresa; so mostra a empresa ativa (ex.: "FILIAL - AXT GOIANIA LTDA"), Conta PJ, Perfil, Termos, Sair. Em 15/10/2026 o usuario trocou FILIAL -> MATRIZ saindo e entrando de novo (tela login.contaazul.com com e-mail/senha preenchidos pelo navegador); o clique em Entrar e do usuario. Vi so a tela de login e o resultado (cabecalho "MATRIZ -"), nao os cliques. Pedir ao usuario para trocar e avisar.
- Para achar notas por tipo no CA (TXM): Servicos > Vendas de servicos > Mais filtros > Centro de custo (lista com "Mostrar mais"). Centros: STORE + (notas Store+, Samsung), SEGUROS e SEGUROS FRANQUIA (Assurant), GARANTIA SAMSUNG, P4P, GD TA, INCENTIVO-SAMSUNG, SMB, SAMSUNG CONTIGO, TAXA DE ANALISE, APORTE SAMSUNG, STATUS 80, ECO-TRADE, SAW - DESCONTO FG, PROGRAMA NA PAREDE, VENDA-ACESSORIOS, VENDA-OUTLET, AGIS - COMISSAO DE VENDA e centros de balcao/inhome. Outubro/2026 TXM: Store+ = NF 390 (R$ 33.950,76) e 391 (R$ 11.229,40); Assurant = 6 vendas, R$ 6.090,01 (NF 395, 396, 398, 399, 400, 401; NF 394 cancelada).
- Centro de custo da obra: Nucleo/TXM/Anapolis C8201245; Buriti C820124.
- Passo a passo: Servicos > Vendas de servicos > Mais filtros > Centro de custo > digitar "gara" > marcar GARANTIA SAMSUNG > Aplicar > na venda mais recente da mesma empresa, Acoes > Clonar.
- No clone trocar so: Numero da venda = Documento Numero do PDF; valor unitario/Total = Total a receber (o valor a receber da parcela atualiza sozinho ao sair do campo com Tab); nas Observacoes complementares da nota fiscal, a data de fechamento e o "Documento numero". ASC, municipio, dados bancarios e centro de custo ficam como no clone. Data da venda, vencimento e vendedor vem do clone.
- Salvar (canto inferior direito) > Detalhes da venda > botao "Nota fiscal" > "Emitir nota fiscal" > previa "Nota Fiscal de Servico" > "Emitir Nota Fiscal". Fica "Nota Fiscal em espera" (fila do municipio) e depois "Emitida com sucesso"; conferir em Servicos > Notas fiscais de servico.
- Em Notas fiscais de servico, Acoes da nota: Visualizar NFS-e, Abrir a venda, Download DANFSE (escolher "Espelho da nota" = PDF RPS-xxx), Download XML (XML_NNN_serie.xml), Cancelar nota (irreversivel, nunca clicar sem pedido).
- Resultados de 15/10/2026: Nucleo NFS-e 444 (doc 3519416, R$ 30.348,86), TXM NFS-e 404 (doc 3511252, R$ 22.274,77), Anapolis NFS-e 804 (doc 3519537, R$ 120,52) emitidas. Buriti NFS-e 374 (doc 3519975, R$ 80,23) FALHOU: prefeitura rejeitou por regime especial de tributacao/aliquota e grupo IBS/CBS (cadastro fiscal); nao reemitir sem o usuario/contador acertar.
- Aviso de "Cliente inadimplente" aparece no clone da Anapolis; ignorado, nao afeta a emissao.

## TomTickets (chamado por nota emitida)
- Instrucoes completas: C:\Users\Samsung\Downloads\INSTRUCOES_TOMTICKET_SAMSUNG.md (modelos de mensagem por empresa e tipos de NF: garantia, incentivo P4P/GD TA, Store+).
- Chamado de garantia: Departamento Payment BPO (101916), Tipo "Pagamento de Mao-de-obra de Servicos" (173097). Campos: Numero do Documento, Valor, Vencimento (dd/mm/aa), Vendor/Partner Number (ASC), Assunto (= 1a linha da mensagem), Mensagem, Cc, anexos XML + PDF.
- Copia fixa: lidiane@gruponucleoservice.com.br, rh.financeiro@gruponucleoservice.com.br, nfservico@samsung.com.
- Vencimento: regra do arquivo (fechamento ate dia 15 -> dia 25) mas o usuario definiu 10/11/26 em 15/10 porque a nota foi emitida depois do dia 15. Perguntar/aplicar 10/11 nesses casos.
- Mensagem Anapolis: "NF {N} Fechamento garantia do dia dd/mm/aaaa / Codigo da ASC / Documento numero / Municipio: Anapolis / Dados bancarios / Centro de custo de mao de obra". Nucleo: "NF {N} Prestacao de servico de Garantia Fechamento ...". TXM: "NF {N} Referente ao fechamento do dia ...".
- Preencher via JS no formulario: codproduto, codtipoassunto, campodinamico[62119]=doc, [86089]=valor (virgula), [31071]=vencimento, [33651]=vendor, titulo, mensagem, copia (selectize). Esperar ~3s apos escolher departamento e tipo.
- Regras: nunca clicar em "Criar Chamado" sem o usuario escrever "criar"; se cair a tela de login, parar e pedir para logar; depois de criar, informar o protocolo.
- Criados em 15/10/2026 (pelo usuario, com anexos): Nucleo NF 444 #314873; TXM Vitoria NF 404 #314877. Anapolis NF 804 #314880 (criado em 15/10/2026 11:56). Nada pendente de garantia; Buriti NF 374 falhou na prefeitura.

## Skills salvas (.claude/skills)
- lancar-fatura-clara, emitir-nota-garantia-samsung, chamado-tomticket-garantia, relatorio-notas-tomticket. Usuario pediu salvar tudo como skill automaticamente: ao aprender uma rotina nova, criar/atualizar a skill sem perguntar.
- "Puxar notas de DD/MM a DD/MM" = ler os chamados do TomTickets (fechados via /helpdesk/arquivo?p=N) e gerar Excel; nao e o Conta Azul. Feito em 15/10/2026 (16/09 a 14/10): Downloads\notas_tomticket_16-09_a_14-10.xlsx.

## Cobli (mapa da plataforma, estudado em 15/10/2026, so leitura)
- Painel React lento: depois de navegar esperar ~4-6s antes de get_page_text; graficos/dashboards (Seguranca visao geral, Produtividade) nao vem como texto, usar screenshot. Listas (Checklists, Veiculos, Motoristas) vem bem em texto.
- Menu lateral (icones): Cobli IA (/ai), Inicio (/home), Operacao, Seguranca, Eficiencia, Relatorios (/report/home), Minha Frota, Integracoes (/apps), Configuracoes (/config/fleet). Filtro de grupos e busca (Ctrl+K) no topo.
- Operacao: Monitoramento (/monitoring, mapa + lista de veiculos ligados/velocidade/motorista), Alertas, Locais de interesse, Trajetos (/tracking-history), Historico de passagens, Servicos e entregas, Comprovantes, Checklists, Associacao de treinamentos.
- Seguranca: Visao geral (nota de conducao), Eventos de video, Videos solicitados (/camera/requests), Rec. facial (/camera/images), Saude das cameras, Ranking de conducao, Velocidade, Tratativas.
- Eficiencia: Produtividade (/productivity/dashboard; por veiculo/grupo/geral), Despesas, Combustivel, Manutencao, Multas.
- Relatorios (/report/home): Eventos de seguranca, Trajetos e paradas (resumo/diario/detalhes), Associacao motorista-veiculo, Associacao veiculo-dispositivo, Atividade em locais de interesse, Motor ocioso, Distancia percorrida, Atividade fora do horario de trabalho, Ponto a ponto (a cada 2 min), Uso de chaveiros sem identificacao. Para o relatorio diario de frota (uso apos 19h, pernoite) usar "Atividade fora do horario" e "Atividade em locais de interesse".
- Minha Frota: Veiculos (/vehicles), Grupos de veiculos, Dispositivos, Motoristas (/driver-management), Situacao operacional, Pedidos. Integracoes: Integracoes, Customizacoes, Chaves de API, Webhooks.
- Checklists (/checklist/responses): filtros periodo, conformidade, checklist, veiculos, motoristas. Unico checklist: "Checklist do VEICULO - CSP GOIANIA". 40 respostas de 08 a 15/10, todas marcadas "Sem conformidade" e 2 "Aguardando foto" (Scudo TFY9F33): conferir o que a coluna significa antes de reportar.
- Frota: 24 veiculos cadastrados, 12 associados (todos com camera) e 12 desassociados sem Cobli. Grupos GOIANIA e "86 - OW". Aviso: 2 veiculos sem velocidade maxima configurada (nao geram alerta de excesso). Motoristas: 25, so 52% (13) com reconhecimento facial completo, 11 rostos aguardando identificacao, cobertura de identificacao de video 84,46% em 30 dias.
- Relatorio "veiculos sem checklist": cruzar Checklists (/checklist/responses?startDate=2026-10-01T00%3A00%3A00-03%3A00&endDate=...&size=200, filtro aceita datas na URL) com viagens do dia (/path-association?startDate=...&endDate=... mesmo dia; "N/M" = viagens associadas/total; total>0 = rodou). Ler com JS esperando a tabela carregar. Script: gerar_checklist_cobli.py; saida Downloads\cobli_sem_checklist_outubro.xlsx (01 a 15/10/2026: 31 ocorrencias; piores TEX0E24 7 dias, TEW0F15 6, TEX0E56 5, TEU2C47 5). TEU2D25 nunca rodou; TFY9F33 nao rodou em 14 e 15/10.
- CONTROLE DE FROTA (relatorio diario Word): regras completas do usuario em controle_frota_cobli.md (raiz do projeto): quem e responsavel por cada veiculo, justificativas, oficina (TEU2D25 e TFY9F33 fora das contagens), formato fim de semana/feriado. Ler antes de qualquer relatorio de frota; ao fechar o dia, atualizar esse arquivo. O responsavel vem do checklist, mas os "responsaveis fixos" prevalecem (TEU2C47 e TXI5B84 = Reyner; TEW0F14 = Jovenildo; TEW0F15, TEX0E56 = Gero; etc.).
- Relatorio Word de frota do dia: dados em Cobli > Relatorios > Trajetos e paradas > Detalhes (/report/trip-and-stop/details?startDate=...&endDate=...&size=500); tabela virtualizada: rolar o container e coletar linhas em JS (193 eventos de 14 a 15/10). Colunas: veiculo, motorista (Cobli, pode divergir das regras), partida/parada, duracao, distancia. Coordenadas ficam atras do botao "Ver local" (nao saem em texto). Gerador: gerar_frota_docx.py (docx escrito a mao, sem python-docx); modelo = Controle_Frota_Cobli_2026-10-14 do usuario (secoes: Resumo, 1 uso apos 19h, 2 pernoite, 3 regulares/oficina, 4 checklist, 5 km, 6 pontos de atencao). Primeira versao (_refeito.docx, estilo simples) foi apagada a pedido; vale a versao _modelo.docx (km so de trajetos iniciados no dia; o do usuario somava tambem retornos da manha seguinte).
- O usuario enviou a receita que gera o relatorio Word de frota: clona elementos de um modelo (tpl.docx = relatorio anterior) com python-docx para manter o estilo. Salva em gerar_frota_template_modelo.py. python-docx nao esta no venv; meu gerar_frota_docx.py faz o docx do zero (estilo simples). Ideal: instalar python-docx no venv (com ok do usuario) e usar o relatorio anterior como modelo.
- python-docx instalado no venv (15/10/2026, com ok do usuario). Gerador com modelo: gerar_frota_com_modelo.py modelo.docx saida.docx (indices do relatorio 14/10 do usuario no topo do script; a receita original usa outros indices, o modelo mudou). Saida: Downloads\Controle_Frota_Cobli_2026-10-14_modelo.docx. Para um relatorio novo, copiar esse script e trocar o conteudo.
- DEFINICAO DE "BASE" na frota (usuario, 15/10/2026): base = so o GSPN ou a Via 86 (Rua 86). Qualquer outro local nao e base (mesmo "Base Principal"/"Base de Pernoite" do Cobli): vira pernoite fora dos pateios. Ver controle_frota_cobli.md. Raio maximo 200 m do GSPN/Via 86; alem disso nao dormiu na base (precisa das coordenadas dos dois pontos).
- Para saber onde um carro parou: botao "Ver local" na tabela Trajetos e paradas detalhado abre o endereco da parada (le por JS). Foi assim que se corrigiu o relatorio de 14/10 (Montes Belos e Aparecida, nao Ipora/Anapolis). Detalhes em controle_frota_cobli.md. Versao atual do relatorio: Controle_Frota_Cobli_2026-10-14_modelo_corrigido.docx.
- Dois Chrome conectados (Browser 1 e 2): o Cobli logado do usuario estava no outro; usar switch_browser e o usuario clica Conectar. Escolher o navegador errado deixa o Cobli na tela de login.
- Nunca nomear motorista por foto/rosto (regra minha); usar so a associacao que o Cobli ja fez. Identificar motoristas (Associacao de Trechos) altera cadastro: so o usuario.
- Nao mexer em nada (usuario pediu so estudar). Cobli IA (/ai) existe e responde perguntas sobre a frota; nao usei ainda.

## Onde guardar os arquivos gerados (pedido do usuario, 15/10/2026)
- As mesmas pastas Cobli e Financeiro tambem existem na Area de Trabalho (usuario pediu em 15/10/2026): copiar os arquivos novos nas duas.
- Pastas por area dentro de Downloads: `Downloads\Cobli` (relatorios de frota, checklists) e `Downloads\Financeiro` (notas, planilhas de notas/TomTickets). Copiar os arquivos novos para a pasta certa (nao mover os originais do usuario). Criar outras pastas por area se aparecer.

## Ambiente
- Projeto em C:\Users\Samsung\Documents\IA\assistente-web; abrir pelo INICIAR.bat, opcao 2 (abre o Claude com --chrome).
- Python 3.13 instalado; o venv fica dentro de assistente-web.
- Na janela preta do Claude: colar texto/link com botao direito do mouse; imagem com Alt+V ou arrastando o arquivo.
- Painel web (painel.py): INICIAR opcao 5 (neste PC, http://localhost:5050) ou 6 (link https pelo celular, muda a cada abertura). Texto, audio (transcrito no PC), fotos/prints (colar, arrastar, anexar). Autorizacoes aparecem na pagina com Permitir/Negar. Senha do painel no cofre do Windows; conversa em painel_dados/, anexos em anexos/.
- Remote Control oficial do Claude esta bloqueado pela organizacao (plano Team); precisa do admin liberar.
- Arquivos de trabalho ficam em C:\Users\Samsung\Downloads (PDFs de fechamento, XML/PDF das notas). Prints em C:\Users\Samsung\Pictures\Screenshots.
