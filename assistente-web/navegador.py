"""
navegador.py - Automacao de navegador com Playwright.
Gerencia sessoes por usuario, navegacao, extracao de tabelas e preenchimento de formularios.
"""

from __future__ import annotations

import os
import json
import time
import re
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page, Browser, BrowserContext

import banco
import credenciais

# False no modo Claude (MCP): o usuario avisa no chat que fez login.
LOGIN_NO_TERMINAL = True


class Navegador:
    """Controla uma instancia do navegador para um usuario especifico."""

    def __init__(self, usuario: str):
        self.usuario = usuario
        self.storage_path = banco.criar_sessao(usuario)
        self.state_file = os.path.join(self.storage_path, "state.json")
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # --- Ciclo de vida ---

    def iniciar(self, headless: bool = False):
        """Abre o navegador. headless=False permite login manual."""
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)

        # Restaura sessao anterior se existir
        if os.path.exists(self.state_file):
            self._context = self._browser.new_context(storage_state=self.state_file)
        else:
            self._context = self._browser.new_context()

        self._page = self._context.new_page()
        banco.registrar_historico(self.usuario, "navegador_iniciado")

    def salvar_sessao(self):
        """Salva cookies e storage para reutilizar depois."""
        if self._context:
            self._context.storage_state(path=self.state_file)

    def fechar(self):
        """Fecha o navegador e salva a sessao."""
        self.salvar_sessao()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._pw = None
        banco.registrar_historico(self.usuario, "navegador_fechado")

    @property
    def pagina(self) -> Page:
        if not self._page:
            raise RuntimeError("Navegador nao iniciado. Chame iniciar() primeiro.")
        return self._page

    # --- Navegacao ---

    def abrir_url(self, url: str, esperar_ms: int = 3000):
        """Abre uma URL e espera carregar."""
        from urllib.parse import urlsplit
        partes = urlsplit(url)
        if partes.scheme not in ("http", "https") or not partes.hostname or partes.username or partes.password:
            raise ValueError("Informe uma URL http/https sem credenciais.")
        self.pagina.goto(url, wait_until="domcontentloaded")
        self.pagina.wait_for_timeout(esperar_ms)
        banco.registrar_historico(self.usuario, "abrir_url", {"url": url})
        return {"ok": True, "titulo": self.pagina.title(), "url": self.pagina.url}

    def aguardar_login(self, timeout_segundos: int = 300):
        """
        Pausa e aguarda o usuario fazer login manualmente.
        Retorna quando detecta mudanca de URL ou timeout.
        """
        if LOGIN_NO_TERMINAL:
            print("Faca login no navegador, incluindo 2FA, e volte ao terminal.")
            input("Pressione ENTER somente quando o login estiver concluido: ")
        self.salvar_sessao()
        return {"url_apos_login": self.pagina.url, "titulo": self.pagina.title(),
                "msg": "Login confirmado manualmente; valide a pagina antes de consultar."}

    def screenshot(self, caminho: str = "screenshot.png") -> str:
        """Tira screenshot da pagina atual."""
        if os.path.basename(caminho) != caminho or "/" in caminho or "\\" in caminho:
            raise ValueError("Use apenas um nome de arquivo para screenshot.")
        destino = os.path.join(self.storage_path, caminho)
        self.pagina.screenshot(path=destino)
        return destino

    # --- Extracao ---

    def extrair_tabela(self, seletor_tabela: str = "table",
                       colunas: list[str] | None = None) -> list[dict]:
        """
        Extrai dados de uma tabela HTML.
        Se 'colunas' for informado, filtra apenas essas colunas.
        """
        tabela = self._unico(self.pagina, seletor_tabela)
        headers = tabela.locator("thead th").all_inner_texts()
        tem_head = bool(headers)
        if not headers:
            headers = tabela.locator("tr").first.locator("th, td").all_inner_texts()
        headers = [h.strip() for h in headers]
        if not headers or len(set(headers)) != len(headers) or any(not h for h in headers):
            raise ValueError("Cabecalhos ausentes, vazios ou duplicados.")
        rows = tabela.locator("tr")
        linhas = []
        for i in range(rows.count()):
            row = rows.nth(i)
            if row.locator("th").count() or (not tem_head and i == 0):
                continue
            valores = row.locator("td").all_inner_texts()
            if not valores:
                continue
            if len(valores) != len(headers):
                raise ValueError("Linha com quantidade de colunas inesperada; extracao interrompida.")
            linhas.append(dict(zip(headers, [v.strip() for v in valores])))
        if colunas:
            mapa = {h.casefold(): h for h in headers}
            if any(c.casefold() not in mapa for c in colunas):
                raise ValueError("Coluna solicitada nao encontrada. Confira os cabecalhos.")
            linhas = [{c: row[mapa[c.casefold()]] for c in colunas} for row in linhas]
        return linhas

    def _unico(self, raiz, seletor):
        loc = raiz.locator(seletor)
        if loc.count() != 1:
            raise ValueError(f"Seletor deve identificar exatamente um elemento: {seletor}")
        return loc

    def extrair_com_paginacao(self, seletor_tabela: str = "table",
                              seletor_proximo: str | None = None,
                              max_paginas: int = 20,
                              colunas: list[str] | None = None) -> list[dict]:
        """
        Extrai tabela percorrendo todas as paginas.
        seletor_proximo: seletor CSS do botao 'Proximo' ou 'Next'.
        """
        if not isinstance(max_paginas, int) or not 1 <= max_paginas <= 1000:
            raise ValueError("max_paginas deve estar entre 1 e 1000.")
        todos, vistas = [], set()
        for pag in range(max_paginas):
            tabela = self._unico(self.pagina, seletor_tabela)
            assinatura = tabela.inner_text()
            if assinatura in vistas:
                raise RuntimeError("Paginacao repetiu uma pagina; extracao interrompida.")
            vistas.add(assinatura)
            todos.extend(self.extrair_tabela(seletor_tabela, colunas))
            if not seletor_proximo:
                return todos
            candidatos = self.pagina.locator(seletor_proximo)
            if candidatos.count() == 0:
                return todos
            btn = self._unico(self.pagina, seletor_proximo)
            if btn.is_disabled() or btn.get_attribute("aria-disabled") == "true" or any(c in (btn.get_attribute("class") or "").split() for c in ("disabled", "desabilitado")):
                return todos
            if pag + 1 == max_paginas:
                raise RuntimeError("Limite de paginas atingido; aumente max_paginas. Relatorio incompleto nao foi salvo.")
            btn.click()
            self.pagina.wait_for_function(
                "([sel, anterior]) => {const el=document.querySelector(sel); return el && el.innerText !== anterior;}",
                arg=[seletor_tabela, assinatura], timeout=15000)
        return todos

    # --- Preenchimento de formularios ---

    def preencher_formulario(self, campos: dict[str, str], seletor_form: str = "form"):
        """
        Preenche campos de um formulario SEM submeter.
        campos: {"seletor_campo": "valor", ...}
        Retorna previa dos valores preenchidos.
        """
        form = self._unico(self.pagina, seletor_form)
        if not form:
            raise ValueError(f"Formulario nao encontrado: {seletor_form}")

        previa = {}
        for seletor, valor in campos.items():
            campo = self._unico(form, seletor)
            valor = str(valor)
            if campo.get_attribute("type") == "password":
                raise ValueError("Senhas devem ser preenchidas manualmente no navegador.")

            tag = campo.evaluate("el => el.tagName.toLowerCase()")
            tipo = campo.get_attribute("type") or ""

            if tag == "select":
                campo.select_option(value=valor)
            elif tag == "textarea" or tipo in ("text", "email", "number", "tel", "search", ""):
                campo.fill(valor)
            elif tipo == "checkbox":
                if valor.lower() in ("true", "1", "sim"):
                    campo.check()
                else:
                    campo.uncheck()
            elif tipo == "radio":
                campo.check()
            else:
                campo.fill(valor)

            previa[seletor] = campo.is_checked() if tipo in ("checkbox", "radio") else campo.input_value()

        banco.registrar_historico(
            self.usuario, "preencher_formulario",
            {"campos_preenchidos": len(previa)}
        )
        return previa

    def validar_previa(self, campos, seletor_form):
        form = self._unico(self.pagina, seletor_form)
        for seletor, esperado in campos.items():
            campo = self._unico(form, seletor)
            valor = campo.is_checked() if campo.get_attribute("type") in ("checkbox", "radio") else campo.input_value()
            if valor != esperado:
                raise ValueError("Formulario alterado desde a previa; preencha e revise novamente.")
        if not form.evaluate("el => el.checkValidity()"):
            raise ValueError("Formulario possui campos invalidos ou obrigatorios vazios.")

    def submeter_formulario(self, seletor_botao: str = "button[type=submit]"):
        """Submete o formulario apos confirmacao do usuario."""
        btn = self._unico(self.pagina, seletor_botao)
        if not btn:
            raise ValueError(f"Botao nao encontrado: {seletor_botao}")
        btn.click()
        self.pagina.wait_for_timeout(3000)
        resultado = {"url_apos": self.pagina.url, "titulo": self.pagina.title()}
        banco.registrar_historico(self.usuario, "submeter_formulario", resultado=json.dumps(resultado))
        return resultado

    def verificar_sucesso(self, seletor_sucesso: str | None = None,
                          texto_sucesso: str | None = None) -> dict:
        """Verifica se a acao foi concluida com sucesso."""
        encontrou = False
        detalhes = ""

        if seletor_sucesso:
            elem = self.pagina.locator(seletor_sucesso)
            if elem.count() == 1 and elem.is_visible():
                encontrou = True
                detalhes = elem.inner_text().strip()

        if texto_sucesso and not encontrou:
            conteudo = self.pagina.inner_text("body")
            if texto_sucesso.lower() in conteudo.lower():
                encontrou = True
                detalhes = texto_sucesso

        return {"sucesso": encontrou, "detalhes": detalhes}

    # --- Login automatico (senha fica no cofre do Windows) ---

    def fazer_login(self, url: str | None = None, seletor_usuario: str | None = None,
                    seletor_senha: str | None = None, seletor_botao: str | None = None,
                    trocar: bool = False):
        """Preenche usuario e senha guardados para o site. Na primeira vez abre uma
        janela local para o usuario digitar. Nunca devolve a senha."""
        from urllib.parse import urlsplit
        if url:
            self.abrir_url(url, 1500)
        site = urlsplit(self.pagina.url).hostname
        if not site:
            raise ValueError("Abra a pagina de login do site antes (abrir_url).")
        if trocar:
            credenciais.excluir(site)
        cred = credenciais.obter(site)
        if not cred:
            cred = credenciais.pedir_na_tela(site)
            if not cred:
                raise ValueError("Login cancelado pelo usuario na janela.")
            credenciais.salvar(site, *cred)
        usuario, senha = cred

        senha_loc = self._campo_login(seletor_senha, "senha")
        user_loc = self._campo_login(seletor_usuario, "usuario")
        if senha_loc is None:
            # Login em duas telas: usuario primeiro, depois senha.
            if user_loc is None:
                return {"login": "sem_formulario", "url": self.pagina.url,
                        "msg": "Nenhum campo de login visivel; talvez ja esteja logado."}
            user_loc.fill(usuario)
            user_loc.press("Enter")
            self.pagina.wait_for_timeout(2500)
            senha_loc = self._campo_login(seletor_senha, "senha")
            if senha_loc is None:
                raise RuntimeError("Campo de senha nao apareceu apos informar o usuario.")
        elif user_loc is not None:
            user_loc.fill(usuario)
        senha_loc.fill(senha)
        if seletor_botao:
            self._unico(self.pagina, seletor_botao).click()
        else:
            senha_loc.press("Enter")
        try:
            self.pagina.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        self.pagina.wait_for_timeout(1000)

        resultado = {"site": site, "url": self.pagina.url, "titulo": self.pagina.title()}
        if self._campo_login(None, "senha") is not None:
            resultado |= {"login": "falhou_ou_pendente",
                          "msg": "Campo de senha ainda visivel. Se a senha mudou, use trocar=true."}
        elif self.pagina.locator("input[autocomplete=one-time-code]").count() or re.search(
                r"c[oó]digo de|verifica[cç][aã]o|two.?factor|2fa|authenticator", self.pagina.inner_text("body"), re.I):
            resultado |= {"login": "aguardando_codigo",
                          "msg": "Peca ao usuario para digitar o codigo no navegador e avisar; depois chame aguardar_login."}
        else:
            resultado["login"] = "ok"
            self.salvar_sessao()
        banco.registrar_historico(self.usuario, "fazer_login", {"site": site})
        return resultado

    def _campo_login(self, seletor, tipo):
        if seletor:
            loc = self.pagina.locator(seletor)
            return loc.first if loc.count() else None
        achou = self.pagina.evaluate("""tipo => {
            const vis = e => e.offsetParent !== null && !e.disabled && !e.readOnly;
            document.querySelectorAll('[data-aw-login=' + tipo + ']').forEach(e => e.removeAttribute('data-aw-login'));
            const senha = [...document.querySelectorAll('input[type=password]')].find(vis);
            let alvo = senha;
            if (tipo === 'usuario') {
                const raiz = (senha && senha.form) || document;
                alvo = [...raiz.querySelectorAll('input')].find(e => vis(e) &&
                    ['text', 'email', 'tel', ''].includes((e.getAttribute('type') || '').toLowerCase()));
            }
            if (!alvo) return false;
            alvo.setAttribute('data-aw-login', tipo);
            return true;
        }""", tipo)
        return self.pagina.locator(f"[data-aw-login={tipo}]").first if achou else None

    # --- Acoes gerais (pouco texto devolvido para economizar tokens) ---

    def listar_elementos(self, max_itens: int = 60, filtro: str | None = None):
        """Lista botoes, links e campos visiveis com seletores curtos [data-aw=N]."""
        itens = self.pagina.evaluate("""([max, filtro]) => {
            const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 &&
                getComputedStyle(e).visibility !== 'hidden'; };
            const sel = 'a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [role=tab], [role=menuitem], [onclick]';
            const f = filtro ? filtro.toLowerCase() : null;
            document.querySelectorAll('[data-aw]').forEach(e => e.removeAttribute('data-aw'));
            const out = []; let n = 0;
            for (const e of document.querySelectorAll(sel)) {
                if (!vis(e)) continue;
                const tag = e.tagName.toLowerCase();
                const tipo = e.getAttribute('type') || '';
                let txt = ((tag === 'select' ? '' : e.innerText) || e.getAttribute('aria-label') || e.placeholder || e.title || e.name || e.id || '').trim().replace(/\\s+/g, ' ').slice(0, 60);
                if (tag === 'input' && tipo !== 'password' && e.value && !['submit', 'button'].includes(tipo)) txt += ' =' + e.value.slice(0, 30);
                if (f && !txt.toLowerCase().includes(f)) continue;
                e.setAttribute('data-aw', ++n);
                const item = {s: '[data-aw="' + n + '"]', t: tag + (tipo ? ':' + tipo : ''), x: txt};
                if (tag === 'select') item.op = [...e.options].slice(0, 15).map(o => o.text.trim());
                out.push(item);
                if (out.length >= max) break;
            }
            return out;
        }""", [max_itens, filtro])
        return {"url": self.pagina.url, "titulo": self.pagina.title(), "elementos": itens,
                "obs": "Seletores valem ate a pagina mudar; liste de novo apos navegar."}

    def ler_pagina(self, seletor: str = "body", max_chars: int = 3000):
        texto = re.sub(r"\n\s*\n+", "\n", self.pagina.locator(seletor).first.inner_text()).strip()
        return {"url": self.pagina.url, "titulo": self.pagina.title(), "total_chars": len(texto),
                "texto": texto[:max_chars]}

    def _depois_de_agir(self):
        try:
            self.pagina.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        self.pagina.wait_for_timeout(800)
        return {"url": self.pagina.url, "titulo": self.pagina.title()}

    def clicar(self, seletor: str | None = None, texto: str | None = None):
        if seletor:
            alvo = self._unico(self.pagina, seletor)
        elif texto:
            alvo = self.pagina.get_by_text(texto, exact=True)
            if alvo.count() != 1:
                alvo = self.pagina.get_by_text(texto)
            if alvo.count() != 1:
                raise ValueError(f"Texto encontrado {alvo.count()} vezes; use listar_elementos e um seletor.")
        else:
            raise ValueError("Informe seletor ou texto.")
        alvo.click()
        return self._depois_de_agir()

    def digitar(self, seletor: str, texto: str, enter: bool = False):
        campo = self._unico(self.pagina, seletor)
        if campo.get_attribute("type") == "password":
            raise ValueError("Senhas nao passam pelo chat: use fazer_login.")
        campo.fill(str(texto))
        if enter:
            campo.press("Enter")
            return self._depois_de_agir()
        return {"ok": True}

    def pressionar_tecla(self, tecla: str):
        self.pagina.keyboard.press(tecla)
        return self._depois_de_agir()

    def selecionar(self, seletor: str, valor: str):
        campo = self._unico(self.pagina, seletor)
        try:
            campo.select_option(label=str(valor), timeout=3000)
        except Exception:
            campo.select_option(value=str(valor))
        return {"ok": True, "selecionado": campo.evaluate("e => e.options[e.selectedIndex].text")}

    def voltar(self):
        self.pagina.go_back()
        return self._depois_de_agir()

    # --- Utilitarios ---

    def texto_da_pagina(self) -> str:
        """Retorna o texto visivel da pagina (sem HTML)."""
        return self.pagina.inner_text("body")

    def url_atual(self) -> str:
        return self.pagina.url

    def titulo_atual(self) -> str:
        return self.pagina.title()
