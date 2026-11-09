"""
assistente.py - Interface principal em portugues (CLI).
Recebe comandos JSON via terminal, executa e exibe resultados.
"""

import json
import sys
import os

import executor

BANNER = r"""
 +---------------------------------------------------+
 |     ASSISTENTE WEB - Automacao de Navegador       |
 |                                                   |
 |  Cole comandos JSON do ChatGPT aqui.              |
 |  Digite 'ajuda' para ver opcoes.                  |
 |  Digite 'sair' para encerrar.                     |
 +---------------------------------------------------+
"""

AJUDA = """
COMANDOS RAPIDOS (digite direto):
  ajuda       - Mostra esta ajuda
  acoes       - Lista todas as acoes disponiveis
  login       - Preenche login na janela local de credenciais
  login manual - Aguarda voce entrar pelo navegador
  https://... - Abre o link diretamente
  sair        - Encerra o programa

COMO USAR COM O CHATGPT:
  1. Descreva o que voce quer para o ChatGPT no chat.
  2. O ChatGPT responde com um JSON de comando.
  3. Copie o JSON e cole aqui.
  4. O programa executa e mostra o resultado.
  5. Se precisar, copie o resumo do resultado de volta para o ChatGPT.

EXEMPLO DE COMANDO JSON:
  {"acao": "abrir_navegador", "usuario": "abner"}
  {"acao": "abrir_url", "usuario": "abner", "params": {"url": "http://localhost:5000"}}

FLUXOS SALVOS:
  Voce pode salvar sequencias de comandos como fluxos e reutiliza-los.
"""


def formatar_resultado(resultado: dict) -> str:
    """Formata o resultado para exibicao no terminal."""
    return json.dumps(resultado, indent=2, ensure_ascii=False, default=str)


def resultado_para_claude(resultado: dict) -> str:
    """
    Gera uma versao compacta do resultado para copiar e enviar ao ChatGPT.
    Remove dados volumosos como 'dados_completos'.
    """
    resumo = dict(resultado)
    if "resultado" in resumo and isinstance(resumo["resultado"], dict):
        r = dict(resumo["resultado"])
        r.pop("dados_completos", None)  # Remove dados brutos
        resumo["resultado"] = r
    return json.dumps(resumo, ensure_ascii=False, default=str)


def main():
    def confirmar(previa):
        print("\n[PREVIA DO ENVIO]", formatar_resultado(previa))
        return input("Confirmar envio? (s/n): ").strip().lower() == "s"
    executor.configurar_confirmacao(confirmar)
    print(BANNER)

    while True:
        try:
            entrada = input("\n[COMANDO] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando...")
            break

        if not entrada:
            continue

        # Comandos rapidos
        if entrada.lower() == "sair":
            print("Ate mais!")
            break

        if entrada.lower() == "ajuda":
            print(AJUDA)
            continue

        if entrada.lower() == "acoes":
            print("\nAcoes disponiveis:")
            for a in sorted(executor.ACOES_PERMITIDAS):
                print(f"  - {a}")
            continue

        if entrada.lower() in ("login", "login manual"):
            acao = "fazer_login" if entrada.lower() == "login" else "aguardar_login"
            print(formatar_resultado(executor.executar({"acao": acao})))
            continue
        if entrada.startswith(("https://", "http://")):
            print(formatar_resultado(executor.executar({"acao": "abrir_url", "params": {"url": entrada}})))
            print("Para entrar, digite login ou faca login no navegador e digite login manual.")
            continue

        # Tentar interpretar como JSON
        try:
            cmd = json.loads(entrada)
        except json.JSONDecodeError:
            print("[ERRO] Entrada nao e um JSON valido. Digite 'ajuda' para instrucoes.")
            continue

        if not isinstance(cmd, dict):
            print("[ERRO] Cole um objeto JSON, nao uma lista ou valor isolado.")
            continue
        acao = cmd.get("acao", "")

        # Executar
        print("[EXECUTANDO]", acao, "...")
        resultado = executor.executar(cmd)

        # Exibir resultado completo
        print("\n[RESULTADO]")
        print(formatar_resultado(resultado))

        # Exibir versao compacta para ChatGPT
        resumo = resultado_para_claude(resultado)
        print(f"\n[COPIE PARA O CHATGPT] (resumo compacto):")
        print(resumo)


if __name__ == "__main__":
    try:
        main()
    finally:
        executor.fechar_todos()
