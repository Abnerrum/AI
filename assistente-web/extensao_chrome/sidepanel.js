const API = "http://127.0.0.1:5050";
const $ = id => document.getElementById(id);
let agente = "operacional";
let contexto = null;
let token = "";
let lendo = false;
let vozAtiva = false;

function mostrarStatus(texto) {
  $("status").textContent = texto;
}

function definirConectado(conectado) {
  $("conectar").classList.toggle("conectado", conectado);
  $("codigo").hidden = conectado;
  $("abrir-painel").hidden = conectado;
  $("vincular").hidden = conectado;
  $("desconectar").hidden = !conectado;
  $("agente").disabled = !conectado;
  $("contexto").disabled = !conectado;
  $("texto").disabled = !conectado;
  $("enviar").disabled = !conectado;
  $("nova").disabled = !conectado;
  mostrarStatus(conectado ? "Conectado ao painel local" : "Desconectado");
}

async function chamar(caminho, opcoes = {}) {
  const cabecalhos = new Headers(opcoes.headers || {});
  cabecalhos.set("Authorization", `Bearer ${token}`);
  cabecalhos.set("X-Painel", "1");
  const resposta = await fetch(API + caminho, {
    ...opcoes,
    headers: cabecalhos,
    credentials: "omit"
  });
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(dados.erro || `Erro ${resposta.status}`);
  return dados;
}

function adicionarMensagem(texto, tipo) {
  const item = document.createElement("div");
  item.className = `mensagem ${tipo}`;
  item.textContent = texto;
  $("conversa").append(item);
  $("conversa").scrollTop = $("conversa").scrollHeight;
  return item;
}

