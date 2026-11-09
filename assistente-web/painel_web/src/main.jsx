import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';

const ICONES = {
  editar: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></>,
  livro: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></>,
  compartilhar: <><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><path d="m8.6 13.5 6.8 4m0-11-6.8 3.5" /></>,
  calendario: <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>,
  usuario: <><circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" /></>,
  cartao: <><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></>,
  sair: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5m5 5H9" /></>,
  menu: <><path d="M3 6h18M3 12h18M3 18h18" /></>,
  clipe: <path d="m21 12.5-8.5 8.5a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.8 1.8 0 0 1-2.6-2.6l8.3-8.3" />,
  microfone: <><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0m-7 7v3" /></>,
  enviar: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  parar: <rect x="7" y="7" width="10" height="10" rx="2" />,
  estrela: <><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /><path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14Z" /></>,
};

function Icon({ nome, preenchido = false }) {
  return (
    <svg viewBox="0 0 24 24" fill={preenchido ? 'currentColor' : 'none'} stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICONES[nome]}
    </svg>
  );
}

function BarraLateral({ aberta, onNavegar }) {
  return (
    <nav className={`sidebar${aberta ? ' aberta' : ''}`} id="sidebar" aria-label="Navegação principal" onClick={onNavegar}>
      <div className="sidebar-topo">
        <a className="marca" href="/" aria-label="Aquilix AI, início">
          <span className="marca-icone"><img src="/estatico/aquilix-logo.png" alt="" className="aquilix-logo" /></span>
          <span className="marca-nome">AQUILIX <span>AI</span></span>
        </a>
        <button className="icone-sidebar" id="nova" type="button" title="Nova conversa" aria-label="Nova conversa">
          <Icon nome="editar" />
        </button>
      </div>

      <div className="sidebar-agente">
        <label className="seletor-agente" htmlFor="agente">
          <span>Seu espaço</span>
          <select id="agente" aria-label="Escolher agente por departamento" />
        </label>
        <span className="agente-descricao" id="agente-descricao">Seu assistente especializado</span>
        <span className="perfil-acesso" id="perfil-acesso" hidden />
      </div>

      <div className="sidebar-nav">
        <div className="uso-grupo">
          <span className="indicador-online" aria-hidden="true" />
          <span className="uso-claude" id="uso-claude" title="Limite diário de mensagens; o consumo de créditos depende do tamanho das conversas." />
          <button className="botao-trava" id="trava-claude" type="button" aria-label="Alterar limite diário" />
        </div>
        <button className="botao-economia" id="modo-economico" type="button" aria-pressed="false" title="Usar Claude Haiku e respostas mais curtas">
          Economia: desativada
        </button>
        <button className="nav-item historico-toggle" id="historico-toggle" type="button" aria-expanded="false">
          <Icon nome="livro" />Histórico de conversas
        </button>
        <div className="lista-historico" id="lista-historico" hidden />
        <span className="nav-legenda">FERRAMENTAS</span>
        <button className="nav-item" id="conhecimentos" type="button"><Icon nome="livro" />Conhecimentos</button>
        <button className="nav-item" id="compartilhamentos" type="button"><Icon nome="compartilhar" />Links públicos</button>
        <button className="nav-item" id="agenda" type="button"><Icon nome="calendario" />Agenda automática</button>
        <button className="nav-item nav-jarvis" id="jarvis" type="button"><Icon nome="estrela" />Aquilix Voz</button>
        <span className="nav-legenda nav-legenda-admin">ADMINISTRAÇÃO</span>
        <button className="nav-item" id="acesso-rh" type="button"><Icon nome="usuario" />Acesso RH</button>
        <button className="nav-item" id="conta-claude-rh" type="button"><Icon nome="cartao" />Conta Claude RH</button>
      </div>

      <div className="sidebar-rodape">
        <form method="post" action="/sair">
          <button className="nav-item nav-sair" type="submit"><Icon nome="sair" />Sair</button>
        </form>
      </div>
    </nav>
  );
}

function Compositor() {
  return (
    <footer className="compositor" id="compositor">
      <div className="previas" id="previas" />
      <div className="modo-ensino">
        <label>
          <input type="checkbox" id="ensinar" />
          <span className="ensino-icone" aria-hidden="true">✦</span>
          <span><strong>Ensinar um processo</strong><small>Ajude o Aquilix a aprender sua rotina</small></span>
        </label>
      </div>
      <div className="linha">
        <button className="icone" id="anexar" type="button" title="Anexar foto, print ou arquivo" aria-label="Anexar foto, print ou arquivo"><Icon nome="clipe" /></button>
        <button className="icone" id="microfone" type="button" title="Gravar áudio" aria-label="Gravar áudio"><Icon nome="microfone" /></button>
        <button className="icone voz" id="voz" type="button" aria-pressed="false" title="Ativar respostas faladas" aria-label="Ativar respostas faladas">🔇</button>
        <textarea id="texto" rows="1" aria-label="Mensagem para o assistente" placeholder="Pergunte ao Aquilix..." />
        <button className="icone enviar" id="enviar" type="button" title="Enviar" aria-label="Enviar mensagem"><Icon nome="enviar" /></button>
        <button className="icone parar" id="parar" type="button" title="Parar" aria-label="Parar resposta" hidden><Icon nome="parar" preenchido /></button>
      </div>
      <div className="dica-compositor">Enter para enviar <span>·</span> Shift + Enter para nova linha <span>·</span> Você também pode colar imagens</div>
      <div className="status" id="status" role="status" aria-live="polite" />
      <input type="file" id="arquivo" multiple hidden />
    </footer>
  );
}

