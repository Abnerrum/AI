# AQUILIX AI — painel web

Automacao local em Python com comandos JSON copiados do **site do ChatGPT**, sem API. O ChatGPT nao acessa o computador automaticamente e nao existe interpretacao livre de linguagem natural no programa: ele executa as acoes JSON documentadas.

## Painel público na nuvem

A versão em `painel_web/nuvem` permite escolher um departamento, experimentar tarefas fictícias e montar prompts para usar no Claude ou no ChatGPT. A geração acontece no navegador. O painel público usa apenas os arquivos listados no build abaixo e funciona com o notebook desligado.

No Render, crie um **Static Site** usando este repositório. Deixe o diretório raiz vazio, use `dist` como diretório de publicação e configure este comando de build:

```sh
mkdir -p dist/estatico &&
cp assistente-web/painel_web/nuvem/{index.html,nuvem.css,nuvem.js} dist/ &&
cp assistente-web/painel_web/estatico/{aquilix-logo.png,icone.svg,painel.css} dist/estatico/
```

## Iniciar no Windows

1. Instale Python **3.11 a 3.13** e marque Add Python to PATH.
2. Extraia o ZIP e abra a pasta assistente-web.
3. Execute **INICIAR.bat**. A primeira execucao instala dependencias e Chromium.
4. Para testar o sistema demonstrativo, abra tambem **DEMO.bat**.
5. Cole os comandos de EXEMPLOS_JSON.md no terminal do assistente.

Nao copie ambientes venv de outro computador. O instalador cria um ambiente novo dentro da pasta do projeto. Nenhuma chave de API e necessaria.

O painel web usa React. O pacote inclui o build de producao; Node.js e npm nao sao necessarios para iniciar o aplicativo. Para alterar a interface, instale Node.js 20.19 ou superior e execute `npm ci` e `npm run build` na pasta `assistente-web`.

O painel pode ser acessado pela internet com a opcao de tunel HTTPS do INICIAR.bat; configure uma senha forte no proprio PC antes de compartilhar o link. O cookie de sessao recebe `Secure` quando o tunel inicia. O recurso **Aquilix Voz** entende comandos em portugues e ingles, salva notas por departamento e reutiliza a gravacao/transcricao e a leitura em voz alta existentes. Abrir sites, pesquisar no navegador, tocar musica, capturar a tela e controlar energia sao recursos locais e nao podem ser acionados pelo tunel; desligar ou reiniciar exige confirmacao e agenda a acao para 60 segundos depois. O acesso remoto continua protegido pelo login do painel.

O ZIP "Jarvis Desktop Voice Assistant" foi consultado como referencia. A implementacao adaptada nao extrai nem executa o codigo original; a atribuicao e a licenca MIT fornecidas no ZIP estao em [Jarvis/LICENSE](Jarvis/LICENSE).

Para trocar a senha do painel, abra `http://localhost:5050/alterar-senha` neste computador. A nova senha e exigida com pelo menos 12 caracteres e deve incluir `1507`; ela e gravada como hash no cofre do Windows. A troca invalida as sessoes existentes. Nunca altere nem compartilhe a senha pelo link publico.

## ChatGPT

Cole a instrucao de PROMPT_CHATGPT.md no ChatGPT. Descreva a tarefa, copie o JSON produzido e cole no assistente. O programa mostra resultado e resumo compacto. Confira o comando antes de executar. Nao envie senhas, cookies ou documentos financeiros completos ao chat.

Cole JSON em uma unica linha. Para login, use fazer_login (janela local de senha) ou faca no navegador visivel e pressione ENTER no terminal. Isso inclui verificacoes em duas etapas feitas manualmente.

## Outro computador