function falar(texto) {
  if (!vozAtiva || !("speechSynthesis" in window)) return;
  const conteudo = texto
    .replace(/```[\s\S]*?```/g, " bloco de código omitido. ")
    .replace(/\[([^\]]+)\]\((?:https?:\/\/|\/)[^)]+\)/g, "$1")
    .replace(/https?:\/\/\S+/g, " link ")
    .replace(/[#*_`>|~]/g, " ")
    .replace(/^\s*[-+]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 8000);
  if (!conteudo) return;
  window.speechSynthesis.cancel();
  const fala = new SpeechSynthesisUtterance(conteudo);
  fala.lang = "pt-BR";
  fala.rate = 1;
  fala.pitch = 0.95;
  const vozes = window.speechSynthesis.getVoices();
  fala.voice = vozes.find(voz => /^pt-BR$/i.test(voz.lang))
    || vozes.find(voz => /^pt/i.test(voz.lang))
    || null;
  window.speechSynthesis.speak(fala);
}

function definirVoz(ativa) {
  vozAtiva = ativa && "speechSynthesis" in window;
  const botao = $("voz");
  botao.textContent = vozAtiva ? "🔊" : "🔇";
  botao.classList.toggle("voz-ativa", vozAtiva);
  botao.setAttribute("aria-pressed", String(vozAtiva));
  botao.title = vozAtiva ? "Desativar respostas faladas" : "Ativar respostas faladas";
  if (!vozAtiva && "speechSynthesis" in window) window.speechSynthesis.cancel();
}

async function carregarConversa() {
  const dados = await chamar(`/api/conversa?agente=${encodeURIComponent(agente)}`);
  $("conversa").replaceChildren();
  for (const mensagem of dados.mensagens.slice(-30)) {
    adicionarMensagem(mensagem.texto || "", mensagem.papel === "usuario" ? "usuario" : "assistente");
  }
  if (dados.rodando) acompanhar();
}

async function carregarAgentes() {
  const dados = await chamar("/api/agentes");
  $("agente").replaceChildren();
  for (const item of dados.agentes) {
    const opcao = document.createElement("option");
    opcao.value = item.id;
    opcao.textContent = item.nome;
    $("agente").append(opcao);
  }
  agente = $("agente").value || "operacional";
}

async function lerAbaAtual() {
  const [aba] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
  if (!aba?.id || !/^https?:\/\//i.test(aba.url || "")) {
    throw new Error("Esta aba não permite leitura pela extensão.");
  }
  const resultados = await chrome.scripting.executeScript({
    target: {tabId: aba.id},
    func: () => ({
      url: location.href,
      titulo: document.title,
      texto: (document.body?.innerText || "").slice(0, 6000)
    })
  });
  const pagina = resultados[0]?.result;
  if (!pagina) throw new Error("Não consegui ler o texto desta aba.");
  return pagina;
}

async function enviar() {
  const texto = $("texto").value.trim();
  if (!texto || lendo) return;
  const dados = new FormData();
  dados.set("agente", agente);
  dados.set("texto", texto);
  if (contexto) {
    dados.set("contexto_url", contexto.url);
    dados.set("contexto_titulo", contexto.titulo);
    dados.set("contexto_texto", contexto.texto);
  }
  const resumo = contexto ? `${texto}\n\n[Texto da aba incluído: ${contexto.titulo}]` : texto;
  adicionarMensagem(resumo, "usuario");
  $("texto").value = "";
  $("enviar").disabled = true;
  try {
    await chamar("/api/mensagem", {method: "POST", body: dados});
    contexto = null;
    $("contexto-status").textContent = "";
    await acompanhar();
  } catch (erro) {
    adicionarMensagem(erro.message, "erro");
  } finally {
    $("enviar").disabled = false;
  }
}

async function acompanhar() {
  if (lendo) return;
  lendo = true;
  $("enviar").disabled = true;
  $("agente").disabled = true;
  $("nova").disabled = true;
  $("parar").hidden = false;
  let respostaAtual = null;
  let textoResposta = "";
  try {
    const resposta = await fetch(
      `${API}/api/eventos?agente=${encodeURIComponent(agente)}&desde=0`,
      {headers: {Authorization: `Bearer ${token}`, "X-Painel": "1"}, credentials: "omit"}
    );
    if (!resposta.ok || !resposta.body) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.erro || `Erro ${resposta.status}`);
    }
    const leitor = resposta.body.getReader();
    const decodificador = new TextDecoder();
    let buffer = "";
    while (true) {
      const {value, done} = await leitor.read();
      if (done) break;
      buffer += decodificador.decode(value, {stream: true});
      const blocos = buffer.split("\n\n");
      buffer = blocos.pop() || "";
      for (const bloco of blocos) {
        const linha = bloco.split("\n").find(item => item.startsWith("data: "));
        if (!linha) continue;
        const evento = JSON.parse(linha.slice(6));
        if (evento.tipo === "texto") {
          textoResposta += evento.texto;
          if (!respostaAtual) respostaAtual = adicionarMensagem("", "assistente");
          respostaAtual.textContent += evento.texto;
        } else if (evento.tipo === "ferramenta") {
          adicionarMensagem(evento.texto, "ferramenta");
        } else if (evento.tipo === "erro") {
          adicionarMensagem(evento.texto, "erro");
        } else if (evento.tipo === "permissao") {
          mostrarPermissao(evento);
        } else if (evento.tipo === "pergunta") {
          mostrarPergunta(evento);
        } else if (evento.tipo === "fim") {
          falar(textoResposta);
          await carregarConversa();
          return;
        }
      }
    }
  } catch (erro) {
    adicionarMensagem(erro.message, "erro");
  } finally {
    lendo = false;
    $("enviar").disabled = !token;
    $("agente").disabled = !token;
    $("nova").disabled = !token;
    $("parar").hidden = true;
  }
}

function mostrarPermissao(evento) {
  const cartao = document.createElement("div");
  cartao.className = "pedido";
  const texto = document.createElement("div");
  texto.textContent = `O assistente solicita autorização: ${evento.texto}`;
  cartao.append(texto);
  for (const [titulo, permitido] of [["Permitir", true], ["Negar", false]]) {
    const botao = document.createElement("button");
    botao.textContent = titulo;
    botao.onclick = async () => {
      botao.disabled = true;
      try {
        await chamar("/api/responder", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({id: evento.id, agente, permitir: permitido})
        });
      } catch (erro) {
        adicionarMensagem(erro.message, "erro");
      }
    };
    cartao.append(botao);
  }
  $("conversa").append(cartao);
}