function ModalConhecimentos() {
  return (
    <dialog className="modal" id="modal-conhecimentos">
      <div className="modal-cabecalho"><div><h2>Conhecimentos ensinados</h2><p>Memória local dos processos que você ensinar. O assistente recebe só os trechos relacionados.</p></div><button className="botao-leve" id="fechar-conhecimentos" type="button">Fechar</button></div>
      <textarea id="texto-conhecimentos" aria-label="Conteúdo dos conhecimentos ensinados" spellCheck="false" />
      <div className="modal-rodape"><span className="status" id="status-conhecimentos" /><button className="botao-principal" id="salvar-conhecimentos" type="button">Salvar conhecimentos</button></div>
    </dialog>
  );
}

function ModalAcessoRh() {
  return (
    <dialog className="modal modal-sm" id="modal-acesso-rh">
      <div className="modal-cabecalho"><div><h2>Acesso exclusivo ao RH</h2><p>Crie um login separado. Essa conta poderá usar somente o agente de Recursos Humanos.</p></div><button className="botao-leve" id="fechar-acesso-rh" type="button">Fechar</button></div>
      <div className="campos-acesso-rh">
        <label>Login do RH<input id="usuario-rh" autoComplete="username" minLength="3" maxLength="128" required /></label>
        <label>Senha nova<input id="senha-rh" type="password" autoComplete="new-password" minLength="8" maxLength="1024" required /></label>
        <label>Repita a senha<input id="repetir-senha-rh" type="password" autoComplete="new-password" minLength="8" maxLength="1024" required /></label>
      </div>
      <div className="modal-rodape"><span className="status" id="status-acesso-rh" /><button className="botao-principal" id="salvar-acesso-rh" type="button">Salvar acesso</button></div>
    </dialog>
  );
}

function ModalClaudeRh() {
  return (
    <dialog className="modal modal-sm" id="modal-claude-rh">
      <div className="modal-cabecalho"><div><h2>Conta Claude do RH</h2><p>O agente de Recursos Humanos usará uma conta separada.</p></div><button className="botao-leve" id="fechar-claude-rh" type="button">Fechar</button></div>
      <div className="informacao-conta-rh"><strong>selecao@gruponucleoservice.com.br</strong><span id="status-claude-rh">Verificando conexão...</span><p>O login oficial será aberto em uma nova janela neste computador. Não digite sua senha neste painel.</p></div>
      <div className="modal-rodape"><span className="status" id="status-login-claude-rh" /><button className="botao-leve" id="verificar-claude-rh" type="button">Verificar conexão</button><button className="botao-principal" id="login-claude-rh" type="button">Entrar na conta Claude</button></div>
    </dialog>
  );
}

function ModalCompartilhamentos() {
  return (
    <dialog className="modal" id="modal-compartilhamentos">
      <div className="modal-cabecalho"><div><h2>Relatórios compartilhados</h2><p>Qualquer pessoa com um link ativo pode ver aquele relatório. Não compartilhe dados confidenciais.</p></div><button className="botao-leve" id="fechar-compartilhamentos" type="button">Fechar</button></div>
      <div id="lista-compartilhamentos" className="lista-compartilhamentos" />
    </dialog>
  );
}

function ModalAgenda() {
  return (
    <dialog className="modal" id="modal-agenda">
      <div className="modal-cabecalho"><div><h2>Agenda automática</h2><p>Tarefas que rodam sozinhas. Ative as que quiser.</p></div><button className="botao-leve" id="fechar-agenda" type="button">Fechar</button></div>
      <div id="lista-agenda" className="lista-agenda" />
      <div className="modal-rodape"><span className="status" id="status-agenda" /></div>
    </dialog>
  );
}