1. Neste PC, clique em **EMPACOTAR.bat**. Ele cria `assistente-web.zip` sem venv, sessoes, banco e relatorios (cookies e dados nao vao junto).
2. No outro PC, extraia o ZIP e clique em **INICIAR.bat**. Se faltar Python ou Claude Code, ele oferece instalar.
3. Escolha no menu:
   - **1 Claude Desktop**: funciona no plano **gratis** (dentro do limite de mensagens dele) e no pago. Instale o app em https://claude.ai/download e entre com a conta da pessoa.
   - **2 Claude Code**: so plano pago (Pro ou superior). Abre com o Sonnet por padrao; no painel, o administrador pode ativar **Economia** para usar Haiku e respostas mais curtas.
   - **3 Copiar e colar**: claude.ai ou ChatGPT gratis, sem app.
4. Cada pessoa entra com a propria conta Claude. As senhas dos sites ficam no cofre do Windows daquele PC; na primeira vez a janela de login pede de novo.

Para gastar menos: pecas diretas, conversa nova para cada tarefa, e salve tarefas repetidas como fluxo (depois so "executa o fluxo X").

## Link temporario ou endereco estavel

- A opcao **6 - Gerar link para compartilhar o painel** cria um link rapido temporario, copia-o para a area de transferencia e o mostra no terminal. Cole o link para compartilhar; ele muda quando o tunel e recriado e nao tem prazo de validade garantido.
- Para reutilizar um endereco estavel, registre um dominio, configure-o na sua conta Cloudflare e escolha **7 - Link estavel com dominio Cloudflare**. Na primeira configuracao, o Cloudflare abre a autorizacao da conta e cria um tunel nomeado e um DNS para o dominio. Nas proximas vezes, o programa reutiliza o mesmo hostname.
- Esse endereco estavel ainda encaminha para o painel e Claude executados neste computador. Mantenha o PC ligado, sem suspensao, e deixe aberta a janela da opcao 7; fechar a janela encerra o acesso. Para funcionar com o PC desligado, e necessario migrar a execucao do Claude e os dados para uma hospedagem.
- No proprio computador, o painel abre sem pedir senha. Acessos pela rede ou internet continuam exigindo senha; configure-a no primeiro acesso local em `/primeiro-acesso`. Compartilhe o endereco apenas com pessoas autorizadas. Nao envie senhas do painel pelo mesmo canal publico do link.

## Claude (sem copiar e colar)

No INICIAR.bat escolha **1** (Desktop) ou **2** (Code). Ele registra o servidor `servidor_mcp.py` no Claude Code (todas as pastas) e abre o Claude. Tambem funciona no Claude do VS Code numa conversa nova. Peca em portugues, por exemplo: "abre o navegador em http://localhost:5000, eu faco login, depois extrai as ordens e gera um Excel".

