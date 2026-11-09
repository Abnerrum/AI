// painel.js - conversa com o Claude: texto, anexos (colar/arrastar/escolher) e audio.
const $ = id => document.getElementById(id);
const conversa = $('conversa'), texto = $('texto'), previas = $('previas'), statusEl = $('status');
const agenteSelect = $('agente');
let agenteAtual = 'operacional';
let perfilAtual = 'admin';
let historicoAtualId = null;
let pendentes = [];          // arquivos a enviar
let fonte = null;            // EventSource da resposta em andamento
let viva = null;             // bolha da resposta em andamento
let limiteAtingido = false, enviando = false;
let gravador = null, pedacos = [], inicioGravacao = 0, relogio = null;
let vozAtiva = false, textoVozResposta = '';

// ------------------------------------------------------------ markdown simples
function esc(s) { return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>')
    .replace(/\[([^\]]+)\]\((\/relatorios\/(?:frotas|financeiro|operacional|administrativo)\/[A-Za-z0-9_-]+\.html)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
}
function md(fonteTexto) {
  const blocos = [];
  let s = esc(fonteTexto || '').replace(/```\w*\n?([\s\S]*?)```/g, (_, c) => `\u0000${blocos.push(c) - 1}\u0000`);
  const linhas = s.split('\n'), out = [];
  let i = 0;
  const celulas = l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => inline(c.trim()));
  while (i < linhas.length) {
    const l = linhas[i];
    if (/^\u0000\d+\u0000$/.test(l.trim())) { out.push(`<pre><code>${blocos[+l.trim().slice(1, -1)]}</code></pre>`); i++; continue; }
    if (/^#{1,6}\s/.test(l)) { out.push(`<h3>${inline(l.replace(/^#+\s/, ''))}</h3>`); i++; continue; }
    if (l.trim().startsWith('|') && /^\s*\|?[\s:|-]+\|?\s*$/.test(linhas[i + 1] || '')) {
      let t = '<table><tr>' + celulas(l).map(c => `<th>${c}</th>`).join('') + '</tr>';
      i += 2;
      while (i < linhas.length && linhas[i].trim().startsWith('|')) { t += '<tr>' + celulas(linhas[i]).map(c => `<td>${c}</td>`).join('') + '</tr>'; i++; }
      out.push(t + '</table>'); continue;
    }
    if (/^\s*([-*]|\d+[.)])\s+/.test(l)) {
      const ordenada = /^\s*\d/.test(l), itens = [];
      while (i < linhas.length && /^\s*([-*]|\d+[.)])\s+/.test(linhas[i])) { itens.push(`<li>${inline(linhas[i].replace(/^\s*([-*]|\d+[.)])\s+/, ''))}</li>`); i++; }
      out.push(ordenada ? `<ol>${itens.join('')}</ol>` : `<ul>${itens.join('')}</ul>`); continue;
    }
    if (!l.trim()) { i++; continue; }
    const par = [];
    while (i < linhas.length && linhas[i].trim() && !/^(#{1,6}\s|\s*([-*]|\d+[.)])\s+|\s*\||\u0000)/.test(linhas[i])) { par.push(inline(linhas[i])); i++; }
    if (par.length) out.push(`<p>${par.join('<br>')}</p>`); else { out.push(`<p>${inline(l)}</p>`); i++; }
  }
  return out.join('').replace(/\u0000(\d+)\u0000/g, (_, n) => `<code>${blocos[+n]}</code>`);
}

// ------------------------------------------------------------ util
async function api(caminho, opcoes = {}) {
  opcoes.headers = Object.assign({'X-Painel': '1'}, opcoes.headers || {});
  const r = await fetch(caminho, opcoes);
  if (r.status === 401) { location.href = '/login'; throw new Error('sessao'); }
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) {
    const erro = new Error(dados.erro || `Erro ${r.status}`);
    Object.assign(erro, dados);
    throw erro;
  }
  return dados;
}
function perto() { return conversa.scrollHeight - conversa.scrollTop - conversa.clientHeight < 120; }
function rolar(forcar) { if (forcar || perto()) conversa.scrollTop = conversa.scrollHeight; }
function aviso(msg) { statusEl.textContent = msg || ''; }
function limparTextoParaVoz(valor) {
  return valor
    .replace(/```[\s\S]*?```/g, ' bloco de código omitido. ')
    .replace(/\[([^\]]+)\]\((?:https?:\/\/|\/)[^)]+\)/g, '$1')
    .replace(/https?:\/\/\S+/g, ' link ')
    .replace(/[#*_`>|~]/g, ' ')
    .replace(/^\s*[-+]\s+/gm, '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 8000);
}
function falar(texto, idioma = 'pt-BR') {
  if (!vozAtiva || !('speechSynthesis' in window)) return;
  const conteudo = limparTextoParaVoz(texto);
  if (!conteudo) return;
  window.speechSynthesis.cancel();
  const fala = new SpeechSynthesisUtterance(conteudo);
  fala.lang = idioma;
  fala.rate = 1;
  fala.pitch = 0.95;
  const vozes = window.speechSynthesis.getVoices();
  const lingua = idioma.split('-')[0];
  fala.voice = vozes.find(voz => voz.lang.toLowerCase() === idioma.toLowerCase())
    || vozes.find(voz => voz.lang.toLowerCase().startsWith(lingua))
    || null;
  window.speechSynthesis.speak(fala);
}
function definirVoz(ativa) {
  vozAtiva = ativa && 'speechSynthesis' in window;
  const botao = $('voz');
  botao.textContent = vozAtiva ? '🔊' : '🔇';
  botao.setAttribute('aria-pressed', String(vozAtiva));
  botao.title = vozAtiva ? 'Desativar respostas faladas' : 'Ativar respostas faladas';
  botao.setAttribute('aria-label', botao.title);
  if (!vozAtiva && 'speechSynthesis' in window) window.speechSynthesis.cancel();
}
function erroAcessoRh(erro) {
  return erro.message === 'Erro 404'
    ? 'O servidor precisa ser reiniciado para carregar o acesso separado do RH. Feche o painel e abra novamente pelo INICIAR.bat.'
    : erro.message;
}
function anexarUrl(relativo) {
  return '/anexos/' + relativo.split('/').map(encodeURIComponent).join('/');
}
function el(tag, classe, html) { const e = document.createElement(tag); if (classe) e.className = classe; if (html != null) e.innerHTML = html; return e; }
function urlAgente(caminho) {
  return `${caminho}${caminho.includes('?') ? '&' : '?'}agente=${encodeURIComponent(agenteAtual)}`;
}
function atualizarUsoClaude(uso) {
  const bloqueado = uso.bloqueado;
  limiteAtingido = bloqueado;
  const economia = $('modo-economico');
  const economicoAtivo = uso.modelo === 'haiku';
  economia.textContent = economicoAtivo
    ? 'Economia: ativada · Haiku'
    : 'Economia: desativada · Sonnet';
  economia.classList.toggle('ativo', economicoAtivo);
  economia.setAttribute('aria-pressed', String(economicoAtivo));
  economia.title = economicoAtivo
    ? 'Voltar ao Claude Sonnet'
    : 'Usar Claude Haiku e respostas mais curtas';
  $('uso-claude').textContent = uso.habilitado
    ? `Claude hoje: ${uso.mensagens}/${uso.limite}`
    : `Trava desligada · ${uso.mensagens} hoje`;
  $('uso-claude').classList.toggle('bloqueado', bloqueado);
  $('trava-claude').textContent = uso.habilitado ? 'Destravar' : 'Ativar trava';
  $('trava-claude').title = uso.habilitado
    ? 'Desativar o limite diário de mensagens'
    : 'Reativar o limite diário de mensagens';
  $('enviar').disabled = bloqueado || enviando;
  $('texto').disabled = bloqueado;
  $('anexar').disabled = bloqueado;
  $('microfone').disabled = bloqueado;
  $('arquivo').disabled = bloqueado;
  if (bloqueado) {
    aviso(`Limite de ${uso.limite} mensagens hoje atingido. Use Destravar se precisar continuar.`);
  } else if (statusEl.textContent.startsWith('Limite de ')) {
    aviso('');
  }
}

// ------------------------------------------------------------ conversa
function anexosHtml(lista) {
  if (!lista || !lista.length) return '';
  return '<div class="anexos-msg">' + lista.map(a => {
    const url = '/anexos/' + a.split('/').map(encodeURIComponent).join('/');
    const nome = esc(a.split('/').pop().replace(/^\d{6}_[0-9a-f]{4}_/, ''));
    return /\.(png|jpe?g|gif|webp)$/i.test(a) ? `<a href="${url}" target="_blank"><img src="${url}" alt="${nome}"></a>`
                                               : `<a class="arquivo" href="${url}" target="_blank">📎 ${nome}</a>`;
  }).join('') + '</div>';
}
function bolha(m) {
  const b = el('div', 'msg ' + m.papel);
  let html = m.papel === 'usuario' ? anexosHtml(m.anexos) + (m.texto ? `<p>${esc(m.texto).replace(/\n/g, '<br>')}</p>` : '')
                                   : md(m.texto || '_(sem texto)_');
  if (m.acoes && m.acoes.length) html += `<details class="acoes"><summary>${m.acoes.length} ${m.acoes.length === 1 ? 'ação' : 'ações'}</summary><ul>${m.acoes.map(a => `<li>${esc(a)}</li>`).join('')}</ul></details>`;
  b.innerHTML = html + `<div class="hora">${esc(m.hora || '')}</div>`;
  botoesCompartilhamento(b);
  return b;
}
function botoesCompartilhamento(container) {
  if (perfilAtual !== 'admin') return;
  container.querySelectorAll('a[href^="/relatorios/"]').forEach(link => {
    if (link.nextElementSibling?.classList.contains('compartilhar-relatorio')) return;
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'compartilhar-relatorio';
    botao.textContent = 'Compartilhar';
    botao.dataset.relatorio = link.getAttribute('href');
    link.insertAdjacentElement('afterend', botao);
  });
}
async function carregar() {
  const solicitado = agenteAtual;
  const historicoSolicitado = historicoAtualId;
  const caminho = historicoSolicitado
    ? urlAgente(`/api/historico/${encodeURIComponent(historicoSolicitado)}`)
    : urlAgente('/api/conversa');
  const dados = await api(caminho);
  if (solicitado !== agenteAtual || historicoSolicitado !== historicoAtualId) return;
  if (fonte) { fonte.close(); fonte = null; }
  conversa.innerHTML = '';
  if (historicoSolicitado) {
    $('titulo-conversa').textContent = `Histórico · ${dados.titulo}`;
    $('voltar-historico').hidden = false;
    $('compositor').classList.add('somente-leitura');
    $('texto').disabled = true;
    $('anexar').disabled = true;
    $('microfone').disabled = true;
    $('voz').disabled = true;
    $('enviar').disabled = true;
    $('parar').hidden = true;
    $('ensinar').disabled = true;
    const atual = await api(urlAgente('/api/conversa'));
    if (solicitado !== agenteAtual || historicoSolicitado !== historicoAtualId) return;
    atualizarUsoClaude(atual.uso_claude);
    $('texto').disabled = true;
    $('anexar').disabled = true;
    $('microfone').disabled = true;
    $('voz').disabled = true;
    $('enviar').disabled = true;
    $('ensinar').disabled = true;
  } else {
    $('titulo-conversa').innerHTML = 'Assistente <span>inteligente</span>';
    $('voltar-historico').hidden = true;
    $('compositor').classList.remove('somente-leitura');
    $('voz').disabled = false;
    $('ensinar').disabled = false;
  }
  if (!dados.mensagens.length && !dados.rodando) {
    const agenteSelecionado = agenteSelect.selectedOptions[0]?.textContent || 'o agente';
    conversa.appendChild(el('div', 'vazio', `<div class="boas-vindas-icone" aria-hidden="true"><img src="/estatico/aquilix-logo.png" alt=""></div><span class="boas-vindas-etiqueta">ASSISTENTE ${esc(agenteSelecionado).toLocaleUpperCase('pt-BR')}</span><h2>Por onde começamos?</h2><p>Pergunte, envie um arquivo ou peça ajuda com uma rotina do seu departamento.</p><div class="sugestoes"><button type="button" data-sugestao="Me ajude a organizar minhas tarefas de hoje">Organizar minhas tarefas</button><button type="button" data-sugestao="Quero ensinar um processo deste departamento">Ensinar um processo</button><button type="button" data-sugestao="Me ajude a criar um relatório">Criar um relatório</button><button type="button" data-sugestao="Que horas são e qual é a data de hoje?">Perguntar data e hora</button><button type="button" data-sugestao="Pesquise na Wikipédia sobre ">Pesquisar na Wikipédia</button><button type="button" data-sugestao="Conte uma piada curta">Contar uma piada</button></div><span class="boas-vindas-dica">Você também pode colar uma imagem ou gravar um áudio.</span>`));
    conversa.querySelectorAll('[data-sugestao]').forEach(botao => {
      botao.addEventListener('click', () => {
        texto.value = botao.dataset.sugestao;
        ajustar();
        texto.focus();
      });
    });
  }
  dados.mensagens.forEach(m => conversa.appendChild(bolha(m)));
  if (dados.mensagens.length || dados.rodando) rolar(true);
  else conversa.scrollTop = 0;
  if (!historicoSolicitado) {
    if (dados.rodando) acompanhar();
    else { ocupado(false); viva = null; }
    atualizarUsoClaude(dados.uso_claude);
  } else {
    ocupado(false);
    viva = null;
    aviso('Conversa antiga em modo de leitura. Volte à conversa atual para enviar mensagens.');
  }
  atualizarListaHistorico();
}

async function atualizarListaHistorico() {
  const lista = $('lista-historico');
  try {
    const dados = await api(urlAgente('/api/historico'));
    lista.replaceChildren();
    if (!dados.conversas.length) {
      lista.appendChild(el('div', 'historico-vazio', 'Suas conversas anteriores aparecerão aqui.'));
      return;
    }
    dados.conversas.forEach(item => {
      const botao = document.createElement('button');
      botao.type = 'button';
      botao.className = `historico-item${item.id === historicoAtualId ? ' ativo' : ''}`;
      botao.dataset.historicoId = item.id;
      const titulo = document.createElement('strong');
      titulo.textContent = item.titulo;
      const detalhe = document.createElement('small');
      detalhe.textContent = `${item.data || 'Data desconhecida'} · ${item.mensagens} mensagens`;
      botao.append(titulo, detalhe);
      lista.appendChild(botao);
    });
  } catch (e) {
    lista.replaceChildren(el('div', 'historico-vazio', e.message));
  }
}

// ------------------------------------------------------------ resposta ao vivo
function ocupado(sim) {
  $('enviar').hidden = sim; $('parar').hidden = !sim;
  if (!sim) aviso('');
}
function acompanhar() {
  ocupado(true);
  textoVozResposta = '';
  viva = el('div', 'msg claude');
  viva.appendChild(el('div', 'pensando', 'Trabalhando'));
  conversa.appendChild(viva);
  rolar(true);
  if (fonte) fonte.close();
  fonte = new EventSource(urlAgente('/api/eventos?desde=0'));
  fonte.onmessage = e => tratar(JSON.parse(e.data));
  fonte.onerror = () => aviso('Conexão instável, tentando de novo...');
}
function tratar(ev) {
  aviso('');
  const pensando = viva.querySelector('.pensando');
  if (ev.tipo === 'texto') {
    textoVozResposta += ev.texto;
    const t = el('div', 'parte', md(ev.texto));
    botoesCompartilhamento(t);
    viva.insertBefore(t, pensando);
  } else if (ev.tipo === 'ferramenta') {
    viva.insertBefore(el('div', 'chip', esc(ev.texto)), pensando);
  } else if (ev.tipo === 'erro') {
    viva.insertBefore(el('p', 'erro', esc(ev.texto)), pensando);
  } else if (ev.tipo === 'permissao') {
    const c = el('div', 'pedido', `<strong>O Claude pede autorização:</strong><div>${esc(ev.texto)}</div><details><summary>detalhes</summary><pre>${esc(ev.detalhe || '')}</pre></details><div class="botoes"><button class="permitir">Permitir</button><button class="negar">Negar</button></div>`);
    c.id = 'p-' + ev.id;
    c.querySelector('.permitir').onclick = () => responder(ev.id, {permitir: true}, c);
    c.querySelector('.negar').onclick = () => responder(ev.id, {permitir: false}, c);
    conversa.appendChild(c);
  } else if (ev.tipo === 'pergunta') {
    const c = el('div', 'pedido'); c.id = 'p-' + ev.id;
    const respostas = {};
    (ev.perguntas || []).forEach(q => {
      c.appendChild(el('strong', '', esc(q.question || '')));
      const botoes = el('div', 'botoes');
      (q.options || []).forEach(o => {
        const b = el('button', 'opcao', `${esc(o.label)}${o.description ? `<small>${esc(o.description)}</small>` : ''}`);
        b.onclick = () => {
          botoes.querySelectorAll('button').forEach(x => x.style.outline = '');
          b.style.outline = '2px solid var(--destaque)';
          respostas[q.question] = o.label;
          if (Object.keys(respostas).length === ev.perguntas.length) responder(ev.id, {respostas}, c);
        };
        botoes.appendChild(b);
      });
      const outra = el('button', 'opcao', 'Outra resposta (escrever)');
      outra.onclick = () => { const r = prompt(q.question); if (r) { respostas[q.question] = r; if (Object.keys(respostas).length === ev.perguntas.length) responder(ev.id, {respostas}, c); } };
      botoes.appendChild(outra);
      c.appendChild(botoes);
    });
    const cancelar = el('button', 'negar', 'Não responder'); cancelar.onclick = () => responder(ev.id, {permitir: false}, c);
    c.appendChild(cancelar);
    conversa.appendChild(c);
  } else if (ev.tipo === 'respondido') {
    const c = $('p-' + ev.id); if (c) c.classList.add('feito');
  } else if (ev.tipo === 'fim') {
    falar(textoVozResposta);
    textoVozResposta = '';
    if (fonte) { fonte.close(); fonte = null; }
    carregar();
    return;
  }
  rolar();
}
async function responder(id, resposta, cartao) {
  cartao.classList.add('feito');
  try { await api('/api/responder', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.assign({id, agente: agenteAtual}, resposta))}); }
  catch (e) { aviso(e.message); }
}