function ModalJarvis() {
  return (
    <dialog className="modal modal-jarvis" id="modal-jarvis">
      <div className="modal-cabecalho">
        <div>
          <span className="jarvis-selo"><Icon nome="estrela" /> ASSISTENTE DE VOZ</span>
          <h2>O que posso fazer por você?</h2>
          <p>Digite ou dite um comando. O Aquilix pode falar a resposta quando a leitura em voz alta estiver ativa.</p>
        </div>
        <button className="botao-leve" id="fechar-jarvis" type="button">Fechar</button>
      </div>
      <div className="jarvis-atalhos">
        <button className="jarvis-atalho" data-jarvis-command="Que horas são?" type="button">Que horas são?</button>
        <button className="jarvis-atalho" data-jarvis-command="Qual é a data de hoje?" type="button">Data de hoje</button>
        <button className="jarvis-atalho" data-jarvis-command="Conte uma piada" type="button">Contar uma piada</button>
        <button className="jarvis-atalho" data-jarvis-command="Pesquisar na Wikipédia sobre " type="button">Wikipédia</button>
        <button className="jarvis-atalho jarvis-acao-local" data-jarvis-command="Pesquisar no Google " type="button">Google</button>
        <button className="jarvis-atalho jarvis-acao-local" data-jarvis-command="Tocar música" type="button">Tocar música</button>
      </div>
      <label className="jarvis-rotulo" htmlFor="jarvis-comando">Seu comando</label>
      <div className="jarvis-compositor">
        <textarea id="jarvis-comando" rows="2" maxLength="500" placeholder="Ex.: anote para mim: ligar para o fornecedor às 15h" />
        <button className="icone" id="jarvis-microfone" type="button" title="Ditar comando" aria-label="Ditar comando"><Icon nome="microfone" /></button>
        <button className="botao-principal" id="jarvis-executar" type="button"><Icon nome="enviar" /> Executar</button>
      </div>
      <div className="jarvis-resultado" id="jarvis-resultado" role="status" aria-live="polite" />
      <section className="jarvis-notas-secao">
        <div className="jarvis-notas-cabecalho"><div><h3>Notas deste departamento</h3><p>Notas ficam salvas no computador do Aquilix.</p></div><button className="botao-leve" id="jarvis-atualizar-notas" type="button">Atualizar</button></div>
        <div className="jarvis-notas" id="jarvis-notas" />
      </section>
      <section className="jarvis-pc" id="jarvis-pc" hidden>
        <div className="jarvis-notas-cabecalho"><div><h3>Recursos do PC do servidor</h3><p>Disponíveis somente quando o painel é aberto neste computador.</p></div><span className="jarvis-local-selo">LOCAL</span></div>
        <div className="jarvis-atalhos">
          <button className="jarvis-atalho" data-jarvis-command="Abrir google" type="button">Abrir Google</button>
          <button className="jarvis-atalho" data-jarvis-command="Tocar música" type="button">Tocar música</button>
          <button className="jarvis-atalho" data-jarvis-command="Capturar a tela" type="button">Capturar tela</button>
          <button className="jarvis-atalho" data-jarvis-command="Cancelar desligamento" type="button">Cancelar energia agendada</button>
          <button className="jarvis-atalho jarvis-power" data-jarvis-command="Reiniciar o computador" type="button">Reiniciar PC</button>
          <button className="jarvis-atalho jarvis-power" data-jarvis-command="Desligar o computador" type="button">Desligar PC</button>
        </div>
      </section>
      <div className="jarvis-aviso">Desligar ou reiniciar exige confirmação e agenda a ação para 60 segundos depois. Capturas de tela e controles do PC não funcionam pela internet.</div>
    </dialog>
  );
}

function App() {
  const [menuAberto, setMenuAberto] = useState(false);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = '/estatico/painel.js?v=20261106-historico';
    script.onerror = () => {
      const status = document.getElementById('status');
      if (status) status.textContent = 'Não foi possível carregar os recursos do painel. Atualize a página.';
    };
    document.body.appendChild(script);
    return () => script.remove();
  }, []);

  function fecharMenu() {
    setMenuAberto(false);
  }

  return (
    <>
      <div className="app">
        <BarraLateral aberta={menuAberto} onNavegar={fecharMenu} />
        <div className="main">
          <header className="topbar">
            <button className="menu-mobile" type="button" aria-label="Abrir menu" aria-expanded={menuAberto} onClick={() => setMenuAberto(!menuAberto)}><Icon nome="menu" /></button>
            <span className="topbar-titulo" id="titulo-conversa">Assistente <span>inteligente</span></span>
            <button className="botao-leve voltar-historico" id="voltar-historico" type="button" hidden>
              Voltar à conversa atual
            </button>
            <span className="topbar-marca"><i /> AQUILIX AI</span>
          </header>
          <main className="conversa" id="conversa" onClick={fecharMenu} />
          <Compositor />
        </div>
      </div>
      <div className={`sidebar-overlay${menuAberto ? ' visivel' : ''}`} onClick={fecharMenu} aria-hidden="true" />
      <ModalConhecimentos />
      <ModalAcessoRh />
      <ModalClaudeRh />
      <ModalCompartilhamentos />
      <ModalAgenda />
      <ModalJarvis />
    </>
  );
}

createRoot(document.getElementById('root')).render(<App />);
