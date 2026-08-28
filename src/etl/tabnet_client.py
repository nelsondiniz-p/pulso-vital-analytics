"""
PULSO - Cliente de extracao TabNet/DATASUS
==========================================
Projeto PULSO (Painel Unico de Leitos, Saude e Ocupacao)
Equipe Vital Analytics - Turma 1TSCOA - Challenge Oracle + FIAP 2026

O TabNet e a interface publica de tabulacao do DATASUS. Ele nao expoe uma API
REST: expoe um CGI (tabcgi.exe) que recebe um POST com os parametros de
tabulacao e devolve HTML com a tabela ja agregada.

Este modulo encapsula esse comportamento em uma interface programatica:

    tn = TabNet("sih/cnv/nisp.def")
    df = tn.tabular(linha="Municipio", coluna="Ano/mes_processamento",
                    incremento="Internacoes", n_arquivos=6)

Detalhes tecnicos tratados aqui:
  * o TabNet responde em ISO-8859-1 (latin-1), nao UTF-8;
  * o HTML usa tags <TR>/<TD> nao fechadas (HTML 3.2), o que quebra parsers
    estritos - por isso a tabela e lida por varredura tolerante;
  * numeros vem no formato brasileiro ("1.455.269", "4,7") e ausencias como "-";
  * todo filtro de categoria precisa ser enviado, mesmo quando nao usado.
"""

from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

BASE = "http://tabnet.datasus.gov.br/cgi"
UA = "Mozilla/5.0 (compatible; PULSO-ETL/1.0; projeto academico FIAP)"
TIMEOUT = 120


def _get(url: str, retries: int = 3) -> str:
    """GET com retry e decodificacao latin-1."""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("latin-1")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"Falha ao acessar {url}: {last}")


def _post(url: str, body: str, retries: int = 3) -> str:
    """POST form-urlencoded em latin-1, com retry."""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=body.encode("latin-1"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": UA,
                },
            )
            return urllib.request.urlopen(req, timeout=TIMEOUT).read().decode("latin-1")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"Falha no POST {url}: {last}")


def _clean(txt: str) -> str:
    """Remove tags, resolve entidades HTML e normaliza espacos."""
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def br_to_float(valor: str):
    """Converte numero em formato brasileiro para float. '-' e vazio viram None."""
    v = (valor or "").strip()
    if v in {"", "-", "...", "..", "0,00"} and v != "0,00":
        return None
    v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


