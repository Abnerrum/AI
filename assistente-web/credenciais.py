"""
credenciais.py - Logins por site no Gerenciador de Credenciais do Windows.

A senha e digitada pelo usuario numa janela local e nunca passa pelo chat,
por arquivos do projeto ou pelo historico.
"""

import json

import keyring

SERVICO = "assistente-web:"


def obter(site: str) -> tuple[str, str] | None:
    bruto = keyring.get_password(SERVICO + site, "login")
    if not bruto:
        return None
    dados = json.loads(bruto)
    return dados["u"], dados["s"]


def salvar(site: str, usuario: str, senha: str):
    keyring.set_password(SERVICO + site, "login", json.dumps({"u": usuario, "s": senha}))


def excluir(site: str) -> bool:
    try:
        keyring.delete_password(SERVICO + site, "login")
        return True
    except keyring.errors.PasswordDeleteError:
        return False


def pedir_na_tela(site: str) -> tuple[str, str] | None:
    """Abre uma janela local pedindo usuario e senha. None se cancelado."""
    import tkinter as tk

    resposta = {}
    janela = tk.Tk()
    janela.title("Assistente Web - login")
    janela.attributes("-topmost", True)
    janela.resizable(False, False)
    tk.Label(janela, text=f"Login para {site}", font=("Segoe UI", 11, "bold")).grid(row=0, columnspan=2, pady=(12, 4), padx=12)
    tk.Label(janela, text="Fica guardado no Gerenciador de Credenciais do Windows.\nO Claude/ChatGPT nao ve a senha.",
             fg="#555").grid(row=1, columnspan=2, padx=12, pady=(0, 8))
    tk.Label(janela, text="Usuario:").grid(row=2, column=0, sticky="e", padx=(12, 4))
    tk.Label(janela, text="Senha:").grid(row=3, column=0, sticky="e", padx=(12, 4))
    e_user = tk.Entry(janela, width=32)
    e_senha = tk.Entry(janela, width=32, show="*")
    e_user.grid(row=2, column=1, padx=(0, 12), pady=3)
    e_senha.grid(row=3, column=1, padx=(0, 12), pady=3)

    def ok(_=None):
        if e_user.get().strip() and e_senha.get():
            resposta["v"] = (e_user.get().strip(), e_senha.get())
            janela.destroy()

    botoes = tk.Frame(janela)
    botoes.grid(row=4, columnspan=2, pady=12)
    tk.Button(botoes, text="Salvar e entrar", width=14, command=ok).pack(side="left", padx=4)
    tk.Button(botoes, text="Cancelar", width=10, command=janela.destroy).pack(side="left", padx=4)
    janela.bind("<Return>", ok)
    janela.bind("<Escape>", lambda _: janela.destroy())
    e_user.focus_force()
    janela.mainloop()
    return resposta.get("v")
