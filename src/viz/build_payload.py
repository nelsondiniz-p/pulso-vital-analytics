"""
PULSO - Montagem do payload do dashboard
========================================
Consolida as tabelas analiticas num unico JSON compacto que alimenta o
dashboard PULSO. O dashboard e estatico (roda em GitHub Pages, sem servidor),
entao os dados viajam embutidos na propria pagina.

No ambiente Oracle este payload e substituido por consultas diretas as views
analiticas do Autonomous Database - a estrutura dos campos e identica, o que
mantem o front-end inalterado na migracao.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"
SAIDA = BASE / "dashboard" / "dados.json"
SAIDA.parent.mkdir(parents=True, exist_ok=True)


def _n(valor):
    """Converte NaN/numpy para tipos JSON validos."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return None
    if isinstance(valor, (np.integer,)):
        return int(valor)
    if isinstance(valor, (np.floating,)):
        return round(float(valor), 2)
    return valor


def montar() -> dict:
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv", dtype={"codigo": str})
    fato = pd.read_csv(PROC / "fato_internacao_mes.csv", dtype={"codigo": str})
    cid = pd.read_csv(PROC / "fato_cid_capitulo.csv", dtype={"codigo": str})
    uf = pd.read_csv(PROC / "fato_uf_mes.csv")
    clusters = pd.read_csv(PROC / "mv_clusters_municipio.csv", dtype={"codigo": str})
    tend = pd.read_csv(PROC / "mv_tendencia_municipio.csv", dtype={"codigo": str})
    rank = pd.read_csv(PROC / "mv_ranking_criticidade.csv", dtype={"codigo": str})
    metricas = json.loads((PROC / "modelo_metricas.json").read_text(encoding="utf-8"))

    ind = (ind
           .merge(clusters[["codigo", "perfil_cluster"]], on="codigo", how="left")
           .merge(tend[["codigo", "variacao_mensal_pct", "variacao_anualizada_pct", "r2"]],
                  on="codigo", how="left")
           .merge(rank[["codigo", "indice_criticidade", "posicao"]],
                  on="codigo", how="left"))

    # --- KPIs de topo ----------------------------------------------------- #
    com_rede = ind[ind["leitos_sus"] > 0]
    kpis = {
        "internacoes_12m": int(ind["internacoes_12m"].sum()),
        "valor_total_12m": float(ind["valor_total_12m"].sum()),
        "custo_medio": float(ind["valor_total_12m"].sum() / ind["internacoes_12m"].sum()),
        "leitos_sus": int(ind["leitos_sus"].sum()),
        "leitos_existentes": int(ind["leitos_existentes"].sum()),
        "populacao": int(ind["populacao"].sum()),
        "municipios": int(len(ind)),
        "municipios_com_rede": int(len(com_rede)),
        "criticos": int((ind["alerta_capacidade"] == "Crítico").sum()),
        "atencao": int((ind["alerta_capacidade"] == "Atenção").sum()),
        "adequado": int((ind["alerta_capacidade"] == "Adequado").sum()),
        "permanencia_media": float(
            (ind["media_permanencia"] * ind["internacoes_12m"]).sum()
            / ind["internacoes_12m"].sum()
        ),
    }

    # --- serie temporal estadual ------------------------------------------ #
    serie = fato.groupby("periodo").agg(
        internacoes=("internacoes", "sum"),
        valor=("valor_total", "sum"),
    ).reset_index()
    serie_lista = [
        {"periodo": r.periodo, "internacoes": int(r.internacoes),
         "valor": round(float(r.valor), 2)}
        for r in serie.itertuples()
    ]

    # --- serie por municipio (para o drill-down) --------------------------- #
    series_municipio = {}
    for codigo, grupo in fato.groupby("codigo"):
        g = grupo.sort_values("periodo")
        if g["internacoes"].sum() > 0:
            series_municipio[codigo] = [int(v) for v in g["internacoes"]]
    periodos = sorted(fato["periodo"].unique())

    # --- perfil CID estadual e por municipio ------------------------------ #
    cid_estado = (cid.groupby("capitulo_cid10")["internacoes"].sum()
                  .sort_values(ascending=False))
    cid_lista = [{"capitulo": k, "internacoes": int(v)}
                 for k, v in cid_estado.items()]
    cid_municipio = {}
    for codigo, grupo in cid.groupby("codigo"):
        topo = grupo.nlargest(5, "internacoes")
        cid_municipio[codigo] = [
            {"c": r.capitulo_cid10, "v": int(r.internacoes)} for r in topo.itertuples()
        ]

    # --- ranking nacional -------------------------------------------------- #
    uf_lista = [
        {"uf": k, "internacoes": int(v)}
        for k, v in uf.groupby("uf")["internacoes"].sum()
                     .sort_values(ascending=False).items()
    ]

    # --- tabela de municipios --------------------------------------------- #
    colunas = ["codigo", "municipio", "regiao_intermediaria", "populacao",
               "leitos_sus", "leitos_existentes", "internacoes_12m",
               "valor_total_12m", "media_permanencia", "ocupacao_estimada_pct",
               "giro_leito_ano", "internacoes_mil_hab", "leitos_sus_10k_hab",
               "custo_medio_internacao", "variacao_trimestral_pct",
               "variacao_mensal_pct", "variacao_anualizada_pct", "r2",
               "indice_criticidade", "posicao", "alerta_capacidade",
               "perfil_permanencia", "perfil_cluster", "perfil_dominante"]
    municipios = [
        {c: _n(r[c]) for c in colunas}
        for _, r in ind[colunas].iterrows()
    ]

    payload = {
        "meta": {
            "projeto": "PULSO — Painel Único de Leitos, Saúde e Ocupação",
            "equipe": "Vital Analytics",
            "turma": "1TSCOA",
            "uf": "SP",
            "periodo_inicio": periodos[0],
            "periodo_fim": periodos[-1],
            "fontes": [
                "SIH/SUS — Sistema de Informações Hospitalares (DATASUS/TabNet)",
                "CNES — Cadastro Nacional de Estabelecimentos de Saúde (API + TabNet)",
                "IBGE — Malha municipal e população estimada (SIDRA t6579)",
            ],
        },
        "kpis": kpis,
        "periodos": periodos,
        "serie_estado": serie_lista,
        "series_municipio": series_municipio,
        "cid_estado": cid_lista,
        "cid_municipio": cid_municipio,
        "ranking_uf": uf_lista,
        "municipios": municipios,
        "modelos": metricas,
    }

    SAIDA.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
    tamanho = SAIDA.stat().st_size / 1024
    print(f"  -> dashboard/dados.json: {tamanho:.0f} KB | "
          f"{len(municipios)} municipios | {len(periodos)} periodos")
    return payload


if __name__ == "__main__":
    montar()
