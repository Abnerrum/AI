# Extensão do Chrome — Assistente Núcleo

A extensão abre uma conversa no painel lateral do Chrome e usa o Assistente Web que roda neste computador. O texto da aba atual só é lido quando você clica em **Incluir texto da aba atual**; esse contexto é limitado a 6.000 caracteres.

Clique em **🔇** para ouvir as próximas respostas em português usando a voz disponível no Chrome. O botão alterna entre ativar e silenciar; a síntese é feita pelo navegador, sem chamadas extras ao modelo e sem consumir tokens.

## Instalar no Chrome

1. Inicie o Assistente Web e mantenha o painel em execução.
2. No Chrome, abra `chrome://extensions` e ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação** e selecione a pasta `assistente-web\extensao_chrome`.
4. Fixe **Assistente Núcleo** na barra de ferramentas.
5. Clique no ícone da extensão. No painel lateral, clique em **Gerar código no painel**.
6. Entre no painel local, gere o código temporário e cole-o na extensão. O código expira em cinco minutos e só funciona uma vez.

O token de conexão fica no armazenamento local da extensão e seu hash fica no Cofre de Credenciais do Windows. Use **Desconectar extensão** para revogar o token.

## Limites e privacidade

- Funciona somente quando o Assistente Web está rodando neste computador.
- A extensão permite conversar, escolher o departamento, iniciar uma conversa e responder a pedidos de autorização.
- A leitura da página é iniciada manualmente e limitada a 6.000 caracteres. O texto é enviado ao assistente junto com a mensagem; não é coletado em segundo plano.
- Páginas internas do Chrome, extensões e algumas páginas protegidas não permitem leitura.
- A extensão não executa cliques ou preenchimentos por conta própria. O assistente pode usar as ferramentas de navegador existentes, sujeitas aos pedidos de autorização do painel.
