"""
PULSO - Recursos visuais do deck da Sprint 2
============================================
Gera os elementos graficos que o PowerPoint nao consegue desenhar bem:
o motivo de marca (linha de ECG) e o diagrama de arquitetura em camadas.

Saida: docs/evidencias/
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

EVID = Path(__file__).resolve().parents[2] / "docs" / "evidencias"
EVID.mkdir(parents=True, exist_ok=True)

NAVY = "#0A2A3B"
TEAL = "#009B98"
CORAL = "#D9452B"
AMBAR = "#B5820A"
ROXO = "#7A4FA8"
CLARO = "#EEF3F4"
CINZA = "#6B8592"


# --------------------------------------------------------------------------- #
def ecg(nome: str, cor: str, fundo: str | None, largura: float = 12.0) -> None:
    """Faixa com o traçado de ECG - motivo de marca do PULSO."""
    x = np.linspace(0, 4, 1600)
    y = np.zeros_like(x)
    for centro in (0.55, 1.55, 2.55, 3.55):
        d = x - centro
        y += -0.22 * np.exp(-((d + 0.10) ** 2) / 0.00035)     # onda Q
        y += 1.00 * np.exp(-(d ** 2) / 0.00022)               # pico R
        y += -0.35 * np.exp(-((d - 0.09) ** 2) / 0.00045)     # onda S
        y += 0.26 * np.exp(-((d - 0.30) ** 2) / 0.0035)       # onda T
        y += 0.16 * np.exp(-((d + 0.30) ** 2) / 0.0030)       # onda P

    fig, ax = plt.subplots(figsize=(largura, 1.05))
    ax.plot(x, y, color=cor, lw=3.4, solid_capstyle="round", solid_joinstyle="round")
    ax.set_xlim(0.05, 3.95)
    ax.set_ylim(-0.62, 1.28)
    ax.axis("off")
    fig.patch.set_alpha(0 if fundo is None else 1)
    if fundo:
        fig.patch.set_facecolor(fundo)
    fig.savefig(EVID / nome, dpi=200, bbox_inches="tight", pad_inches=0.04,
                transparent=fundo is None)
    plt.close(fig)
    print(f"  -> {nome}")


# --------------------------------------------------------------------------- #
def arquitetura() -> None:
    """Diagrama de camadas da arquitetura implementada."""
    fig, ax = plt.subplots(figsize=(12.4, 7.1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 104)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    def caixa(x, y, w, h, titulo, itens, cor, tam=9.0):
        """Desenha a caixa e distribui o texto a partir do topo, com folga fixa."""
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.4",
            facecolor=cor, edgecolor="none"))
        ax.text(x + w / 2, y + h - 3.2, titulo, ha="center", va="top",
                fontsize=10.0, fontweight="bold", color="white")
        # Reserva 8,2 para o titulo e 4,2 por item; a altura da caixa e sempre
        # dimensionada para caber 8,2 + (n-1)*4,2 + 3 de folga inferior.
        for i, item in enumerate(itens):
            ax.text(x + w / 2, y + h - 8.2 - i * 4.2, item, ha="center", va="top",
                    fontsize=tam, color="white", alpha=.93)

    def seta(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
            color=CINZA, lw=1.7, shrinkA=2, shrinkB=2))

    def rotulo_camada(y, texto):
        ax.text(0.5, y, texto, ha="center", va="center", fontsize=7.8,
                color=CINZA, fontweight="bold", rotation=90)

    ESQ = 6.0
    LARG = 92.0

    # ---- camada 1: origem ------------------------------------------------- #
    rotulo_camada(92.5, "ORIGEM")
    lw = (LARG - 2 * 3.0) / 3
    caixa(ESQ, 82, lw, 21, "SIH/SUS  ·  DATASUS",
          ["Internações · valor pago", "permanência · CID-10",
           "→ RELACIONAL"], TEAL)
    caixa(ESQ + lw + 3, 82, lw, 21, "CNES  ·  Ministério da Saúde",
          ["Estabelecimentos (API)", "leitos de internação",
           "→ JSON"], AMBAR)
    caixa(ESQ + 2 * (lw + 3), 82, lw, 21, "IBGE  ·  Localidades + SIDRA",
          ["Malha municipal", "população estimada",
           "→ CSV"], ROXO)

    seta(ESQ + lw / 2, 81.4, 40, 75.0)
    seta(50, 81.4, 50, 75.0)
    seta(ESQ + 2 * (lw + 3) + lw / 2, 81.4, 60, 75.0)

    # ---- camada 2: ingestão ----------------------------------------------- #
    rotulo_camada(66.5, "INGESTÃO")
    caixa(ESQ, 58, LARG, 17,
          "INGESTÃO E PROCESSAMENTO   ·   Python 3.11 · pandas",
          ["tabnet_client.py  ·  extract_sih / extract_cnes / extract_ibge  ·  transform.py",
           "integração das três fontes pelo código IBGE de 6 dígitos — nunca por nome de município"],
          NAVY)
    seta(50, 57.4, 50, 51.0)

    # ---- camada 3: armazenamento ------------------------------------------ #
    rotulo_camada(40.5, "ARMAZENAMENTO")
    caixa(ESQ, 29, LARG, 22,
          "ORACLE AUTONOMOUS DATABASE 23ai   ·   OCI Object Storage",
          ["COPY_DATA → tabelas relacionais      ·      COPY_COLLECTION → coleção JSON nativa",
           "CREATE_EXTERNAL_TABLE → CSV lido direto do Object Storage",
           "dim_municipio  +  fato_internacao_mes  ·  fato_cid_capitulo  ·  fato_uf_mes"],
          "#123B4F")
    seta(30, 28.4, 30, 24.4)
    seta(70, 28.4, 70, 24.4)

    # ---- camada 4: modelagem e consumo ------------------------------------ #
    rotulo_camada(13, "MODELAGEM E CONSUMO")
    lw2 = (LARG - 4.0) / 2
    caixa(ESQ, 3, lw2, 21, "MODELAGEM ANALÍTICA   ·   scikit-learn",
          ["K-Means (k=4) → perfil de pressão", "Índice composto → priorização",
           "Regressão linear → tendência"], TEAL, tam=8.8)
    caixa(ESQ + lw2 + 4, 3, lw2, 21, "CONSUMO",
          ["Select AI → pergunta em português", "gera e executa o SQL no banco",
           "Dashboard → painel navegável"], CORAL, tam=8.8)

    ax.text(50, -1.0, "As saídas dos modelos voltam ao banco como tabelas, "
                     "para que o Select AI possa consultá-las",
            ha="center", va="bottom", fontsize=8.2, color=CINZA, style="italic")

    fig.savefig(EVID / "a1_arquitetura_camadas.png", dpi=190,
                bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print("  -> a1_arquitetura_camadas.png")


# --------------------------------------------------------------------------- #
def fluxo_dado() -> None:
    """Percurso de um dado, da fonte até a resposta ao gestor."""
    fig, ax = plt.subplots(figsize=(12.4, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    etapas = [
        ("1", "EXTRAÇÃO", "TabNet devolve o total\nmensal do município", TEAL),
        ("2", "INTEGRAÇÃO", "Conciliação com população\ndo IBGE e leitos do CNES", AMBAR),
        ("3", "INDICADOR", "Ocupação estimada\nresulta em 105,0%", CORAL),
        ("4", "MODELO", "K-Means agrupa em\n'Rede local pressionada'", ROXO),
        ("5", "RESPOSTA", "Jundiaí aparece quando\no gestor pergunta", NAVY),
    ]
    larg, gap = 16.5, 4.2
    x0 = (100 - (len(etapas) * larg + (len(etapas) - 1) * gap)) / 2

    for i, (n, titulo, texto, cor) in enumerate(etapas):
        x = x0 + i * (larg + gap)
        ax.add_patch(FancyBboxPatch(
            (x, 22), larg, 56, boxstyle="round,pad=0.3,rounding_size=1.6",
            facecolor=CLARO, edgecolor="none"))
        # O eixo nao e quadrado (12,4 x 3,5 pol), entao um Circle sairia oval.
        # A elipse abaixo compensa a razao de aspecto e desenha um circulo real.
        from matplotlib.patches import Ellipse
        razao = (12.4 / 3.5)
        ax.add_patch(Ellipse((x + larg / 2, 68), width=5.2, height=5.2 * razao,
                             facecolor=cor, edgecolor="none", zorder=3))
        ax.text(x + larg / 2, 68, n, ha="center", va="center", fontsize=11,
                fontweight="bold", color="white", zorder=4)
        ax.text(x + larg / 2, 54, titulo, ha="center", va="center", fontsize=8.6,
                fontweight="bold", color=cor)
        ax.text(x + larg / 2, 38, texto, ha="center", va="center", fontsize=8.2,
                color=NAVY, linespacing=1.5)
        if i < len(etapas) - 1:
            ax.add_patch(FancyArrowPatch(
                (x + larg + 0.5, 50), (x + larg + gap - 0.5, 50),
                arrowstyle="-|>", mutation_scale=13, color=CINZA, lw=1.6))

    ax.text(50, 9, "Uma internação em Jundiaí em março de 2026, do registro público "
                   "à resposta em linguagem natural",
            ha="center", va="center", fontsize=8.8, color=CINZA, style="italic")

    fig.savefig(EVID / "a2_fluxo_dado.png", dpi=190, bbox_inches="tight",
                pad_inches=0.1, facecolor="white")
    plt.close(fig)
    print("  -> a2_fluxo_dado.png")


def executar() -> None:
    print("[Deck] gerando recursos visuais...")
    ecg("m1_ecg_teal.png", TEAL, None)
    ecg("m2_ecg_branco.png", "#FFFFFF", None)
    arquitetura()
    fluxo_dado()
    print("[Deck] concluido.")


if __name__ == "__main__":
    executar()