- No painel, selecione um dos seis agentes: **RH, Frotas, Financeiro, Operacional, Administrativo ou Estudos**. Cada agente tem conversa, sessao e memoria isoladas, pode receber texto, imagens e documentos e pode trabalhar em paralelo com outro agente. Sao perfis especializados do mesmo modelo, nao seis modelos treinados. RH pode usar uma conta Claude Code separada; os demais agentes continuam usando a conta principal configurada neste computador.
- **Historico de conversas** na barra lateral mostra conversas arquivadas do departamento selecionado. Clique em uma para consultar as mensagens e anexos em modo de leitura; use **Voltar a conversa atual** para continuar. O historico fica salvo localmente no computador do servidor e separado por departamento. Conversas antigas feitas fora deste painel nao sao importadas automaticamente.
- **Estudos** e voltado ao curso de Inteligencia Artificial do SENAI FATESG: analisa enunciados e anexos, explica o raciocinio e prepara rascunhos de atividades e projetos quando solicitado. Revise o conteudo e faca pessoalmente o envio final conforme as regras da faculdade.
- O administrador pode criar um login separado em **Configurar acesso RH**. A conta do RH entra pelo link **Acesso exclusivo do RH** na tela de login, acessa somente o agente de Recursos Humanos e nao pode trocar para outros departamentos. O login fica no cofre do Windows deste computador e a senha e guardada apenas como hash com salt; redefina-a pelo painel administrador.
- Para vincular o Claude do RH, o administrador abre **Conta Claude RH** e inicia o login oficial de `selecao@gruponucleoservice.com.br`. A autenticacao abre em uma nova janela neste computador e deve ser concluida no site oficial da Anthropic; nao digite a senha Claude no painel. A configuracao de autenticacao e isolada da conta Claude principal. O uso requer um plano Claude Code/Claude compativel para essa conta e usa a cota/faturamento dela.
- Marque **Ensinar ou corrigir um processo** ao demonstrar uma rotina. Quando voce pedir para ensinar ou guardar, o agente registra os passos diretamente na memoria do departamento, sem pedir uma segunda autorizacao. Em **Conhecimentos**, consulte/edite a memoria ativa. Novas memorias ficam em `painel_dados/agentes/<departamento>/`; conhecimentos existentes em `APRENDIZADO.md` sao copiados para os departamentos relacionados na primeira utilizacao.
- Frotas, Financeiro, Operacional e Administrativo podem usar trechos relevantes das conversas anteriores arquivadas do proprio departamento como referencia, sem enviar o historico inteiro. O pedido atual autoriza as ferramentas e etapas necessarias para executa-lo, sem confirmacoes repetidas. O agente nao deve extrapolar o pedido; so pergunta quando falta informacao essencial ou ha ambiguidade. Conversas antigas nunca valem como autorizacao atual. RH permanece fora deste modo.
- Ao pedir um relatorio web ou dashboard como Power BI, esses quatro agentes usam somente arquivos enviados ou fontes indicadas pelo usuario e geram o arquivo solicitado sem pedir autorizacao outra vez. Se faltarem fonte, periodo ou dados essenciais, perguntam somente o que falta. O relatorio fica em `relatorios/<departamento>/`, sem bibliotecas ou conexoes externas. Use **Compartilhar** ao lado do link do relatorio para criar um link publico somente de leitura; qualquer pessoa com o link podera ver aquele relatorio. O link permanece ativo ate ser revogado em **Links publicos**, onde tambem e possivel copia-lo novamente. O relatorio continua servido sem cache e em contexto isolado do navegador; o compartilhamento nao publica no servico Power BI. Para abrir fora da rede local, inicie antes a opcao **6** (link temporario) ou **7** (dominio Cloudflare); o computador e o tunel precisam permanecer ligados.
- O pedido atual e a autorizacao para executar exatamente o que voce pediu e as etapas necessarias; o painel nao pede permissao ferramenta por ferramenta. Para pagar, enviar, aprovar, excluir ou outra acao de impacto, diga claramente a acao e o alvo; o agente nao deve fazer nada alem do pedido. Se faltar um detalhe essencial, pergunta apenas esse detalhe. Para atividades de Estudos, o envio final continua sendo feito pessoalmente por voce.
- Login automatico: na primeira vez em cada site abre uma janela no PC pedindo usuario e senha; fica no Gerenciador de Credenciais do Windows (nem o Claude nem arquivos do projeto veem a senha). Para trocar, peca "esquece o login do site X".
- Codigo de verificacao (2FA) voce digita no navegador e avisa no chat.
- Para ouvir as respostas no painel, clique no botao **🔇** para ativar a voz. A leitura usa a voz em portugues disponivel no navegador e pode ser desligada pelo mesmo botao; nao faz chamadas extras ao modelo nem consome tokens.
- O Claude tambem clica, digita, escolhe opcoes, le a pagina e lista botoes/campos, sempre devolvendo pouco texto.
- Tabelas ficam no computador; o Claude recebe so total, colunas e 3 linhas.
- Envio de formulario usa a ferramenta `submeter_formulario`: envia sem confirmacao repetida somente se o pedido atual solicitar claramente o envio e o alvo/conteudo estiver definido; se voce pediu apenas para preparar ou preencher, nao envia.
- Fluxos com envio dentro sao cancelados no modo Claude; envie pela ferramenta propria.
- No painel, **Conhecimentos** abre a memoria local `APRENDIZADO.md`, que voce pode consultar e editar. So as secoes relacionadas a pergunta sao enviadas, e Claude pede confirmacao antes de guardar um novo procedimento; isso evita repetir instrucoes e mandar o arquivo inteiro em toda conversa.
- O painel limita inicialmente o uso a **150 mensagens por dia**, com contador salvo localmente e reiniciado a cada dia. Ao atingir o teto, use **Destravar** para liberar mensagens sem esse limite; **Ativar trava** volta a limitar. O contador mede mensagens, nao creditos exatos, e nao controla o uso feito fora do painel.
- **Economia** no painel alterna o modelo entre Sonnet (padrao) e Haiku e orienta respostas mais diretas. A preferencia fica salva neste computador. O efeito sobre limites ou creditos depende do plano e das regras da conta Claude; nao recupera cota ja consumida. A extensao do Chrome continua usando o Sonnet configurado.