// ------------------------------------------------------------ envio
function mostrarPrevias() {
  previas.innerHTML = '';
  pendentes.forEach((f, i) => {
    const p = el('div', 'previa');
    if (f.type.startsWith('image/')) { const img = el('img'); img.src = URL.createObjectURL(f); p.appendChild(img); }
    p.appendChild(el('span', '', esc(f.name)));
    const x = el('button', '', '×'); x.title = 'Remover'; x.onclick = () => { pendentes.splice(i, 1); mostrarPrevias(); };
    p.appendChild(x);
    previas.appendChild(p);
  });
}
function adicionar(arquivos) {
  for (const f of arquivos) {
    if (!f) continue;
    const nome = f.name && f.name !== 'image.png' ? f.name : `print_${new Date().toISOString().slice(11, 19).replace(/:/g, '')}.png`;
    pendentes.push(f.name === nome ? f : new File([f], nome, {type: f.type}));
  }
  mostrarPrevias();
}
async function enviar() {
  if (enviando || limiteAtingido) return;
  const t = texto.value.trim();
  if (!t && !pendentes.length) return;
  const dados = new FormData();
  dados.append('agente', agenteAtual);
  dados.append('texto', t);
  dados.append('ensinar', $('ensinar').checked ? '1' : '0');
  pendentes.forEach(f => dados.append('arquivos', f, f.name));
  enviando = true;
  $('enviar').disabled = true;
  aviso(pendentes.length ? 'Enviando anexos...' : '');
  try {
    await api('/api/mensagem', {method: 'POST', body: dados});
    texto.value = ''; pendentes = []; mostrarPrevias(); ajustar();
    await carregar();
  } catch (e) {
    aviso(e.message);
    if (e.message.includes('Limite diario')) {
      try {
        const uso = await api(urlAgente('/api/conversa'));
        atualizarUsoClaude(uso.uso_claude);
      } catch (atualizacao) { aviso(atualizacao.message); }
    }
  } finally {
    enviando = false;
    $('enviar').disabled = limiteAtingido;
  }
}