@dataclass
class TabNet:
    """Representa um cubo (.def) do TabNet e permite tabular sobre ele."""

    definicao: str                      # ex.: "sih/cnv/nisp.def"
    linhas: list = field(default_factory=list, repr=False)
    colunas: list = field(default_factory=list, repr=False)
    incrementos: list = field(default_factory=list, repr=False)
    arquivos: list = field(default_factory=list, repr=False)
    filtros: list = field(default_factory=list, repr=False)
    titulo: str = ""

    def __post_init__(self) -> None:
        self._carregar_metadados()

    # ------------------------------------------------------------------ #
    # metadados                                                           #
    # ------------------------------------------------------------------ #
    def _carregar_metadados(self) -> None:
        """Le o formulario do .def e descobre dimensoes, medidas e periodos."""
        raw = _get(f"{BASE}/deftohtm.exe?{self.definicao}")
        self.titulo = _clean(
            (re.findall(r"<title>(.*?)</title>", raw, re.I | re.S) or [""])[0]
        )
        selects: dict[str, list[str]] = {}
        for m in re.finditer(
            r"<select[^>]*name=\"([^\"]+)\"[^>]*>(.*?)</select>", raw, re.I | re.S
        ):
            selects[m.group(1)] = re.findall(
                r"<option[^>]*value=\"([^\"]*)\"", m.group(2), re.I
            )
        self.linhas = selects.get("Linha", [])
        self.colunas = selects.get("Coluna", [])
        self.incrementos = selects.get("Incremento", [])
        self.arquivos = selects.get("Arquivos", [])
        # Todo filtro de categoria comeca com "S" (ex.: SMunicipio, SSexo)
        self.filtros = [k for k in selects if k.startswith("S") and k != "Selecao"]

    def _resolver(self, alvo: str, opcoes: list[str], rotulo: str) -> str:
        """Aceita nome aproximado (sem acento / case-insensitive) e resolve."""
        def norm(s: str) -> str:
            s = s.lower()
            for a, b in zip("aaaaeeiooouuc", "áàâãéêíóôõúüç"):
                s = s.replace(b, a)
            return re.sub(r"[^a-z0-9]", "", s)

        alvo_n = norm(alvo)
        for o in opcoes:
            if norm(o) == alvo_n:
                return o
        for o in opcoes:
            if alvo_n in norm(o):
                return o
        raise ValueError(
            f"{rotulo} '{alvo}' nao encontrado. Opcoes: {opcoes}"
        )

    # ------------------------------------------------------------------ #
    # tabulacao                                                           #
    # ------------------------------------------------------------------ #
    def tabular(
        self,
        linha: str,
        incremento: str,
        coluna: str = "--Nao-Ativa--",
        n_arquivos: int = 6,
        arquivos: list | None = None,
        filtros: dict | None = None,
    ) -> tuple[list, list]:
        """Executa a tabulacao e devolve (cabecalho, linhas).

        Args:
            linha: dimensao das linhas (ex.: "Municipio").
            incremento: medida (ex.: "Internacoes", "Valor_total").
            coluna: dimensao das colunas ou "--Nao-Ativa--".
            n_arquivos: quantos periodos mais recentes usar.
            arquivos: lista explicita de periodos (sobrepoe n_arquivos).
            filtros: {"SCapitulo_CID-10": "10"} para restringir categorias.
        """
        linha_v = self._resolver(linha, self.linhas, "Linha")
        incr_v = self._resolver(incremento, self.incrementos, "Incremento")
        col_v = (
            "--Não-Ativa--"
            if coluna in ("--Nao-Ativa--", None, "")
            else self._resolver(coluna, self.colunas, "Coluna")
        )
        arqs = arquivos if arquivos else self.arquivos[:n_arquivos]
        filtros = filtros or {}

        pares = [("Linha", linha_v), ("Coluna", col_v), ("Incremento", incr_v)]
        pares += [("Arquivos", a) for a in arqs]
        for f in self.filtros:
            pares.append((f, filtros.get(f, "TODAS_AS_CATEGORIAS__")))
        for i in range(1, 15):
            pares.append((f"pesqmes{i}", "Digite o texto e ache facil"))
        pares += [("formato", "table"), ("mostre", "sim"), ("zeradas", "exibirlz")]

        body = "&".join(
            f"{urllib.parse.quote_plus(k, encoding='latin-1')}="
            f"{urllib.parse.quote_plus(str(v), encoding='latin-1')}"
            for k, v in pares
        )
        raw = _post(f"{BASE}/tabcgi.exe?{self.definicao}", body)
        return self._parse_tabela(raw)

    @staticmethod
    def _parse_tabela(raw: str) -> tuple[list, list]:
        """Le a tabela do HTML 3.2 do TabNet (tags nao fechadas).

        Estrategia: fatiar o documento em blocos <TR> e, dentro de cada bloco,
        fatiar em celulas <TD>/<TH>. Isso e imune a tags sem fechamento.
        """
        corpo = raw
        ini = corpo.upper().find("<THEAD")
        if ini == -1:
            ini = corpo.upper().find("<TR")
        corpo = corpo[ini:]
        fim = corpo.upper().find("</TABLE")
        if fim > 0:
            corpo = corpo[:fim]

        blocos = re.split(r"<TR[^>]*>", corpo, flags=re.I)[1:]
        cabecalho: list[str] = []
        linhas: list[list[str]] = []
        for bloco in blocos:
            # descarta rodape
            if re.search(r'class="rodape', bloco, re.I):
                continue
            celulas = re.split(r"<T[DH][^>]*>", bloco, flags=re.I)[1:]
            celulas = [_clean(c) for c in celulas]
            celulas = [c for c in celulas if c != ""] if not cabecalho else celulas
            if not celulas:
                continue
            if not cabecalho and re.search(r"<TH", bloco, re.I):
                cabecalho = celulas
                continue
            if re.search(r"<TH", bloco, re.I):
                continue
            linhas.append(celulas)
        return cabecalho, linhas


# ---------------------------------------------------------------------- #
# utilitarios de dominio                                                  #
# ---------------------------------------------------------------------- #
def separar_codigo_nome(rotulo: str) -> tuple[str, str]:
    """'350010 ADAMANTINA' -> ('350010', 'ADAMANTINA')."""
    m = re.match(r"^\s*(\d{2,7})\s+(.*)$", rotulo)
    if m:
        return m.group(1), m.group(2).strip()
    return "", rotulo.strip()


def periodo_de_arquivo(nome: str) -> str:
    """'nisp2506.dbf' -> '2025-06'."""
    m = re.search(r"(\d{2})(\d{2})\.dbf$", nome, re.I)
    if not m:
        return nome
    return f"20{m.group(1)}-{m.group(2)}"