## Extensao do Chrome

O menu do `INICIAR.bat`, opcao **8**, abre `chrome://extensions` e a pasta da extensao. Ative o modo de desenvolvedor e carregue a pasta `extensao_chrome`. Com o painel local em execucao, abra a extensao, gere um codigo no painel e cole-o para vincular. O codigo vale cinco minutos e so pode ser usado uma vez; o token e guardado no Cofre de Credenciais do Windows e pode ser revogado na extensao.

A extensao adiciona um chat lateral aos seis agentes. A leitura da aba atual e opcional, iniciada pelo usuario e limitada a 6.000 caracteres. O texto da pagina e enviado somente junto com a mensagem em que foi solicitado; a extensao nao observa abas em segundo plano. O botao **🔇** ativa a leitura das respostas pela voz do navegador, sem chamadas extras ao modelo ou tokens. Para instrucoes adicionais, consulte `extensao_chrome/LEIA.md`.

Para reduzir o uso de tokens, respostas sao orientadas a serem concisas e a extensao nao anexa a pagina automaticamente. A extensao continua usando Sonnet; a opcao de modelo Haiku existe somente no painel web.

## Relatorio sem reenviar os dados

Apos extrair a tabela, os registros ficam na memoria, separados por usuario. Gere o Excel assim:

```json
{"acao":"gerar_excel","usuario":"abner","params":{"nome_arquivo":"relatorio.xlsx"}}
```

Os arquivos sao salvos em relatorios/abner. Ao encerrar, os dados em memoria sao descartados. Uma nova extracao que falha invalida os dados anteriores, evitando exportar uma consulta antiga por engano.

## Lancamentos

Preencha primeiro com preencher_formulario. O envio exige chave_unica e texto_sucesso ou seletor_sucesso, verifica a previa e pede confirmacao no terminal, inclusive dentro de fluxos. O indicador de sucesso deve ser especifico e ausente antes do envio.

A chave fica registrada como incerta antes de enviar. So e marcada concluida apos verificar sucesso. Se a confirmacao falhar, consulte o site antes de reenviar. O programa nao faz retry automatico e nao fornece reconciliacao automatica de resultados incertos.

## Limites e privacidade

- **Clara ainda nao integrada**: e preciso configurar e testar URLs, seletores, filtros, campos e indicador de sucesso do sistema real. Nao foram feitos lancamentos na Clara.
- O controle de duplicidade local depende de uma chave unica consistente; nao substitui a verificacao do registro no site.
- Extracao suporta tabelas HTML convencionais. Tabelas virtualizadas, iframes e interfaces especiais precisam de adaptacao.
- Sessoes do navegador contem cookies locais; proteja a pasta sessoes. Historico guarda metadados, sem valores dos formularios.
- Fluxos sao compartilhados no programa local. Separacao de sessoes nao e autenticacao multiusuario; use contas Windows separadas em computadores compartilhados.
- O site demo tem dados simulados em memoria e credenciais admin/1234. Use somente para testes locais.

## Verificacao realizada

11 testes de regressao e teste real de navegador contra o demo: login, 67 registros em 7 paginas, Excel e envio com verificacao. Windows .bat foi revisado, mas nao executado neste ambiente Linux. Clara e acesso ao site do ChatGPT nao foram testados.

Para repetir: instale pytest separadamente (`python -m pip install pytest`) e execute `python -m pytest -q`. O teste `python tests/verificar_demo.py` inicia seu proprio servidor local na porta 5000; feche DEMO.bat antes.