// ------------------------------------------------------------ audio
async function microfone() {
  if (gravador) { gravador.stop(); return; }
  if (!window.isSecureContext || !navigator.mediaDevices) {
    aviso('Microfone só funciona em https ou no próprio PC (localhost). Use o link de internet ou anexe um arquivo de áudio.');
    return;
  }
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({audio: true}); }
  catch (e) {
    aviso(e.name === 'NotFoundError' || e.name === 'OverconstrainedError'
      ? 'Nenhum microfone encontrado neste aparelho. Conecte um fone com microfone, use o celular (opção 6) ou anexe um arquivo de áudio pelo 📎.'
      : e.name === 'NotReadableError'
        ? 'O microfone está em uso por outro programa (Teams, WhatsApp...). Feche-o e tente de novo.'
        : 'Microfone bloqueado: clique no ícone à esquerda do endereço, em Microfone escolha Permitir e recarregue a página.');
    return;
  }
  const tipo = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'].find(t => MediaRecorder.isTypeSupported(t)) || '';
  gravador = new MediaRecorder(stream, tipo ? {mimeType: tipo} : undefined);
  pedacos = [];
  gravador.ondataavailable = e => e.data.size && pedacos.push(e.data);
  gravador.onstop = async () => {
    stream.getTracks().forEach(t => t.stop());
    clearInterval(relogio);
    $('microfone').classList.remove('gravando');
    const mime = gravador.mimeType || 'audio/webm';
    gravador = null;
    const ext = mime.includes('mp4') ? 'm4a' : mime.includes('ogg') ? 'ogg' : 'webm';
    const dados = new FormData();
    dados.append('audio', new Blob(pedacos, {type: mime}), `audio.${ext}`);
    aviso('Transcrevendo áudio... (a primeira vez demora mais)');
    try {
      const r = await api('/api/transcrever', {method: 'POST', body: dados});
      texto.value = (texto.value ? texto.value + ' ' : '') + r.texto;
      ajustar(); texto.focus();
      aviso('Áudio transcrito. Confira o texto e envie.');
    } catch (e) { aviso(e.message); }
  };
  gravador.start();
  inicioGravacao = Date.now();
  $('microfone').classList.add('gravando');
  relogio = setInterval(() => aviso(`Gravando ${Math.round((Date.now() - inicioGravacao) / 1000)}s - toque no microfone para parar`), 500);
}

