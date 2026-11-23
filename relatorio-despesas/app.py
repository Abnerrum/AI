"""Núcleo Service | Relatório web de despesas.

Dados persistidos em MySQL, PostgreSQL ou SQLite; planilhas XLSX originais também
são guardadas no banco junto com as despesas importadas.
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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from openpyxl import load_workbook
from sqlalchemy import BigInteger, Date, DateTime, Integer, LargeBinary, String, Text, create_engine, select, func
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from urllib.parse import quote
import urllib.request as _url_req
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).parent
SHEETS_CSV_URL = os.getenv("SHEETS_CSV_URL", "https://docs.google.com/spreadsheets/d/1Q7SEEYhjRKY2Ro1eLPQh0fvXVbNj7ehyqc4OkM4lzOA/export?format=csv&gid=1901102031")
CLARA_CSV_URL = os.getenv("CLARA_CSV_URL", "https://docs.google.com/spreadsheets/d/1Q7SEEYhjRKY2Ro1eLPQh0fvXVbNj7ehyqc4OkM4lzOA/export?format=csv&gid=1901102029")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT / 'dados' / 'despesas.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

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


class IdentificacaoUso(Base):
    """Complemento de rastreabilidade, independente das despesas financeiras."""
    __tablename__ = "identificacoes_uso"
    despesa_pk: Mapped[int] = mapped_column(Integer, primary_key=True)
    responsavel: Mapped[str] = mapped_column(String(255), default="")
    material_utilizado: Mapped[str] = mapped_column(Text, default="")
    referencia_os: Mapped[str] = mapped_column(String(255), default="")
    observacoes: Mapped[str] = mapped_column(Text, default="")
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

class PessoaFonte(Base):
    """Titular informado pela fonte Clara; NÃO equivale ao consumidor/usuário comprovado."""
    __tablename__ = "pessoas_fonte"
    id_origem: Mapped[str] = mapped_column(String(240), primary_key=True)
    titular_cartao: Mapped[str] = mapped_column(String(255), default="")
    descricao_origem: Mapped[str] = mapped_column(Text, default="")
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FonteDados(Base):
    __tablename__ = "fontes_dados"
    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    login: Mapped[str] = mapped_column(String(255), default="")
    senha: Mapped[str] = mapped_column(String(255), default="")
    ativo: Mapped[int] = mapped_column(Integer, default=1)
    ultima_sync: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ArquivoExcel(Base):
    __tablename__ = "arquivos_excel"
    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    conteudo: Mapped[bytes] = mapped_column(
        LargeBinary().with_variant(LONGBLOB(), "mysql"), nullable=False
    )
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


def import_records(file_name, stream, original_file=None):
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
        original_digest = hashlib.sha256(original_file).hexdigest() if original_file is not None else None
        original_name = file_name.replace("\\", "/").rsplit("/", 1)[-1][:255]
        original_already_saved = False
        with SessionLocal.begin() as db:
            for i in range(0, len(unique), 500):
                chunk = list(unique.values())[i:i+500]
                if engine.dialect.name == "postgresql":
                    stmt = pg_insert(Despesa).values(chunk).on_conflict_do_nothing(index_elements=["chave"])
                elif engine.dialect.name == "sqlite":
                    stmt = sqlite_insert(Despesa).values(chunk).on_conflict_do_nothing(index_elements=["chave"])
                elif engine.dialect.name == "mysql":
                    stmt = mysql_insert(Despesa).values(chunk)
                    stmt = stmt.on_duplicate_key_update(chave=stmt.inserted.chave)
                else:
                    raise RuntimeError(f"Banco de dados não suportado: {engine.dialect.name}")
                db.execute(stmt)
            if original_file is not None:
                original_already_saved = db.scalar(
                    select(ArquivoExcel.pk).where(ArquivoExcel.sha256 == original_digest)
                ) is not None
                values = {
                    "nome": original_name,
                    "sha256": original_digest,
                    "tamanho_bytes": len(original_file),
                    "conteudo": original_file,
                }
                if engine.dialect.name == "postgresql":
                    stmt = pg_insert(ArquivoExcel).values(**values).on_conflict_do_nothing(index_elements=["sha256"])
                elif engine.dialect.name == "sqlite":
                    stmt = sqlite_insert(ArquivoExcel).values(**values).on_conflict_do_nothing(index_elements=["sha256"])
                elif engine.dialect.name == "mysql":
                    stmt = mysql_insert(ArquivoExcel).values(**values)
                    stmt = stmt.on_duplicate_key_update(sha256=stmt.inserted.sha256)
                else:
                    raise RuntimeError(f"Banco de dados não suportado: {engine.dialect.name}")
                db.execute(stmt)
        return {"analisadas": len(candidates), "duplicadas_na_planilha": len(candidates) - len(unique),
                "ignoradas": ignored, "erros_amostra": errors, "total_no_banco": count_records(),
                "arquivo_original_guardado": original_file is not None,
                "arquivo_original_ja_existia": original_already_saved}
    finally:
        if workbook:
            workbook.close()



def sync_google_sheets_rows(stream):
    """Merge the BI_GRAFICOS sheet into PostgreSQL/SQLite using Origem + ID origem.

    New rows are inserted and edits to existing source IDs are updated in place.
    Entries removed from the sheet are intentionally not deleted from the database.
    """
    rows, mapping, workbook = parse_uploaded_file("google-sheets.csv", stream)
    candidates, errors, ignored = {}, [], 0
    try:
        for line_number, row in enumerate(rows, start=2):
            if line_number > 100002:
                raise ValueError("Máximo de 100.000 linhas por arquivo.")
            if not row or not any(x is not None and str(x).strip() for x in row):
                continue
            try:
                payload = row_to_expense(row, mapping, line_number)
                if payload is None:
                    ignored += 1
                    continue
                unique_id = (payload["origem"], payload["id_origem"]) if payload["id_origem"] else ("hash", payload["chave"])
                candidates[unique_id] = payload
            except (ValueError, TypeError) as exc:
                if len(errors) < 8:
                    errors.append(f"Linha {line_number}: {str(exc)}")
        if not candidates:
            raise ValueError("A planilha BI_GRAFICOS não possui lançamentos válidos para incluir.")

        added = updated = 0
        with SessionLocal.begin() as db:
            existing = db.scalars(select(Despesa)).all()
            by_id = {(r.origem, r.id_origem): r for r in existing if r.id_origem}
            by_hash = {r.chave: r for r in existing}
            fields = ("chave", "data", "categoria", "descricao", "placa", "atendimento", "origem", "fornecedor", "valor_centavos", "situacao", "id_origem")
            for payload in candidates.values():
                key = (payload["origem"], payload["id_origem"])
                target = by_id.get(key) if payload["id_origem"] else None
                if target is None:
                    target = by_hash.get(payload["chave"])
                if target is not None:
                    if any(getattr(target, name) != payload[name] for name in fields):
                        collision = by_hash.get(payload["chave"])
                        if collision is not None and collision is not target:
                            if len(errors) < 8:
                                errors.append("Atualização ignorada por conflito entre identificadores.")
                            continue
                        old_hash = target.chave
                        for name in fields:
                            setattr(target, name, payload[name])
                        if old_hash != payload["chave"]:
                            by_hash.pop(old_hash, None)
                        by_hash[payload["chave"]] = target
                        updated += 1
                else:
                    target = Despesa(**payload)
                    db.add(target)
                    by_hash[payload["chave"]] = target
                    if payload["id_origem"]:
                        by_id[key] = target
                    added += 1
        return {"analisadas": len(candidates), "novas": added, "atualizadas": updated,
                "ignoradas": ignored, "erros_amostra": errors,
                "total_no_banco": count_records()}
    finally:
        if workbook:
            workbook.close()


def count_records():
    with SessionLocal() as db:
        return db.scalar(select(func.count(Despesa.pk))) or 0


def serialize_expense(x, identificacao=None, pessoa_fonte=None):
    return {"pk": x.pk, "data": x.data.isoformat(), "categoria": x.categoria,
            "descricao": x.descricao, "placa": x.placa, "atendimento": x.atendimento,
            "origem": x.origem, "fornecedor": x.fornecedor,
            "valor": x.valor_centavos / 100, "situacao": x.situacao, "id": x.id_origem,
            "responsavel_uso": identificacao.responsavel if identificacao else "",
            "material_utilizado": identificacao.material_utilizado if identificacao else "",
            "referencia_os": identificacao.referencia_os if identificacao else "",
            "observacoes_identificacao": identificacao.observacoes if identificacao else "",
            "titular_cartao_fonte": pessoa_fonte.titular_cartao if pessoa_fonte else "",
            "descricao_origem_fonte": pessoa_fonte.descricao_origem if pessoa_fonte else ""}


def authenticated(request: Request):
    return request.session.get("authenticated") is True


def require_auth(request: Request):
    if not authenticated(request):
        raise HTTPException(401, "Faça login para acessar os dados.")


def require_persistent_storage():
    # Render gratuito tem disco efêmero. Nunca permita uploads persistidos em SQLite online.
    if os.environ.get("COOKIE_SECURE") == "1" and engine.dialect.name == "sqlite":
        raise HTTPException(503, "Configure DATABASE_URL com MySQL ou PostgreSQL persistente antes de adicionar despesas na hospedagem.")


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
        identificacoes = {r.despesa_pk: r for r in db.scalars(select(IdentificacaoUso)).all()}
        pessoas_fonte = {r.id_origem: r for r in db.scalars(select(PessoaFonte)).all()}
        return {"registros": [serialize_expense(
            x, identificacoes.get(x.pk), pessoas_fonte.get(x.id_origem)) for x in records],
                "total": len(records),
                "storage_ready": not (os.environ.get("COOKIE_SECURE") == "1" and engine.dialect.name == "sqlite")}


@app.post("/api/identificacoes/{pk}")
async def salvar_identificacao(pk: int, request: Request):
    """Identifica quem consumiu alimentação ou quem usou qual material de OS.

    Combustível e frota continuam rastreados pela placa, fora deste controle.
    A despesa original, valores e classificação financeira não são alterados.
    """
    require_auth(request)
    require_csrf(request)
    require_persistent_storage()
    try:
        payload = await request.json()
    except (ValueError, TypeError):
        raise HTTPException(400, "Dados da identificação inválidos.")
    if not isinstance(payload, dict):
        raise HTTPException(400, "Envie um objeto de identificação.")

    field_limits = {"responsavel_uso": 255, "material_utilizado": 1000,
                    "referencia_os": 255, "observacoes_identificacao": 1000}
    values = {}
    for name, limit in field_limits.items():
        raw = payload.get(name, "")
        if raw is not None and not isinstance(raw, str):
            raise HTTPException(400, f"Campo {name} inválido.")
        value = (raw or "").strip()
        if len(value) > limit:
            raise HTTPException(400, f"Campo {name} excede o limite de {limit} caracteres.")
        values[name] = value

    with SessionLocal.begin() as db:
        despesa = db.get(Despesa, pk)
        if not despesa:
            raise HTTPException(404, "Despesa não encontrada.")
        if despesa.categoria not in ("Alimentação", "Material de OS"):
            raise HTTPException(400, "Somente Alimentação e Material de OS exigem identificação pessoal.")
        item = db.get(IdentificacaoUso, pk)
        if item is None:
            item = IdentificacaoUso(despesa_pk=pk)
            db.add(item)
        item.responsavel = values["responsavel_uso"]
        item.material_utilizado = values["material_utilizado"] if despesa.categoria == "Material de OS" else ""
        item.referencia_os = values["referencia_os"] if despesa.categoria == "Material de OS" else ""
        item.observacoes = values["observacoes_identificacao"]
        item.atualizado_em = datetime.now(timezone.utc)

    return {"status": "salvo", "despesa_pk": pk}


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
    try:
        content = await file.read(20 * 1024 * 1024 + 1)
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(413, "Arquivo muito grande: limite de 20 MB.")
        before = count_records()
        result = import_records(
            file.filename,
            io.BytesIO(content),
            original_file=content if Path(file.filename).suffix.lower() == ".xlsx" else None,
        )
    except ValueError as err:
        raise HTTPException(400, str(err))
    finally:
        await file.close()
    result["novas"] = result["total_no_banco"] - before
    return {"resultado": result}

@app.get("/api/excel-files")
def list_excel_files(request: Request):
    require_auth(request)
    with SessionLocal() as db:
        files = db.scalars(select(ArquivoExcel).order_by(ArquivoExcel.criado_em.desc())).all()
        return {"arquivos": [
            {"id": item.pk, "nome": item.nome, "tamanho_bytes": item.tamanho_bytes,
             "criado_em": item.criado_em.isoformat() if item.criado_em else None}
            for item in files
        ]}

@app.get("/api/excel-files/{file_id}")
def download_excel_file(file_id: int, request: Request):
    require_auth(request)
    with SessionLocal() as db:
        item = db.get(ArquivoExcel, file_id)
        if item is None:
            raise HTTPException(404, "Arquivo Excel não encontrado.")
        name = quote(item.nome)
        return Response(
            content=item.conteudo,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{name}"},
        )


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


def serialize_fonte(f: FonteDados):
    return {
        "pk": f.pk, "nome": f.nome, "url": f.url, "login": f.login,
        "tem_senha": bool(f.senha), "ativo": bool(f.ativo),
        "ultima_sync": f.ultima_sync.isoformat() if f.ultima_sync else None,
        "criado_em": f.criado_em.isoformat() if f.criado_em else None,
    }


@app.get("/api/fontes")
def list_fontes(request: Request):
    require_auth(request)
    with SessionLocal() as db:
        rows = db.scalars(select(FonteDados).order_by(FonteDados.criado_em.desc())).all()
        return {"fontes": [serialize_fonte(f) for f in rows]}


@app.post("/api/fontes", status_code=201)
async def create_fonte(request: Request):
    require_auth(request)
    require_csrf(request)
    payload = await request.json()
    nome = str(payload.get("nome") or "").strip()[:255]
    url = str(payload.get("url") or "").strip()[:2048]
    login = str(payload.get("login") or "").strip()[:255]
    senha = str(payload.get("senha") or "").strip()[:255]
    if not nome or not url:
        raise HTTPException(400, "Nome e URL são obrigatórios.")
    fonte = FonteDados(nome=nome, url=url, login=login, senha=senha)
    with SessionLocal.begin() as db:
        db.add(fonte)
        db.flush()
        return {"fonte": serialize_fonte(fonte)}


@app.delete("/api/fontes/{pk}")
async def delete_fonte(pk: int, request: Request):
    require_auth(request)
    require_csrf(request)
    with SessionLocal.begin() as db:
        f = db.get(FonteDados, pk)
        if not f:
            raise HTTPException(404, "Fonte não encontrada.")
        db.delete(f)
    return {"ok": True}


@app.post("/api/fontes/{pk}/sync")
async def sync_fonte_pk(pk: int, request: Request):
    require_auth(request)
    require_csrf(request)
    require_persistent_storage()
    with SessionLocal() as db:
        fonte = db.get(FonteDados, pk)
        if not fonte:
            raise HTTPException(404, "Fonte não encontrada.")
        url, login, senha, nome = fonte.url, fonte.login, fonte.senha, fonte.nome
    try:
        import httpx
        auth = (login, senha) if login and senha else None
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url, auth=auth)
            resp.raise_for_status()
            content = resp.content
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Arquivo muito grande: limite de 10 MB.")
        fname = url.rstrip("/").split("/")[-1].split("?")[0] or "fonte.csv"
        if not fname.lower().endswith((".csv", ".xlsx")):
            fname = fname + ".csv"
        before = count_records()
        result = import_records(fname, io.BytesIO(content))
        result["novas"] = result["total_no_banco"] - before
        with SessionLocal.begin() as db:
            f = db.get(FonteDados, pk)
            if f:
                f.ultima_sync = datetime.now(timezone.utc)
        return {"resultado": result, "fonte": nome}
    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(400, str(err))
    except Exception as err:
        raise HTTPException(502, f"Erro ao buscar '{nome}': {str(err)[:200]}")



def sincronizar_titulares_clara(stream):
    """Importa nomes da aba CLARA pela chave original, sem atribuir uso ou consumo."""
    raw = stream.read().decode("utf-8-sig")
    if raw.lstrip().lower().startswith(("<html", "<!doctype html")):
        raise ValueError("Acesso ao CSV Clara indisponível.")
    leitor = csv.DictReader(io.StringIO(raw))
    if not leitor.fieldnames or "Identificador único" not in leitor.fieldnames or "Responsável" not in leitor.fieldnames:
        raise ValueError("A aba CLARA não possui as colunas de identificação esperadas.")
    registros = {}
    for linha in leitor:
        uid = str(linha.get("Identificador único") or "").strip()
        if not uid:
            continue
        titular = " ".join(str(linha.get("Responsável") or "").split())
        descricao = str(linha.get("Descrição") or "").strip()
        registros["CLARA:" + uid] = (titular[:255], descricao[:2000])
    inseridos = atualizados = 0
    with SessionLocal.begin() as db:
        existentes = {p.id_origem: p for p in db.scalars(select(PessoaFonte)).all()}
        for chave, (titular, descricao) in registros.items():
            pessoa = existentes.get(chave)
            if pessoa is None:
                db.add(PessoaFonte(id_origem=chave, titular_cartao=titular,
                                   descricao_origem=descricao))
                inseridos += 1
            elif pessoa.titular_cartao != titular or pessoa.descricao_origem != descricao:
                pessoa.titular_cartao = titular
                pessoa.descricao_origem = descricao
                pessoa.atualizado_em = datetime.now(timezone.utc)
                atualizados += 1
    return {"titulares_novos": inseridos, "titulares_atualizados": atualizados,
            "fonte_clara": len(registros)}


@app.post("/api/sync-sheets")
async def sync_sheets(request: Request):
    require_auth(request)
    require_csrf(request)
    require_persistent_storage()
    try:
        req = _url_req.Request(SHEETS_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
        with _url_req.urlopen(req, timeout=30) as resp:
            content = resp.read(10 * 1024 * 1024 + 1)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Planilha muito grande: limite de 10 MB.")
        if content.lstrip()[:20].lower().startswith((b"<!doctype html", b"<html")):
            raise ValueError("Google Sheets retornou uma página de login em vez do CSV. Configure acesso autorizado à fonte.")
        result = sync_google_sheets_rows(io.BytesIO(content))
        # Atualização complementar: nomes da Clara identificam o TITULAR do cartão.
        # Acesso indisponível não deve interromper a sincronização das despesas.
        try:
            req_clara = _url_req.Request(CLARA_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
            with _url_req.urlopen(req_clara, timeout=30) as resp:
                dados_clara = resp.read(10 * 1024 * 1024 + 1)
            if len(dados_clara) > 10 * 1024 * 1024:
                raise ValueError("CSV Clara excede o limite de 10 MB.")
            result.update(sincronizar_titulares_clara(io.BytesIO(dados_clara)))
        except Exception:
            # Sem adivinhar nomes: conservar registros já obtidos e permitir
            # que o administrador continue identificando os casos pendentes.
            result["aviso_titulares"] = "Não foi possível sincronizar os titulares da aba CLARA."
        return {"resultado": result}
    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(400, str(err))
    except Exception as err:
        raise HTTPException(502, f"Erro ao buscar planilha Google Sheets: {str(err)[:200]}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", 5000)))
