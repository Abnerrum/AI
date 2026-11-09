const exemplos = {
  operacional: 'Crie um checklist para acompanhar ordens de serviço atrasadas e identificar a próxima ação de cada uma.',
  financeiro: 'Monte um modelo de conciliação com valor previsto, valor pago, data e diferença.',
  frotas: 'Monte um controle de combustível e manutenção para três veículos fictícios.',
  rh: 'Crie um checklist de integração para a primeira semana de uma nova pessoa na equipe.',
  administrativo: 'Organize um fluxo de revisão e aprovação de documentos internos.',
  estudos: 'Monte um roteiro de revisão de SQL com exercícios e respostas explicadas.',
};

const formulario = document.getElementById('formulario');
const agente = document.getElementById('agente');
const tarefa = document.getElementById('tarefa');
const resultado = document.getElementById('resultado');
const prompt = document.getElementById('prompt');
const statusCopia = document.getElementById('status-copia');

document.getElementById('exemplo').addEventListener('click', () => {
  tarefa.value = exemplos[agente.value];
  tarefa.focus();
});

formulario.addEventListener('submit', (evento) => {
  evento.preventDefault();
  const pedido = tarefa.value.trim();
  if (!pedido) {
    tarefa.focus();
    return;
  }

  const departamento = agente.selectedOptions[0].textContent;
  prompt.value = [
    `Atue como assistente do departamento de ${departamento}.`,
    '',
    pedido,
    '',
    'Responda em português do Brasil. Estruture a resposta em passos claros e indique quais informações faltam. Use dados fictícios se precisar de exemplos.',
  ].join('\n');
  statusCopia.textContent = '';
  resultado.hidden = false;
  prompt.focus();
});

document.getElementById('copiar').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(prompt.value);
    statusCopia.textContent = 'Prompt copiado.';
  } catch {
    prompt.focus();
    prompt.select();
    statusCopia.textContent = 'Use Ctrl+C ou a opção Copiar para copiar o texto selecionado.';
  }
});
