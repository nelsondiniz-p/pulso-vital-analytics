"""
PULSO - Modelos analiticos e tecnicas aplicadas
===============================================
Tres tecnicas, cada uma respondendo a uma pergunta de gestao especifica:

  1. CLUSTERIZACAO (K-Means, nao supervisionado)
     Pergunta: "quais municipios se parecem entre si em termos de pressao
     assistencial?" Substitui a comparacao ingenua por porte populacional, que
     junta realidades muito diferentes. Permite a Secretaria tratar grupos, nao
     645 casos isolados.

  2. INDICE COMPOSTO DE CRITICIDADE (normalizacao min-max ponderada)
     Pergunta: "por onde comecar?" Reduz quatro indicadores a um ranking unico
     e auditavel. Pesos explicitos e justificados - nao e caixa-preta.

  3. REGRESSAO LINEAR SOBRE SERIE TEMPORAL (tendencia)
     Pergunta: "onde as internacoes crescem mais rapido?" Ajusta a reta de
     tendencia em 12 meses por municipio e devolve a inclinacao normalizada,
     que e mais robusta que comparar dois pontos isolados.

Decisao metodologica importante: municipios de longa permanencia (hospitais
psiquiatricos e de retaguarda) sao EXCLUIDOS dos modelos de capacidade. Sem
isso eles dominam qualquer ranking de ocupacao por um motivo estrutural, nao
por crise assistencial.

Saidas (data/processed):
    mv_clusters_municipio.csv      cluster + perfil de cada municipio
    mv_ranking_criticidade.csv     ranking priorizado
    mv_tendencia_municipio.csv     inclinacao e classificacao de tendencia
    modelo_metricas.json           metricas de avaliacao dos modelos
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"

SEMENTE = 42  # reprodutibilidade: mesmo resultado a cada execucao


# --------------------------------------------------------------------------- #
# 1. Clusterizacao                                                             #
# --------------------------------------------------------------------------- #
ATRIBUTOS_CLUSTER = [
    "internacoes_mil_hab",      # demanda relativa a populacao
    "leitos_sus_10k_hab",       # oferta relativa a populacao
    "ocupacao_estimada_pct",    # pressao sobre a oferta
    "media_permanencia",        # complexidade/eficiencia do cuidado
    "custo_medio_internacao",   # intensidade de recurso por caso
]


def clusterizar(ind: pd.DataFrame, k: int = 4) -> tuple[pd.DataFrame, dict]:
    """Agrupa municipios com rede de agudos por perfil de pressao assistencial."""
    print(f"[Modelo 1] K-Means (k={k}) sobre {len(ATRIBUTOS_CLUSTER)} atributos")

    base = ind[
        (ind["perfil_permanencia"] != "Longa permanência")
        & (ind["leitos_sus"] > 0)
        & (ind["internacoes_12m"] > 0)
    ].copy()
    print(f"  populacao do modelo: {len(base)} municipios "
          f"(excluidos long-stay e sem rede)")

    X = base[ATRIBUTOS_CLUSTER].fillna(0).to_numpy(dtype=float)
    escalador = StandardScaler()          # K-Means e sensivel a escala
    Xp = escalador.fit_transform(X)

    # Avaliacao: silhueta para k de 2 a 7, escolha justificada
    avaliacao = {}
    for kk in range(2, 8):
        rotulos = KMeans(n_clusters=kk, random_state=SEMENTE, n_init=10).fit_predict(Xp)
        avaliacao[kk] = round(float(silhouette_score(Xp, rotulos)), 4)
    print(f"  silhueta por k: {avaliacao}")

    modelo = KMeans(n_clusters=k, random_state=SEMENTE, n_init=25)
    base["cluster"] = modelo.fit_predict(Xp)
    silhueta = float(silhouette_score(Xp, base["cluster"]))
    print(f"  silhueta final (k={k}): {silhueta:.4f} | inercia: {modelo.inertia_:.1f}")

    # ---- nomeacao dos clusters ------------------------------------------- #
    # Rotular apenas pela ocupacao seria enganoso: existe um grupo com MUITOS
    # leitos por habitante E ocupacao alta (polos regionais que atendem a
    # populacao de municipios vizinhos) e outro com muitos leitos e ocupacao
    # baixa (capacidade ociosa). Sao situacoes de gestao opostas. Por isso o
    # nome vem de duas dimensoes: pressao (ocupacao) x densidade de oferta.
    resumo = base.groupby("cluster")[ATRIBUTOS_CLUSTER].mean()
    ordem = resumo["ocupacao_estimada_pct"].sort_values(ascending=False).index.tolist()
    corte_oferta = base["leitos_sus_10k_hab"].median() * 1.6

    def nomear(centro: pd.Series) -> str:
        ocupacao = centro["ocupacao_estimada_pct"]
        oferta = centro["leitos_sus_10k_hab"]
        # Oferta extrema (acima de 50 leitos/10 mil hab.) nao e excesso de
        # capacidade: e municipio pequeno que sedia hospital de referencia
        # regional e atende a populacao de toda a microrregiao.
        if oferta >= 50:
            return "Sede de hospital regional"
        if ocupacao >= 70 and oferta >= corte_oferta:
            return "Polo regional sob pressão"
        if ocupacao >= 70:
            return "Rede local pressionada"
        if ocupacao < 45 and oferta >= corte_oferta:
            return "Capacidade ociosa"
        if ocupacao < 45:
            return "Rede com folga"
        return "Rede local equilibrada"

    mapa, usados = {}, {}
    for c in ordem:
        nome = nomear(resumo.loc[c])
        usados[nome] = usados.get(nome, 0) + 1
        mapa[c] = nome if usados[nome] == 1 else f"{nome} ({usados[nome]})"
    base["perfil_cluster"] = base["cluster"].map(mapa)

    print("  perfis identificados:")
    for c in ordem:
        r = resumo.loc[c]
        print(f"    {mapa[c]:<30} n={int((base['cluster'] == c).sum()):>3} | "
              f"ocup {r['ocupacao_estimada_pct']:>5.1f}% | "
              f"leitos/10k {r['leitos_sus_10k_hab']:>5.2f} | "
              f"perm {r['media_permanencia']:>4.1f}d")

    saida = base[["codigo", "municipio", "cluster", "perfil_cluster",
                  *ATRIBUTOS_CLUSTER, "internacoes_12m", "leitos_sus",
                  "populacao", "alerta_capacidade"]]
    saida.to_csv(PROC / "mv_clusters_municipio.csv", index=False)
    print(f"  -> mv_clusters_municipio.csv: {len(saida)} municipios")

    metricas = {
        "algoritmo": "K-Means",
        "k_escolhido": k,
        "silhueta": round(silhueta, 4),
        "silhueta_por_k": avaliacao,
        "inercia": round(float(modelo.inertia_), 2),
        "atributos": ATRIBUTOS_CLUSTER,
        "n_municipios": int(len(base)),
        "perfis": {mapa[c]: int((base["cluster"] == c).sum()) for c in ordem},
    }
    return saida, metricas


# --------------------------------------------------------------------------- #
# 2. Indice composto de criticidade                                            #
# --------------------------------------------------------------------------- #
PESOS = {
    "ocupacao_estimada_pct": 0.40,   # pressao imediata sobre o leito
    "internacoes_mil_hab": 0.25,     # demanda estrutural da populacao
    "escassez_leitos": 0.20,         # inverso da oferta per capita
    "variacao_trimestral_pct": 0.15, # aceleracao recente da demanda
}


def _min_max(s: pd.Series) -> pd.Series:
    """Normaliza para 0-1. Usa percentis 5-95 para nao deixar outlier dominar."""
    lo, hi = s.quantile(0.05), s.quantile(0.95)
    if hi == lo:
        return pd.Series(0.0, index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def ranking_criticidade(ind: pd.DataFrame) -> pd.DataFrame:
    """Indice 0-100 combinando pressao, demanda, escassez e aceleracao."""
    print("[Modelo 2] indice composto de criticidade")
    base = ind[(ind["perfil_permanencia"] != "Longa permanência")
               & (ind["leitos_sus"] > 0) & (ind["internacoes_12m"] > 0)].copy()

    # escassez = inverso da oferta de leitos por habitante
    base["escassez_leitos"] = -base["leitos_sus_10k_hab"]
    base["variacao_trimestral_pct"] = base["variacao_trimestral_pct"].fillna(0)

    componentes = {}
    for coluna, peso in PESOS.items():
        norm = _min_max(base[coluna])
        componentes[coluna] = norm * peso
        base[f"n_{coluna}"] = norm.round(3)

    base["indice_criticidade"] = (
        sum(componentes.values()) * 100
    ).round(1)
    base = base.sort_values("indice_criticidade", ascending=False)
    base["posicao"] = range(1, len(base) + 1)

    colunas = ["posicao", "codigo", "municipio", "indice_criticidade",
               "ocupacao_estimada_pct", "internacoes_mil_hab",
               "leitos_sus_10k_hab", "variacao_trimestral_pct",
               "internacoes_12m", "leitos_sus", "populacao",
               "perfil_dominante", "alerta_capacidade"]
    base[colunas].to_csv(PROC / "mv_ranking_criticidade.csv", index=False)
    print(f"  -> mv_ranking_criticidade.csv: {len(base)} municipios")
    print("  top 5:")
    for _, r in base.head(5).iterrows():
        print(f"    {int(r['posicao']):>2}. {r['municipio']:<24} "
              f"indice {r['indice_criticidade']:>5.1f} | "
              f"ocup {r['ocupacao_estimada_pct']:>5.1f}%")
    return base[colunas]


# --------------------------------------------------------------------------- #
# 3. Tendencia (regressao linear sobre 12 meses)                               #
# --------------------------------------------------------------------------- #
def tendencia(fato: pd.DataFrame, ind: pd.DataFrame,
              minimo_internacoes: int = 600) -> pd.DataFrame:
    """Ajusta reta de tendencia por municipio e classifica o movimento."""
    print("[Modelo 3] regressao linear de tendencia (12 meses)")
    elegiveis = ind[ind["internacoes_12m"] >= minimo_internacoes]["codigo"]
    dados = fato[fato["codigo"].isin(elegiveis)].copy()
    dados = dados.sort_values(["codigo", "periodo"])
    print(f"  municipios com volume suficiente (>= {minimo_internacoes}/ano): "
          f"{dados['codigo'].nunique()}")

    linhas = []
    for codigo, grupo in dados.groupby("codigo"):
        y = grupo["internacoes"].to_numpy(dtype=float)
        if len(y) < 6 or y.mean() == 0:
            continue
        x = np.arange(len(y), dtype=float)
        inclinacao, intercepto = np.polyfit(x, y, 1)
        previsto = inclinacao * x + intercepto
        ss_res = float(((y - previsto) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        # inclinacao mensal em % da media -> comparavel entre municipios
        var_mensal = inclinacao / y.mean() * 100
        linhas.append({
            "codigo": codigo,
            "media_mensal": round(float(y.mean()), 1),
            "inclinacao_mes": round(float(inclinacao), 2),
            "variacao_mensal_pct": round(float(var_mensal), 2),
            "variacao_anualizada_pct": round(float(var_mensal * 12), 1),
            "r2": round(float(r2), 3),
        })

    tend = pd.DataFrame(linhas)
    tend["classificacao"] = pd.cut(
        tend["variacao_mensal_pct"],
        bins=[-np.inf, -1.0, -0.25, 0.25, 1.0, np.inf],
        labels=["Queda forte", "Queda", "Estavel", "Alta", "Alta forte"],
    )
    tend = tend.merge(
        ind[["codigo", "municipio", "populacao", "internacoes_12m",
             "ocupacao_estimada_pct", "alerta_capacidade"]],
        on="codigo", how="left",
    ).sort_values("variacao_mensal_pct", ascending=False)

    tend.to_csv(PROC / "mv_tendencia_municipio.csv", index=False)
    print(f"  -> mv_tendencia_municipio.csv: {len(tend)} municipios")
    print(f"  distribuicao: "
          f"{tend['classificacao'].value_counts().reindex(['Alta forte','Alta','Estavel','Queda','Queda forte']).to_dict()}")
    print("  maiores altas:")
    for _, r in tend.head(5).iterrows():
        print(f"    {r['municipio']:<24} {r['variacao_mensal_pct']:>+5.2f}%/mes "
              f"(R2 {r['r2']:.2f}) | {int(r['internacoes_12m']):>6,} internacoes/ano")
    return tend


# --------------------------------------------------------------------------- #
def executar() -> dict:
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv", dtype={"codigo": str})
    fato = pd.read_csv(PROC / "fato_internacao_mes.csv", dtype={"codigo": str})

    clusters, metricas_cluster = clusterizar(ind)
    ranking = ranking_criticidade(ind)
    tend = tendencia(fato, ind)

    metricas = {
        "clusterizacao": metricas_cluster,
        "indice_criticidade": {
            "metodo": "normalizacao min-max (p5-p95) com pesos fixos",
            "pesos": PESOS,
            "n_municipios": int(len(ranking)),
        },
        "tendencia": {
            "metodo": "regressao linear ordinaria sobre 12 observacoes mensais",
            "n_municipios": int(len(tend)),
            "r2_mediano": round(float(tend["r2"].median()), 3),
            # O R2 mediano do conjunto e baixo de proposito: a maioria dos
            # municipios NAO tem tendencia, oscila em torno da media. O numero
            # que importa para a gestao e quantos tem tendencia consistente.
            "n_tendencia_consistente": int((tend["r2"] >= 0.5).sum()),
            "r2_mediano_consistentes": round(
                float(tend.loc[tend["r2"] >= 0.5, "r2"].median()), 3),
            "criterio_consistencia": "R2 >= 0,5",
        },
    }
    (PROC / "modelo_metricas.json").write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\n[Modelos] metricas gravadas em data/processed/modelo_metricas.json")
    return {"clusters": clusters, "ranking": ranking, "tendencia": tend,
            "metricas": metricas}


if __name__ == "__main__":
    executar()
