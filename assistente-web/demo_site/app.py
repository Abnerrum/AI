"""
app.py - Site demonstrativo local para testar o Assistente Web.

Funcionalidades:
- Login com usuario/senha fixos (admin/1234)
- Tabela de ordens de servico com paginacao
- Formulario de lancamento de nova ordem
- Verificacao de lancamento

ESTE SITE E APENAS PARA DEMONSTRACAO E TESTES.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
app.secret_key = "chave-demo-apenas-para-testes"

# --- Dados simulados ---

USUARIOS = {
    "admin": "1234",
    "tecnico1": "1234",
    "tecnico2": "1234",
}

STATUS_OPCOES = ["Pendente", "Em andamento", "Concluido", "Cancelado"]
TECNICOS = ["Carlos Silva", "Ana Costa", "Pedro Lima", "Maria Santos"]
CLIENTES = [
    "Empresa ABC Ltda", "Comercio XYZ", "Padaria Bom Sabor",
    "Farmacia Saude", "Auto Mecanica JR", "Loja Eletro Plus",
    "Restaurante Sabor & Cia", "Clinica Vida", "Escola Futuro",
    "Supermercado Central", "Hotel Estrela", "Academia Corpo Ativo",
    "Pet Shop Amigo Fiel", "Papelaria Escolar", "Consultorio Dental",
]

# Gerar ordens de servico simuladas
ORDENS = []
for i in range(1, 68):
    dias_atras = random.randint(0, 30)
    data = datetime.now() - timedelta(days=dias_atras)
    ORDENS.append({
        "numero": f"OS-{2024000 + i}",
        "cliente": random.choice(CLIENTES),
        "status": random.choice(STATUS_OPCOES),
        "tecnico": random.choice(TECNICOS),
        "descricao": f"Servico de manutencao #{i}",
        "data": data.strftime("%d/%m/%Y"),
        "valor": f"R$ {random.randint(80, 2500):.2f}".replace(".", ","),
    })

# Garantir que algumas sao de hoje
for i in range(5):
    ORDENS[i]["data"] = datetime.now().strftime("%d/%m/%Y")
    ORDENS[i]["status"] = "Pendente"

POR_PAGINA = 10


# --- Rotas ---

@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("ordens"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        senha = request.form.get("senha", "")
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session["usuario"] = usuario
            flash(f"Bem-vindo, {usuario}!", "success")
            return redirect(url_for("ordens"))
        else:
            flash("Usuario ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    flash("Voce saiu do sistema.", "info")
    return redirect(url_for("login"))


@app.route("/ordens")
def ordens():
    if "usuario" not in session:
        return redirect(url_for("login"))

    # Filtros
    filtro_status = request.args.get("status", "")
    filtro_cliente = request.args.get("cliente", "")
    filtro_data = request.args.get("data", "")

    dados = ORDENS[:]

    if filtro_status:
        dados = [o for o in dados if o["status"] == filtro_status]
    if filtro_cliente:
        dados = [o for o in dados if filtro_cliente.lower() in o["cliente"].lower()]
    if filtro_data:
        dados = [o for o in dados if o["data"] == filtro_data]

    # Paginacao
    try:
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        pagina = 1
    total = len(dados)
    total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)
    pagina = max(1, min(pagina, total_paginas))
    inicio = (pagina - 1) * POR_PAGINA
    fim = inicio + POR_PAGINA
    dados_pagina = dados[inicio:fim]

    return render_template(
        "ordens.html",
        ordens=dados_pagina,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        filtro_status=filtro_status,
        filtro_cliente=filtro_cliente,
        filtro_data=filtro_data,
        status_opcoes=STATUS_OPCOES,
        hoje=datetime.now().strftime("%d/%m/%Y"),
        usuario=session["usuario"],
    )


@app.route("/nova-ordem", methods=["GET", "POST"])
def nova_ordem():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        tecnico = request.form.get("tecnico", "").strip()
        descricao = request.form.get("descricao", "").strip()
        valor = request.form.get("valor", "0").strip()

        if not cliente or not tecnico:
            flash("Cliente e tecnico sao obrigatorios.", "danger")
            return render_template("nova_ordem.html", tecnicos=TECNICOS, clientes=CLIENTES)

        # Verificar duplicidade (mesmo cliente + mesma descricao hoje)
        hoje = datetime.now().strftime("%d/%m/%Y")
        duplicada = any(
            o["cliente"] == cliente and o["descricao"] == descricao and o["data"] == hoje
            for o in ORDENS
        )
        if duplicada:
            flash("ATENCAO: Ja existe uma ordem identica para este cliente hoje.", "warning")
            return render_template("nova_ordem.html", tecnicos=TECNICOS, clientes=CLIENTES)

        numero = f"OS-{2024000 + len(ORDENS) + 1}"
        ORDENS.insert(0, {
            "numero": numero,
            "cliente": cliente,
            "status": "Pendente",
            "tecnico": tecnico,
            "descricao": descricao,
            "data": hoje,
            "valor": f"R$ {valor}",
        })
        flash(f"Ordem {numero} criada com sucesso!", "success")
        return redirect(url_for("ordens"))

    return render_template("nova_ordem.html", tecnicos=TECNICOS, clientes=CLIENTES)


@app.route("/api/ordens")
def api_ordens():
    """API JSON para consultas programaticas."""
    if "usuario" not in session:
        return jsonify({"erro": "Nao autenticado"}), 401
    return jsonify({"total": len(ORDENS), "ordens": ORDENS})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SITE DEMONSTRATIVO - Assistente Web")
    print("  Acesse: http://localhost:5000")
    print("  Login: admin / 1234")
    print("=" * 50 + "\n")
    app.run(host="127.0.0.1", debug=False, port=5000)
