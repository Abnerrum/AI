"""Núcleo Service | Relatório web de despesas.

Dados persistidos em PostgreSQL (produção) ou SQLite (desenvolvimento).
Carregamento por XLSX, CSV ou cadastro manual; nenhum dado privado no repositório.
"""
import csv
import hashlib
import io
import os
import re
import secrets
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from openpyxl import load_workbook
from sqlalchemy import BigInteger, Date, DateTime, Integer, String, Text, create_engine, select, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).parent
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'dados' / 'despesas.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

if DATABASE_URL.startswith("sqlite:///"):
    Path(DATABASE_URL.removeprefix("sqlite:///" )).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Despesa(Base):
    __tablename__ = "despesas"
    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chave: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    categoria: Mapped[str] = mapped_column(String(160), index=True)
    descricao: Mapped[str] = mapped_column(Text, default="")
    placa: Mapped[str] = mapped_column(String(100), default="")
    atendimento: Mapped[str] = mapped_column(String(100), index=True, default="")
    origem: Mapped[str] = mapped_column(String(150), index=True, default="")
    fornecedor: Mapped[str] = mapped_column(Text, default="")
    valor_centavos: Mapped[int] = mapped_column(BigInteger, nullable=False)
    situacao: Mapped[str] = mapped_column(String(100), default="")
    id_origem: Mapped[str] = mapped_column(String(240), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)

app = FastAPI(title="Relatório Financeiro — Núcleo Service", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
                   same_site="lax", https_only=os.environ.get("COOKIE_SECURE") == "1")
templates = Jinja2Templates(directory=str(ROOT / "templates"))

@app.middleware("http")
async def privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path != "/health":
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
AUTH_ATTEMPTS = {}


def normalized(value):
    t = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")

COLUMN_MAP = {
    "data": ["data", "date", "dt"],
    "categoria": ["categoria", "categoria_despesa", "category"],
    "descricao": ["descricao", "historico", "detalhes", "description"],
    "placa": ["placa_cartao", "placa", "cartao", "veiculo"],
    "atendimento": ["tipo_de_atendimento", "tipo_atendimento", "atendimento", "garantia"],
    "origem": ["origem", "fonte", "empresa"],
    "fornecedor": ["fornecedor_posto", "fornecedor", "posto"],
    "valor": ["valor_r", "valor", "total", "valor_rs", "valor_despesa"],
    "situacao": ["situacao", "status_pagamento", "status"],
    "id_origem": ["id_origem", "id", "codigo", "numero_documento"],
    "status_bi": ["status_bi", "incluir_bi"],
}