// ------------------------------------------------------------ eventos da tela
function ajustar() { texto.style.height = 'auto'; texto.style.height = Math.min(texto.scrollHeight, 180) + 'px'; }
texto.addEventListener('input', ajustar);
texto.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !matchMedia('(pointer: coarse)').matches) { e.preventDefault(); enviar(); } });
texto.addEventListener('paste', e => {
  const arquivos = [...(e.clipboardData?.items || [])].filter(i => i.kind === 'file').map(i => i.getAsFile());
  if (arquivos.length) { e.preventDefault(); adicionar(arquivos); }
});
$('anexar').onclick = () => $('arquivo').click();
$('arquivo').onchange = e => { adicionar(e.target.files); e.target.value = ''; };
$('enviar').onclick = enviar;
$('voz').onclick = () => {
  if (!('speechSynthesis' in window)) {
    aviso('Este navegador não oferece leitura em voz alta.');
    return;
  }
  definirVoz(!vozAtiva);
  try { localStorage.setItem('nucleo-voz-ativa', String(vozAtiva)); }
  catch (e) { console.warn('Nao foi possivel salvar a preferencia de voz.', e); }
  if (vozAtiva) falar('Respostas faladas ativadas.');
};
$('parar').onclick = () => api('/api/parar', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({agente: agenteAtual})
}).catch(e => aviso(e.message));
$('agente').onchange = async () => {
  agenteAtual = agenteSelect.value;
  historicoAtualId = null;
  $('agente-descricao').textContent = agenteSelect.selectedOptions[0]?.dataset.descricao || 'Seu assistente especializado';
  try { localStorage.setItem('agente-departamento', agenteAtual); }
  catch (e) { console.warn('Nao foi possivel salvar o departamento selecionado.', e); }
  pendentes = [];
  mostrarPrevias();
  $('ensinar').checked = false;
  try { await carregar(); } catch (e) { aviso(e.message); }
};
$('historico-toggle').onclick = evento => {
  evento.stopPropagation();
  const lista = $('lista-historico');
  lista.hidden = !lista.hidden;
  $('historico-toggle').setAttribute('aria-expanded', String(!lista.hidden));
};
$('lista-historico').onclick = async evento => {
  const botao = evento.target.closest('[data-historico-id]');
  if (!botao) return;
  historicoAtualId = botao.dataset.historicoId;
  try { await carregar(); } catch (e) { aviso(e.message); }
};
$('voltar-historico').onclick = async () => {
  historicoAtualId = null;
  try { await carregar(); } catch (e) { aviso(e.message); }
};
$('microfone').onclick = microfone;
$('compartilhamentos').onclick = abrirCompartilhamentos;
$('fechar-compartilhamentos').onclick = () => $('modal-compartilhamentos').close();