function mostrarPergunta(evento) {
  const cartao = document.createElement("div");
  cartao.className = "pedido";
  const respostas = {};
  const perguntas = evento.perguntas || [];
  for (const pergunta of perguntas) {
    const rotulo = document.createElement("label");
    rotulo.textContent = pergunta.question || "Resposta";
    const entrada = document.createElement("input");
    entrada.placeholder = "Digite sua resposta";
    entrada.maxLength = 500;
    cartao.append(rotulo, entrada);
    respostas[pergunta.question] = entrada;
  }
  const botao = document.createElement("button");
  botao.textContent = "Enviar resposta";
  botao.onclick = async () => {
    const preenchidas = Object.fromEntries(
      Object.entries(respostas).map(([pergunta, entrada]) => [pergunta, entrada.value.trim()])
    );
    if (Object.values(preenchidas).some(valor => !valor)) return;
    botao.disabled = true;
    try {
      await chamar("/api/responder", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: evento.id, agente, respostas: preenchidas})
      });
    } catch (erro) {
      adicionarMensagem(erro.message, "erro");
    }
  };
  cartao.append(botao);
  $("conversa").append(cartao);
}

$("abrir-painel").onclick = () => chrome.tabs.create({url: `${API}/extensao/conectar`});
$("vincular").onclick = async () => {
  const codigo = $("codigo").value.trim();
  if (!codigo) return;
  try {
    const resposta = await fetch(`${API}/api/extensao/vincular`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({codigo}),
      credentials: "omit"
    });
    const dados = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(dados.erro || `Erro ${resposta.status}`);
    token = dados.token;
    await chrome.storage.local.set({tokenAssistenteNucleo: token});
    $("codigo").value = "";
    definirConectado(true);
    await carregarAgentes();
    await carregarConversa();
  } catch (erro) {
    mostrarStatus(erro.message);
  }
};
$("desconectar").onclick = async () => {
  try {
    await chamar("/api/extensao/revogar", {method: "POST"});
  } catch (erro) {
    mostrarStatus(`Token removido deste navegador; revogação no servidor falhou: ${erro.message}`);
  }
  await chrome.storage.local.remove("tokenAssistenteNucleo");
  token = "";
  definirConectado(false);
  $("conversa").replaceChildren();
};
$("contexto").onclick = async () => {
  $("contexto").disabled = true;
  try {
    contexto = await lerAbaAtual();
    $("contexto-status").textContent = `Aba incluída: ${contexto.titulo} (até 6.000 caracteres).`;
  } catch (erro) {
    contexto = null;
    $("contexto-status").textContent = erro.message;
  } finally {
    $("contexto").disabled = false;
  }
};
$("agente").onchange = async () => {
  agente = $("agente").value;
  try { await carregarConversa(); } catch (erro) { adicionarMensagem(erro.message, "erro"); }
};
$("nova").onclick = async () => {
  if (!confirm("Começar uma nova conversa deste departamento?")) return;
  try {
    await chamar("/api/nova", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({agente})
    });
    await carregarConversa();
  } catch (erro) {
    adicionarMensagem(erro.message, "erro");
  }
};
$("enviar").onclick = enviar;
$("voz").onclick = async () => {
  if (!("speechSynthesis" in window)) {
    mostrarStatus("Este navegador não oferece leitura em voz alta.");
    return;
  }
  definirVoz(!vozAtiva);
  await chrome.storage.local.set({vozNucleoAtiva: vozAtiva});
  if (vozAtiva) falar("Respostas faladas ativadas.");
};
$("parar").onclick = async () => {
  $("parar").disabled = true;
  try {
    await chamar("/api/parar", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({agente})
    });
  } catch (erro) {
    adicionarMensagem(erro.message, "erro");
  } finally {
    $("parar").disabled = false;
  }
};
$("texto").addEventListener("keydown", evento => {
  if (evento.key === "Enter" && !evento.shiftKey) {
    evento.preventDefault();
    enviar();
  }
});

(async () => {
  const salvo = await chrome.storage.local.get(["tokenAssistenteNucleo", "vozNucleoAtiva"]);
  token = salvo.tokenAssistenteNucleo || "";
  definirVoz(salvo.vozNucleoAtiva === true);
  if (!token) {
    definirConectado(false);
    return;
  }
  try {
    definirConectado(true);
    await carregarAgentes();
    await carregarConversa();
  } catch (erro) {
    token = "";
    await chrome.storage.local.remove("tokenAssistenteNucleo");
    definirConectado(false);
    mostrarStatus(`Reconecte a extensão: ${erro.message}`);
  }
})();
