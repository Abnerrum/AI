"""Painel local PrimeServer (somente ações explícitas do usuário)."""
import subprocess
import secrets
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
URLS = {"PHP / Laravel": "http://localhost:8080", "Python / FastAPI": "http://localhost:8000", "Java": "http://localhost:8081"}

class PrimeServer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PrimeServer | Painel de desenvolvimento")
        self.geometry("800x570")
        self.configure(bg="#101827")
        tk.Label(self, text="PrimeServer", fg="#eaf1ff", bg="#101827", font=("Segoe UI", 25, "bold")).pack(pady=(18, 0))
        tk.Label(self, text="PHP • Laravel • Python • Java • Docker • SQLite • MariaDB", fg="#99b4da", bg="#101827", font=("Segoe UI", 11)).pack(pady=(0, 18))
        actions = tk.Frame(self, bg="#101827")
        actions.pack()
        for title, args in [
            ("Iniciar tudo", ["up", "-d", "--build"]),
            ("Parar tudo", ["down"]),
            ("Reiniciar", ["restart"]),
            ("Status", ["ps"]),
            ("Logs", ["logs", "--tail", "80"]),
            ("Iniciar banco", ["--profile", "database", "up", "-d", "mariadb"]),
        ]:
            ttk.Button(actions, text=title, command=lambda a=args: self.run(a)).pack(side="left", padx=4)
        links = tk.Frame(self, bg="#101827")
        links.pack(pady=18)
        for title, url in URLS.items():
            ttk.Button(links, text=f"Abrir {title}", command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=5)
        self.log = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg="#172338", fg="#e4f0ff", insertbackground="white", height=19, font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.write("Bem-vindo! Inicie o Docker Desktop e clique em 'Iniciar tudo'.\n")
        self.write("O banco MariaDB é opcional. O painel gera senhas locais na primeira ação.\n")

    def write(self, content):
        self.log.insert(tk.END, content)
        self.log.see(tk.END)

    def ensure_env(self):
        target = ROOT / ".env"
        if not target.exists():
            target.write_text(
                "MARIADB_PASSWORD=" + secrets.token_urlsafe(32) + "\n"
                + "MARIADB_ROOT_PASSWORD=" + secrets.token_urlsafe(32) + "\n",
                encoding="utf-8",
            )
            self.write("Credenciais locais do MariaDB geradas em .env. Não compartilhe esse arquivo.\n")

    def run(self, args):
        self.ensure_env()
        self.write("\n$ docker compose " + " ".join(args) + "\n")
        def worker():
            try:
                result = subprocess.run(["docker", "compose", "--project-directory", str(ROOT), "-f", str(ROOT / "docker-compose.yml"), *args], cwd=ROOT, text=True, capture_output=True, timeout=300, errors="replace")
                output = (result.stdout or "") + (result.stderr or "") + f"\nCódigo de saída: {result.returncode}\n"
            except FileNotFoundError:
                output = "Docker não encontrado. Instale o Docker Desktop e abra-o antes de iniciar.\n"
            except subprocess.TimeoutExpired:
                output = "Tempo limite de 5 minutos excedido; confira o Docker Desktop e os logs.\n"
            except Exception as error:
                output = f"Erro: {error}\n"
            self.after(0, lambda: self.write(output))
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    PrimeServer().mainloop()
