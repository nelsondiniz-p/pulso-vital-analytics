"""
PULSO - Geracao das evidencias visuais
======================================
Produz os graficos usados no PPT da Sprint 2 e no dashboard.

Identidade visual do PULSO (definida na Sprint 1): a linha de ECG como metafora
dos sinais vitais do sistema de saude.
    teal navy  #0A2A3B   estrutura e texto
    teal       #0E8C8B   medida principal
    coral      #E8552D   alerta / criticidade
    ambar      #F2A900   atencao
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"
EVID = BASE / "docs" / "evidencias"
EVID.mkdir(parents=True, exist_ok=True)

NAVY, TEAL, CORAL, AMBAR = "#0A2A3B", "#0E8C8B", "#E8552D", "#F2A900"
CINZA = "#8FA3AD"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": CINZA,
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})

MIL = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))


def _titulo(ax, titulo: str, subtitulo: str = "") -> None:
    ax.set_title(titulo, fontsize=13, fontweight="bold", color=NAVY,
                 loc="left", pad=18 if subtitulo else 10)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes,
                fontsize=9, color=CINZA, va="bottom")


def _salvar(fig, nome: str) -> None:
    caminho = EVID / nome
    fig.savefig(caminho)
    plt.close(fig)
    print(f"  -> {nome}")


# --------------------------------------------------------------------------- #
def g1_serie_temporal() -> None:
    fato = pd.read_csv(PROC / "fato_internacao_mes.csv")
    serie = fato.groupby("periodo")["internacoes"].sum()
    x = np.arange(len(serie))
    coef = np.polyfit(x, serie.values, 1)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(serie.index, serie.values, color=TEAL, lw=2.4, marker="o",
            ms=5, mfc="white", mew=1.8, label="Internações/mês")
    ax.plot(serie.index, coef[0] * x + coef[1], color=CORAL, lw=1.6, ls="--",
            label=f"Tendência ({coef[0]:+,.0f}/mês)")
    ax.fill_between(serie.index, serie.values, serie.values.min() * 0.97,
                    color=TEAL, alpha=0.08)
    ax.set_ylim(serie.values.min() * 0.95, serie.values.max() * 1.04)
    ax.yaxis.set_major_formatter(MIL)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.legend(frameon=False, fontsize=9)
    _titulo(ax, "Internações SUS no estado de São Paulo",
            f"12 meses  ·  {serie.sum():,.0f} internações".replace(",", "."))
    ax.grid(axis="y", color=CINZA, alpha=0.2)
    _salvar(fig, "g1_serie_temporal_sp.png")


def g2_ranking_criticidade(n: int = 15) -> None:
    rk = pd.read_csv(PROC / "mv_ranking_criticidade.csv").head(n).iloc[::-1]
    cores = [CORAL if a == "Crítico" else AMBAR if a == "Atenção" else TEAL
             for a in rk["alerta_capacidade"]]

    fig, ax = plt.subplots(figsize=(9, 5.6))
    barras = ax.barh(rk["municipio"], rk["indice_criticidade"], color=cores, height=0.72)
    for b, v, o in zip(barras, rk["indice_criticidade"], rk["ocupacao_estimada_pct"]):
        ax.text(v + 0.8, b.get_y() + b.get_height() / 2,
                f"{v:.1f}  ({o:.0f}% ocup.)", va="center", fontsize=8, color=NAVY)
    ax.set_xlim(0, rk["indice_criticidade"].max() * 1.25)
    ax.set_xlabel("Índice de criticidade (0–100)", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    _titulo(ax, f"Top {n} municípios por pressão assistencial",
            "Vermelho = ocupação ≥ 100%  ·  âmbar = ≥ 85%")
    ax.grid(axis="x", color=CINZA, alpha=0.2)
    _salvar(fig, "g2_ranking_criticidade.png")


def g3_perfil_cid(n: int = 10) -> None:
    cid = pd.read_csv(PROC / "fato_cid_capitulo.csv")
    top = cid.groupby("capitulo_cid10")["internacoes"].sum().nlargest(n).iloc[::-1]
    rotulos = [t.split(". ", 1)[-1][:44] for t in top.index]
    total = cid["internacoes"].sum()

    fig, ax = plt.subplots(figsize=(9, 5))
    cores = [CORAL if i >= n - 3 else TEAL for i in range(n)]
    barras = ax.barh(rotulos, top.values, color=cores, height=0.72)
    for b, v in zip(barras, top.values):
        ax.text(v * 1.01, b.get_y() + b.get_height() / 2,
                f"{v/1000:,.0f}k ({v/total*100:.1f}%)", va="center",
                fontsize=8, color=NAVY)
    ax.set_xlim(0, top.values.max() * 1.2)
    ax.xaxis.set_major_formatter(MIL)
    ax.set_xlabel("Internações em 12 meses", fontsize=9)
    ax.tick_params(axis="y", labelsize=8.5)
    _titulo(ax, "Perfis de atendimento que mais pressionam a rede",
            "Capítulos CID-10  ·  estado de São Paulo")
    ax.grid(axis="x", color=CINZA, alpha=0.2)
    _salvar(fig, "g3_perfil_cid10.png")


def g4_clusters() -> None:
    cl = pd.read_csv(PROC / "mv_clusters_municipio.csv")
    paleta = {"Polo regional sob pressão": CORAL, "Rede local pressionada": AMBAR,
              "Sede de hospital regional": "#7A4FA8", "Rede local equilibrada": TEAL,
              "Rede com folga": TEAL, "Capacidade ociosa": CINZA}

    fig, ax = plt.subplots(figsize=(9, 5.4))
    limite_x = float(cl["leitos_sus_10k_hab"].quantile(0.97))
    ax.set_xlim(0, limite_x)
    ax.set_ylim(-4, max(120, cl["ocupacao_estimada_pct"].quantile(0.99) + 8))
    for perfil, grupo in cl.groupby("perfil_cluster"):
        ax.scatter(grupo["leitos_sus_10k_hab"], grupo["ocupacao_estimada_pct"],
                   s=np.clip(grupo["internacoes_12m"] / 90, 12, 320),
                   color=paleta.get(perfil, CINZA), alpha=0.62,
                   edgecolor="white", linewidth=0.6,
                   label=f"{perfil} (n={len(grupo)})")
    ax.axhline(100, color=CORAL, ls="--", lw=1.2)
    ax.text(limite_x * 0.985, 101.5, "limite de capacidade", color=CORAL,
            fontsize=8, ha="right", va="bottom")
    ax.axhline(85, color=AMBAR, ls=":", lw=1.2)
    ax.set_xlabel("Leitos SUS por 10 mil habitantes", fontsize=9)
    ax.set_ylabel("Ocupação estimada (%)", fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="lower right", ncol=2)
    _titulo(ax, "Agrupamento de municípios por perfil de pressão (K-Means)",
            "Tamanho do ponto = volume anual de internações")
    ax.grid(color=CINZA, alpha=0.18)
    _salvar(fig, "g4_clusters.png")


def g5_ranking_uf(n: int = 12) -> None:
    uf = pd.read_csv(PROC / "fato_uf_mes.csv")
    top = uf.groupby("uf")["internacoes"].sum().nlargest(n).iloc[::-1]
    cores = [CORAL if u == "São Paulo" else TEAL for u in top.index]

    fig, ax = plt.subplots(figsize=(9, 5))
    barras = ax.barh(top.index, top.values, color=cores, height=0.72)
    for b, v in zip(barras, top.values):
        ax.text(v * 1.01, b.get_y() + b.get_height() / 2, f"{v/1e6:.2f} mi",
                va="center", fontsize=8, color=NAVY)
    ax.set_xlim(0, top.values.max() * 1.16)
    ax.xaxis.set_major_formatter(MIL)
    ax.set_xlabel("Internações em 12 meses", fontsize=9)
    _titulo(ax, f"Contexto nacional: {n} maiores UFs em internações SUS",
            f"Brasil: {uf['internacoes'].sum()/1e6:.1f} milhões de internações em 12 meses")
    ax.grid(axis="x", color=CINZA, alpha=0.2)
    _salvar(fig, "g5_ranking_uf.png")


def g6_tendencia() -> None:
    td = pd.read_csv(PROC / "mv_tendencia_municipio.csv")
    top = td.nlargest(12, "variacao_mensal_pct").iloc[::-1]

    fig, ax = plt.subplots(figsize=(9, 5))
    barras = ax.barh(top["municipio"], top["variacao_anualizada_pct"],
                     color=CORAL, height=0.72)
    for b, v, r2 in zip(barras, top["variacao_anualizada_pct"], top["r2"]):
        ax.text(v + 1.5, b.get_y() + b.get_height() / 2,
                f"{v:+.0f}%  (R2 {r2:.2f})", va="center", fontsize=8, color=NAVY)
    ax.set_xlim(0, top["variacao_anualizada_pct"].max() * 1.28)
    ax.set_xlabel("Variação anualizada da demanda (%)", fontsize=9)
    _titulo(ax, "Onde as internações crescem mais rápido",
            "Regressão linear sobre 12 meses  ·  municípios com ≥ 600 internações/ano")
    ax.grid(axis="x", color=CINZA, alpha=0.2)
    _salvar(fig, "g6_tendencia.png")


def g7_distribuicao_alerta() -> None:
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv")
    base = ind[ind["alerta_capacidade"].isin(["Crítico", "Atenção", "Adequado"])]
    cont = base["alerta_capacidade"].value_counts().reindex(
        ["Crítico", "Atenção", "Adequado"]
    )
    cores = [CORAL, AMBAR, TEAL]

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    cunhas, _, textos = ax.pie(
        cont.values, labels=None, colors=cores, autopct="%1.0f%%",
        startangle=90, pctdistance=0.78,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 10, "fontweight": "bold", "color": "white"},
    )
    ax.text(0, 0.06, f"{int(cont.sum())}", ha="center", fontsize=24,
            fontweight="bold", color=NAVY)
    ax.text(0, -0.16, "municípios\ncom rede de agudos", ha="center",
            fontsize=8.5, color=CINZA)
    ax.legend(cunhas, [f"{r}  ({v})" for r, v in cont.items()],
              frameon=False, fontsize=9, loc="center left", bbox_to_anchor=(0.98, 0.5))
    ax.set_title("Situação de capacidade da rede paulista", fontsize=12,
                 fontweight="bold", color=NAVY, loc="left")
    _salvar(fig, "g7_distribuicao_alerta.png")


def executar() -> None:
    print("[Viz] gerando evidencias visuais...")
    g1_serie_temporal()
    g2_ranking_criticidade()
    g3_perfil_cid()
    g4_clusters()
    g5_ranking_uf()
    g6_tendencia()
    g7_distribuicao_alerta()
    print("[Viz] concluido.")


if __name__ == "__main__":
    executar()