// ------------------------------------------------------------ Aquilix Jarvis
const modalJarvis = $('modal-jarvis');
let gravadorJarvis = null, pedacosJarvis = [], relogioJarvis = null, inicioJarvis = 0;
function renderizarNotasJarvis(notas) {
  const lista = $('jarvis-notas');
  lista.replaceChildren();
  if (!notas.length) {
    lista.appendChild(el('p', 'jarvis-sem-notas', 'Nenhuma nota salva neste departamento.'));
    return;
  }
  notas.forEach(nota => {
    const item = el('article', 'jarvis-nota');
    const textoNota = el('p', '', esc(nota.texto).replace(/\n/g, '<br>'));
    const hora = el('time', '', esc(nota.criada_em.replace('T', ' ')));
    const apagar = el('button', 'jarvis-apagar-nota', 'Apagar');
    apagar.type = 'button';
    apagar.setAttribute('aria-label', 'Apagar nota');
    apagar.onclick = async () => {
      if (!confirm('Apagar esta nota deste departamento?')) return;
      try {
        await api(urlAgente(`/api/jarvis/notas/${encodeURIComponent(nota.id)}`), {method: 'DELETE'});
        await carregarNotasJarvis();
      } catch (erro) { resultadoJarvis(erro.message, true); }
    };
    item.append(textoNota, hora, apagar);
    lista.appendChild(item);
  });
}
async function carregarNotasJarvis() {
  const dados = await api(urlAgente('/api/jarvis/notas'));
  renderizarNotasJarvis(dados.notas);
}
function resultadoJarvis(mensagem, erro = false, anexo = '', idioma = 'pt') {
  const resultado = $('jarvis-resultado');
  resultado.replaceChildren();
  if (mensagem) {
    resultado.appendChild(el('p', erro ? 'erro' : 'jarvis-resposta', esc(mensagem).replace(/\n/g, '<br>')));
  }
  if (anexo) {
    const imagem = el('img', 'jarvis-captura');
    imagem.src = anexarUrl(anexo);
    imagem.alt = 'Captura de tela salva no computador do Aquilix';
    const link = el('a', 'jarvis-link-captura', 'Abrir captura');
    link.href = anexarUrl(anexo);
    link.target = '_blank';
    link.rel = 'noopener';
    resultado.append(imagem, link);
  }
  if (!erro && mensagem) falar(mensagem, idioma === 'en' ? 'en-US' : 'pt-BR');
}
async function executarJarvis(comando, confirmado = false) {
  const botao = $('jarvis-executar');
  botao.disabled = true;
  try {
    const dados = await api('/api/jarvis', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({comando, agente: agenteAtual, confirmado})
    });
    resultadoJarvis(dados.resposta, false, dados.anexo || '', dados.idioma);
    if (dados.acao === 'anotar') await carregarNotasJarvis();
    if (dados.acao === 'parar_voz') {
      if (gravadorJarvis) gravadorJarvis.stop();
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      modalJarvis.close();
    }
    return dados;
  } catch (erro) {
    if (erro.confirmacao_necessaria) {
      const acao = erro.acao === 'desligar' ? 'desligar' : 'reiniciar';
      const ingles = erro.idioma === 'en';
      const confirmou = confirm(ingles
        ? `Confirm ${acao === 'desligar' ? 'shutdown' : 'restart'} on this computer in 60 seconds? This action only works when the panel is open on this PC.`
        : `Confirmar ${acao} este computador em 60 segundos? O comando só funciona quando o painel está aberto neste PC.`);
      if (confirmou) return executarJarvis(comando, true);
      resultadoJarvis(
        ingles ? 'Action canceled. The computer was not changed.' : 'Ação cancelada. O computador não foi alterado.',
        false,
        '',
        erro.idioma
      );
      return null;
    }
    resultadoJarvis(erro.message, true);
    return null;
  } finally {
    botao.disabled = false;
  }
}
async function abrirJarvis() {
  $('jarvis-comando').value = '';
  $('jarvis-resultado').replaceChildren();
  modalJarvis.showModal();
  try {
    const [estado] = await Promise.all([
      api(urlAgente('/api/jarvis')),
      carregarNotasJarvis()
    ]);
    $('jarvis-pc').hidden = !estado.local;
    document.querySelectorAll('.jarvis-acao-local').forEach(botao => { botao.hidden = !estado.local; });
  } catch (erro) { resultadoJarvis(erro.message, true); }
}
$('jarvis').onclick = abrirJarvis;
$('fechar-jarvis').onclick = () => {
  if (gravadorJarvis) gravadorJarvis.stop();
  modalJarvis.close();
};
$('jarvis-atualizar-notas').onclick = () => carregarNotasJarvis().catch(erro => resultadoJarvis(erro.message, true));
$('jarvis-executar').onclick = () => executarJarvis($('jarvis-comando').value.trim());
$('jarvis-comando').addEventListener('keydown', evento => {
  if (evento.key === 'Enter' && !evento.shiftKey) {
    evento.preventDefault();
    executarJarvis(evento.currentTarget.value.trim());
  }
});
modalJarvis.addEventListener('click', evento => {
  const atalho = evento.target.closest('[data-jarvis-command]');
  if (!atalho) return;
  const comando = atalho.dataset.jarvisCommand;
  if (comando.endsWith(' ')) {
    $('jarvis-comando').value = comando;
    $('jarvis-comando').focus();
    return;
  }
  executarJarvis(comando);
});
$('jarvis-microfone').onclick = async () => {
  const botao = $('jarvis-microfone');
  if (gravadorJarvis) {
    gravadorJarvis.stop();
    return;
  }
  if (!window.isSecureContext || !navigator.mediaDevices || !window.MediaRecorder) {
    resultadoJarvis('Ditar só funciona em HTTPS ou neste computador. Digite o comando ou use o botão de microfone da conversa.', true);
    return;
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio: true});
  } catch (erro) {
    resultadoJarvis(
      erro.name === 'NotFoundError'
        ? 'Nenhum microfone foi encontrado neste aparelho.'
        : 'Microfone bloqueado. Permita o acesso ao microfone nas configurações do navegador.',
      true
    );
    return;
  }
  const tipo = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
    .find(formato => MediaRecorder.isTypeSupported(formato)) || '';
  try {
    gravadorJarvis = new MediaRecorder(stream, tipo ? {mimeType: tipo} : undefined);
  } catch (erro) {
    stream.getTracks().forEach(trilha => trilha.stop());
    resultadoJarvis(`Não foi possível iniciar a gravação: ${erro.message}`, true);
    return;
  }
  pedacosJarvis = [];
  gravadorJarvis.ondataavailable = evento => { if (evento.data.size) pedacosJarvis.push(evento.data); };
  gravadorJarvis.onstop = async () => {
    stream.getTracks().forEach(trilha => trilha.stop());
    clearInterval(relogioJarvis);
    botao.classList.remove('gravando');
    botao.title = 'Ditar comando';
    const mime = gravadorJarvis.mimeType || 'audio/webm';
    gravadorJarvis = null;
    const extensao = mime.includes('mp4') ? 'm4a' : mime.includes('ogg') ? 'ogg' : 'webm';
    const dados = new FormData();
    dados.append('audio', new Blob(pedacosJarvis, {type: mime}), `jarvis.${extensao}`);
    resultadoJarvis('Transcrevendo áudio…');
    try {
      const transcricao = await api('/api/transcrever', {method: 'POST', body: dados});
      $('jarvis-comando').value = transcricao.texto;
      $('jarvis-comando').focus();
      resultadoJarvis('Confira o texto transcrito e toque em Executar.');
    } catch (erro) { resultadoJarvis(erro.message, true); }
  };
  gravadorJarvis.start();
  inicioJarvis = Date.now();
  botao.classList.add('gravando');
  botao.title = 'Parar gravação';
  resultadoJarvis('Gravando… toque no microfone para parar.');
  relogioJarvis = setInterval(() => {
    if ((Date.now() - inicioJarvis) > 30_000 && gravadorJarvis) gravadorJarvis.stop();
  }, 500);
};
document.querySelectorAll('[data-jarvis-command]').forEach(botao => { botao.type = 'button'; });
conversa.addEventListener('click', async e => {
  const botao = e.target.closest('.compartilhar-relatorio');
  if (!botao) return;
  const relatorio = botao.dataset.relatorio.match(
    /^\/relatorios\/(frotas|financeiro|operacional|administrativo)\/([A-Za-z0-9_-]+\.html)$/
  );
  if (!relatorio) { aviso('O endereço deste relatório não é válido para compartilhamento.'); return; }
  if (!confirm('Este link será público: qualquer pessoa que o receber poderá ver o relatório. Ele permanecerá ativo até ser revogado. Para acesso pela internet, deixe a opção 6 ou 7 ativa. Continuar?')) return;
  botao.disabled = true;
  try {
    const compartilhamento = await api('/api/compartilhamentos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({agente: relatorio[1], nome: relatorio[2]})
    });
    const hostname = new URL(compartilhamento.url).hostname;
    const enderecoLocal = hostname === 'localhost' || hostname === '[::1]' ||
      /^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname);
    const dicaTunel = enderecoLocal
      ? ' Para acesso fora da rede local, inicie a opção 6 ou 7.'
      : '';
    try {
      await navigator.clipboard.writeText(compartilhamento.url);
      aviso(`Link público copiado.${dicaTunel} Você pode revogá-lo em “Links públicos”.`);
    } catch (e) {
      window.prompt('Copie o link público do relatório:', compartilhamento.url);
      aviso(`Link criado.${dicaTunel} Você pode revogá-lo em “Links públicos”.`);
    }
  } catch (e) { aviso(e.message); }
  finally { botao.disabled = false; }
});
async function abrirCompartilhamentos() {
  const lista = $('lista-compartilhamentos');
  lista.replaceChildren(el('p', '', 'Carregando links...'));
  $('modal-compartilhamentos').showModal();
  try {
    const dados = await api('/api/compartilhamentos');
    lista.replaceChildren();
    if (!dados.compartilhamentos.length) {
      lista.appendChild(el('p', '', 'Ainda não há relatórios compartilhados.'));
      return;
    }
    dados.compartilhamentos.forEach(compartilhamento => {
      const item = el('div', 'item-compartilhamento');
      const info = document.createElement('div');
      const nome = document.createElement('strong');
      nome.textContent = `${compartilhamento.agente} · ${compartilhamento.nome}`;
      const link = document.createElement('a');
      link.href = compartilhamento.url;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = compartilhamento.url;
      const criado = document.createElement('small');
      criado.textContent = `Criado em ${compartilhamento.criado || 'data desconhecida'}`;
      info.append(nome, document.createElement('br'), link, document.createElement('br'), criado);
      const revogar = el('button', 'botao-revogar', 'Revogar');
      revogar.type = 'button';
      revogar.onclick = async () => {
        if (!confirm(`Revogar o link público de "${compartilhamento.nome}"?`)) return;
        revogar.disabled = true;
        try {
          await api('/api/compartilhamentos', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({token: compartilhamento.token})
          });
          item.remove();
          if (!lista.querySelector('.item-compartilhamento')) {
            lista.appendChild(el('p', '', 'Ainda não há relatórios compartilhados.'));
          }
        } catch (e) {
          aviso(e.message);
          revogar.disabled = false;
        }
      };
      item.append(info, revogar);
      lista.appendChild(item);
    });
  } catch (e) {
    lista.replaceChildren(el('p', 'erro', e.message));
  }
}
$('trava-claude').onclick = async () => {
  try {
    const atual = await api('/api/limite');
    const habilitado = !atual.habilitado;
    const confirmacao = habilitado
      ? 'Reativar o limite diário de mensagens?'
      : 'Destravar o limite diário? O painel poderá enviar mensagens sem esse teto e consumir mais créditos.';
    if (!confirm(confirmacao)) return;
    const uso = await api('/api/limite', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({habilitado})
    });
    atualizarUsoClaude(uso);
  } catch (e) { aviso(e.message); }
};
$('modo-economico').onclick = async () => {
  const botao = $('modo-economico');
  botao.disabled = true;
  try {
    const atual = await api('/api/limite');
    const uso = await api('/api/limite', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({modelo: atual.modelo === 'haiku' ? 'sonnet' : 'haiku'})
    });
    atualizarUsoClaude(uso);
  } catch (e) { aviso(e.message); }
  finally { botao.disabled = false; }
};
$('conhecimentos').onclick = async () => {
  try {
    const dados = await api(urlAgente('/api/conhecimentos'));
    const editor = $('texto-conhecimentos');
    editor.value = dados.conteudo;
    editor.dataset.original = dados.conteudo;
    $('status-conhecimentos').textContent = '';
    $('modal-conhecimentos').showModal();
  } catch (e) { aviso(e.message); }
};
$('acesso-rh').onclick = async () => {
  try {
    const acesso = await api('/api/acesso-rh');
    $('usuario-rh').value = acesso.usuario || '';
    $('senha-rh').value = '';
    $('repetir-senha-rh').value = '';
    $('status-acesso-rh').textContent = acesso.configurado
      ? 'Acesso configurado. Preencha uma nova senha para atualizar.'
      : 'Ainda não há um login separado configurado para RH.';
    $('modal-acesso-rh').showModal();
  } catch (e) { aviso(erroAcessoRh(e)); }
};
async function verificarContaClaudeRh(abrir = false) {
  if (abrir) {
    $('status-login-claude-rh').textContent = '';
    $('modal-claude-rh').showModal();
  }
  try {
    const status = await api('/api/claude-rh');
    $('status-claude-rh').textContent = status.conectado
      ? `Conectado à conta ${status.email_conectado}.`
      : status.email_conectado
        ? `Conectada outra conta (${status.email_conectado}). Conecte a conta correta do RH.`
        : status.instalado
          ? `A conta ${status.email_esperado} ainda não foi conectada neste computador.`
          : 'Claude Code não está instalado neste computador.';
  } catch (e) { $('status-claude-rh').textContent = erroAcessoRh(e); }
}
$('conta-claude-rh').onclick = () => verificarContaClaudeRh(true);
$('fechar-claude-rh').onclick = () => $('modal-claude-rh').close();
$('verificar-claude-rh').onclick = () => verificarContaClaudeRh();
$('login-claude-rh').onclick = async () => {
  const botao = $('login-claude-rh');
  botao.disabled = true;
  $('status-login-claude-rh').textContent = 'Abrindo o login oficial no computador do painel...';
  try {
    const resultado = await api('/api/claude-rh/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: '{}'
    });
    $('status-login-claude-rh').textContent = resultado.conectado
      ? 'A conta Claude do RH já está conectada.'
      : resultado.iniciado
        ? 'Janela de login aberta neste computador. Conclua o acesso e clique em “Verificar conexão”.'
        : 'A janela de login já está aberta. Conclua o acesso e depois verifique a conexão.';
  } catch (e) { $('status-login-claude-rh').textContent = erroAcessoRh(e); }
  finally { botao.disabled = false; }
};
$('fechar-acesso-rh').onclick = () => $('modal-acesso-rh').close();
$('salvar-acesso-rh').onclick = async () => {
  const botao = $('salvar-acesso-rh');
  botao.disabled = true;
  $('status-acesso-rh').textContent = 'Salvando acesso...';
  try {
    const dados = await api('/api/acesso-rh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        usuario: $('usuario-rh').value,
        senha: $('senha-rh').value,
        repetir: $('repetir-senha-rh').value
      })
    });
    $('senha-rh').value = '';
    $('repetir-senha-rh').value = '';
    $('status-acesso-rh').textContent = `Acesso RH configurado para "${dados.usuario}". A senha fica protegida no cofre do Windows.`;
  } catch (e) { $('status-acesso-rh').textContent = erroAcessoRh(e); }
  finally { botao.disabled = false; }
};
$('fechar-conhecimentos').onclick = () => {
  const editor = $('texto-conhecimentos');
  if (editor.value !== editor.dataset.original && !confirm('Descartar as alteracoes nao salvas?')) return;
  $('modal-conhecimentos').close();
};
$('salvar-conhecimentos').onclick = async () => {
  const botao = $('salvar-conhecimentos');
  botao.disabled = true;
  $('status-conhecimentos').textContent = 'Salvando...';
  try {
    const conteudo = $('texto-conhecimentos').value;
    const dados = await api('/api/conhecimentos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({conteudo, agente: agenteAtual})
    });
    $('texto-conhecimentos').dataset.original = conteudo;
    $('status-conhecimentos').textContent = `${dados.caracteres} caracteres salvos neste computador.`;
  } catch (e) { $('status-conhecimentos').textContent = e.message; }
  finally { botao.disabled = false; }
};
$('nova').onclick = async () => {
  if (historicoAtualId) {
    historicoAtualId = null;
    try { await carregar(); } catch (e) { aviso(e.message); }
    return;
  }
  if (!confirm('Começar uma conversa nova? A atual fica guardada no histórico.')) return;
  try {
    await api('/api/nova', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({agente: agenteAtual})
    });
    await carregar();
    await atualizarListaHistorico();
  } catch (e) { aviso(e.message); }
};
['dragover', 'dragenter'].forEach(t => document.addEventListener(t, e => { e.preventDefault(); document.body.classList.add('soltar'); }));
['dragleave', 'drop'].forEach(t => document.addEventListener(t, e => { e.preventDefault(); document.body.classList.remove('soltar'); }));
document.addEventListener('drop', e => adicionar(e.dataTransfer.files));

