const formulario = document.getElementById('chat');
const mensagens = document.getElementById('mensagens');
const entrada = document.getElementById('mensagem');
const statusChat = document.getElementById('status-chat');
const limpar = document.getElementById('limpar');
const enviar = formulario.querySelector('button[type="submit"]');
const csrf = document.querySelector('meta[name="aquilix-csrf"]').content;
let historico = [];

function adicionarMensagem(rotulo, texto) {
  const artigo = document.createElement('article');
  const titulo = document.createElement('strong');
  const corpo = document.createElement('div');
  corpo.className = 'texto-chat';
  titulo.textContent = rotulo;
  corpo.textContent = texto;
  artigo.append(titulo, corpo);
  mensagens.append(artigo);
  mensagens.hidden = false;
}

limpar.addEventListener('click', () => {
  historico = [];
  mensagens.replaceChildren();
  mensagens.hidden = true;
  entrada.value = '';
  statusChat.textContent = '';
  entrada.focus();
});

formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const texto = entrada.value.trim();
  if (!texto || enviar.disabled) return;

  const pergunta = { role: 'user', content: texto };
  enviar.disabled = true;
  limpar.disabled = true;
  entrada.readOnly = true;
  statusChat.textContent = 'Aguardando resposta do Claude…';

  try {
    const resposta = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Aquilix-CSRF': csrf },
      body: JSON.stringify({ mensagens: [...historico, pergunta] }),
    });
    const dados = await resposta.json();
    if (!resposta.ok) {
      statusChat.textContent = dados.erro || 'Não foi possível obter a resposta.';
      return;
    }

    adicionarMensagem('Você', texto);
    adicionarMensagem('Claude', dados.resposta);
    historico = [...historico, pergunta, {
      role: 'assistant',
      content: dados.resposta.slice(0, entrada.maxLength),
    }].slice(-4);
    entrada.value = '';
    statusChat.textContent = 'Resposta recebida.';
    entrada.scrollIntoView({ block: 'nearest' });
  } catch {
    statusChat.textContent = 'Falha de conexão. Tente novamente.';
  } finally {
    enviar.disabled = false;
    limpar.disabled = false;
    entrada.readOnly = false;
    entrada.focus();
  }
});