def parse_date(raw):
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, (int, float)):
        return date(1899, 12, 30) + timedelta(days=int(raw))
    s = str(raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Data inválida: {s[:40]}")


def parse_money(raw):
    if raw is None or str(raw).strip() == "":
        raise ValueError("Valor em branco")
    if isinstance(raw, (int, float, Decimal)):
        number = Decimal(str(raw))
    else:
        value = str(raw).replace("R$", "").replace("\xa0", "").replace(" ", "").strip()
        if "," in value and "." in value:
            value = value.replace(".", "").replace(",", ".") if value.rfind(",") > value.rfind(".") else value.replace(",", "")
        elif "," in value:
            value = value.replace(",", ".")
        elif value.count(".") > 1:
            value = value.replace(".", "")
        try:
            number = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Valor monetário inválido") from exc
    if not number.is_finite() or abs(number) > 10**12:
        raise ValueError("Valor monetário fora do limite")
    return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def map_header(headers):
    norm = [normalized(h) for h in headers]
    found = {}
    for attr, options in COLUMN_MAP.items():
        for n, h in enumerate(norm):
            if h in options:
                found[attr] = n
                break
    if "data" not in found or "categoria" not in found or "valor" not in found:
        return None
    return found


def row_to_expense(row, mapping, index):
    def field(name):
        pos = mapping.get(name)
        return row[pos] if pos is not None and pos < len(row) else ""
    if not field("data") or not field("categoria"):
        return None
    status = normalized(field("status_bi"))
    if status and status not in ("incluir", "sim", "true", "1", "yes"):
        return None
    d = parse_date(field("data"))
    amount = parse_money(field("valor"))
    payload = {key: str(field(key) or "").strip()[:240] for key in
               ("categoria", "descricao", "placa", "atendimento", "origem", "fornecedor", "situacao", "id_origem")}
    payload["data"] = d
    payload["valor_centavos"] = amount
    ident = "|".join((d.isoformat(), payload["categoria"], payload["descricao"], payload["origem"], payload["id_origem"], str(amount), payload["atendimento"], payload["placa"]))
    if not payload["id_origem"]:
        ident += f"|linha:{index}"
    payload["chave"] = hashlib.sha256(ident.encode("utf-8")).hexdigest()
    return payload


def parse_uploaded_file(file_name, stream):
    ext = Path(file_name).suffix.lower()
    if ext == ".csv":
        raw = stream.read()
        if not raw:
            raise ValueError("O CSV está vazio.")
        for codec in ("utf-8-sig", "cp1252"):
            try:
                text = raw.decode(codec)
                break
            except UnicodeDecodeError:
                continue
        lines = io.StringIO(text)
        sample = text[:10000]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        except csv.Error:
            dialect = csv.excel
        rows = csv.reader(lines, dialect=dialect)
        header = next(rows, None)
        mapping = map_header(header or [])
        if not mapping:
            raise ValueError("CSV sem as colunas obrigatórias: Data, Categoria e Valor.")
        return rows, mapping, None
    if ext == ".xlsx":
        try:
            book = load_workbook(stream, read_only=True, data_only=True)
        except Exception as exc:
            raise ValueError("Excel inválido ou danificado.") from exc
        ordered = sorted(book.worksheets, key=lambda ws: (ws.title != "BI_GRAFICOS", ws.title != "BASE_NOVA"))
        for sheet in ordered:
            it = sheet.iter_rows(values_only=True)
            header = next(it, None)
            mapping = map_header(header or [])
            if mapping:
                return it, mapping, book
        book.close()
        raise ValueError("Não encontrei uma aba com Data, Categoria e Valor. Use o modelo BI_GRAFICOS.")
    raise ValueError("Envie um arquivo .xlsx ou .csv.")


def import_records(file_name, stream):
    rows, mapping, workbook = parse_uploaded_file(file_name, stream)
    candidates, errors, ignored = [], [], 0
    try:
        for idx, row in enumerate(rows, start=2):
            if idx > 100002:
                raise ValueError("Máximo de 100.000 linhas por arquivo.")
            if not row or not any(x is not None and str(x).strip() for x in row):
                continue
            try:
                converted = row_to_expense(row, mapping, idx)
                if converted is None:
                    ignored += 1
                    continue
                candidates.append(converted)
            except (ValueError, TypeError) as err:
                if len(errors) < 8:
                    errors.append(f"Linha {idx}: {str(err)}")
        if not candidates:
            raise ValueError("Nenhuma despesa válida encontrada. " + (errors[0] if errors else "Verifique Status BI e valores."))
        unique = {x["chave"]: x for x in candidates}
        with SessionLocal.begin() as db:
            for i in range(0, len(unique), 500):
                chunk = list(unique.values())[i:i+500]
                stmt = pg_insert(Despesa) if engine.dialect.name == "postgresql" else sqlite_insert(Despesa)
                db.execute(stmt.values(chunk).on_conflict_do_nothing(index_elements=["chave"]))
        return {"analisadas": len(candidates), "duplicadas_na_planilha": len(candidates) - len(unique),
                "ignoradas": ignored, "erros_amostra": errors, "total_no_banco": count_records()}
    finally:
        if workbook:
            workbook.close()


def count_records():
    with SessionLocal() as db:
        return db.scalar(select(func.count(Despesa.pk))) or 0


def serialize_expense(x):
    return {"pk": x.pk, "data": x.data.isoformat(), "categoria": x.categoria,
            "descricao": x.descricao, "placa": x.placa, "atendimento": x.atendimento,
            "origem": x.origem, "fornecedor": x.fornecedor,
            "valor": x.valor_centavos / 100, "situacao": x.situacao, "id": x.id_origem}


def authenticated(request: Request):
    return request.session.get("authenticated") is True


def require_auth(request: Request):
    if not authenticated(request):
        raise HTTPException(401, "Faça login para acessar os dados.")


def require_persistent_storage():
    # Render gratuito tem disco efêmero. Nunca permita uploads persistidos em SQLite online.
    if os.environ.get("COOKIE_SECURE") == "1" and engine.dialect.name == "sqlite":
        raise HTTPException(503, "Configure DATABASE_URL com PostgreSQL persistente antes de adicionar despesas na hospedagem.")


def require_csrf(request: Request, body=None):
    token = request.headers.get("X-CSRF-Token") or ((body or {}).get("csrf_token") if isinstance(body, dict) else None)
    valid = request.session.get("csrf_token")
    if not (token and valid and secrets.compare_digest(str(token), str(valid))):
        raise HTTPException(403, "Token de segurança inválido.")


@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(select(func.count(Despesa.pk))).scalar()
        return {"status": "ok"}
    except Exception:
        return JSONResponse({"status": "database_unavailable"}, status_code=503)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if authenticated(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {
        "error": None if ADMIN_PASSWORD else "Configure ADMIN_PASSWORD no ambiente antes de usar o sistema.",
    }, status_code=200 if ADMIN_PASSWORD else 503)


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    if not ADMIN_PASSWORD:
        return templates.TemplateResponse(request, "login.html", {"error": "Configure ADMIN_PASSWORD no ambiente."}, status_code=503)
    form = await request.form()
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in AUTH_ATTEMPTS.get(ip, []) if now - t < 600]
    if len(attempts) >= 10:
        error = "Muitas tentativas. Tente novamente mais tarde."
    elif secrets.compare_digest(str(form.get("username", "")), ADMIN_USERNAME) and secrets.compare_digest(str(form.get("password", "")), ADMIN_PASSWORD):
        request.session.clear()
        request.session["authenticated"] = True
        request.session["csrf_token"] = secrets.token_hex(32)
        AUTH_ATTEMPTS.pop(ip, None)
        return RedirectResponse("/", status_code=303)
    else:
        attempts.append(now)
        AUTH_ATTEMPTS[ip] = attempts
        error = "Usuário ou senha incorretos."
    return templates.TemplateResponse(request, "login.html", {"error": error}, status_code=401)