async function iniciar() {
  try { definirVoz(localStorage.getItem('nucleo-voz-ativa') === 'true'); }
  catch (e) { definirVoz(false); }
  try {
    const dados = await api('/api/agentes');
    perfilAtual = dados.perfil;
    agenteSelect.innerHTML = '';
    dados.agentes.forEach(item => {
      const opcao = document.createElement('option');
      opcao.value = item.id;
      opcao.textContent = item.nome;
      opcao.title = item.descricao;
      opcao.dataset.descricao = item.descricao;
      agenteSelect.appendChild(opcao);
    });
    const acessoRh = dados.perfil === 'rh';
    $('acesso-rh').hidden = acessoRh;
    $('conta-claude-rh').hidden = acessoRh;
    $('compartilhamentos').hidden = acessoRh;
    $('trava-claude').hidden = acessoRh;
    $('modo-economico').hidden = acessoRh;
    $('agente').disabled = acessoRh;
    $('perfil-acesso').hidden = !acessoRh;
    $('perfil-acesso').textContent = acessoRh ? 'Acesso exclusivo do RH' : '';
    let salvo = null;
    try { salvo = localStorage.getItem('agente-departamento'); }
    catch (e) { console.warn('Nao foi possivel recuperar o departamento selecionado.', e); }
    agenteAtual = acessoRh ? 'rh' : dados.agentes.some(item => item.id === salvo) ? salvo : 'operacional';
    agenteSelect.value = agenteAtual;
    $('agente-descricao').textContent = agenteSelect.selectedOptions[0]?.dataset.descricao || 'Seu assistente especializado';
    await carregar();
  } catch (e) { aviso(e.message); }
}