@app.post("/logout")
async def logout(request: Request):
    require_auth(request)
    form = await request.form()
    require_csrf(request, dict(form))
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if not authenticated(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "index.html", {
        "csrf_token": request.session["csrf_token"], "username": ADMIN_USERNAME,
    })


@app.get("/api/records")
def records(request: Request):
    require_auth(request)
    with SessionLocal() as db:
        records = db.scalars(select(Despesa).order_by(Despesa.data.desc(), Despesa.pk.desc())).all()
        return {"registros": [serialize_expense(x) for x in records], "total": len(records),
                "storage_ready": not (os.environ.get("COOKIE_SECURE") == "1" and engine.dialect.name == "sqlite")}


@app.post("/api/import")
async def upload(request: Request):
    require_auth(request)
    require_csrf(request)
    require_persistent_storage()
    form = await request.form()
    file = form.get("file")
    if not file or not getattr(file, "filename", None):
        raise HTTPException(400, "Selecione um arquivo Excel ou CSV.")
    if Path(file.filename).suffix.lower() not in (".xlsx", ".csv"):
        raise HTTPException(400, "Somente .xlsx ou .csv são aceitos.")
    if getattr(file, "size", 0) and file.size > 20 * 1024 * 1024:
        raise HTTPException(413, "Arquivo muito grande: limite de 20 MB.")
    before = count_records()
    try:
        result = import_records(file.filename, file.file)
    except ValueError as err:
        raise HTTPException(400, str(err))
    finally:
        await file.close()
    result["novas"] = result["total_no_banco"] - before
    return {"resultado": result}


@app.post("/api/manual", status_code=201)
async def create_manual(request: Request):
    require_auth(request)
    require_csrf(request)
    require_persistent_storage()
    payload = await request.json()
    try:
        data = parse_date(payload.get("data"))
        categoria = str(payload.get("categoria") or "").strip()
        descricao = str(payload.get("descricao") or "").strip()
        if not categoria or not descricao:
            raise ValueError("Categoria e descrição são obrigatórias.")
        valor = parse_money(payload.get("valor"))
        novo = Despesa(
            chave=hashlib.sha256(f"manual:{uuid4()}".encode()).hexdigest(), data=data,
            categoria=categoria[:160], descricao=descricao[:2000],
            placa=str(payload.get("placa") or "")[:100],
            atendimento=str(payload.get("atendimento") or "Não informado")[:100],
            origem=str(payload.get("origem") or "MANUAL")[:150],
            fornecedor=str(payload.get("fornecedor") or "")[:2000],
            valor_centavos=valor, situacao=str(payload.get("situacao") or "")[:100],
            id_origem="MANUAL:" + str(uuid4()))
        with SessionLocal.begin() as db:
            db.add(novo)
            db.flush()
            return {"registro": serialize_expense(novo)}
    except ValueError as err:
        raise HTTPException(400, str(err))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", 5000)))