iniciar();

// ------------------------------------------------------------ agenda automática
$('agenda').onclick = abrirAgenda;
$('fechar-agenda').onclick = () => $('modal-agenda').close();

const DIAS_NOMES = ['', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

function renderizarTarefa(t) {
  const item = el('div', 'item-compartilhamento');
  const info = document.createElement('div');
  const nome = el('strong', '', esc(t.nome));
  const agente = el('small', '', `Departamento: ${esc(t.agente)} · ${t.tipo === 'horario' ? `Todo dia às ${esc(t.horario)}` : `Monitorar pasta`}`);
  if (t.tipo === 'horario' && t.dias) {
    const dias = t.dias.map(d => DIAS_NOMES[d] || d).join(', ');
    agente.textContent += ` (${dias})`;
  }
  if (t.tipo === 'arquivo' && t.pasta) {
    agente.textContent += ` · ${esc(t.pasta)}`;
  }
  const ultimaVez = el('small', '', t.ultimo_disparo ? `Último disparo: ${esc(t.ultimo_disparo)}` : 'Nunca disparou');
  info.append(nome, document.createElement('br'), agente, document.createElement('br'), ultimaVez);

  const acoes = el('div', 'botoes-agenda');

  const toggle = el('button', t.ativo ? 'botao-principal botao-sm' : 'botao-leve botao-sm', t.ativo ? 'Ativada ✓' : 'Ativar');
  toggle.type = 'button';
  toggle.onclick = async () => {
    toggle.disabled = true;
    try {
      await api('/api/agenda', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({...t, ativo: !t.ativo})
      });
      await abrirAgenda();
    } catch (e) { $('status-agenda').textContent = e.message; toggle.disabled = false; }
  };

  const executar = el('button', 'botao-leve botao-sm', '▶ Executar agora');
  executar.type = 'button';
  executar.onclick = async () => {
    if (!confirm(`Executar "${t.nome}" agora?`)) return;
    executar.disabled = true;
    try {
      await api(`/api/agenda/${encodeURIComponent(t.id)}/executar`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
      $('status-agenda').textContent = `Tarefa "${t.nome}" iniciada. Veja o departamento ${t.agente}.`;
    } catch (e) { $('status-agenda').textContent = e.message; }
    finally { executar.disabled = false; }
  };

  acoes.append(toggle, executar);
  item.append(info, acoes);
  return item;
}

async function abrirAgenda() {
  const lista = $('lista-agenda');
  $('status-agenda').textContent = '';
  lista.replaceChildren(el('p', '', 'Carregando...'));
  $('modal-agenda').showModal();
  try {
    const dados = await api('/api/agenda');
    lista.replaceChildren();
    if (!dados.tarefas.length) {
      lista.appendChild(el('p', '', 'Nenhuma tarefa configurada.'));
      return;
    }
    dados.tarefas.forEach(t => lista.appendChild(renderizarTarefa(t)));
  } catch (e) {
    lista.replaceChildren(el('p', 'erro', e.message));
  }
}
