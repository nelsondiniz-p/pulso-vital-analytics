"""
PULSO - Verificacao de consistencia da entrega
==============================================
Confere se os numeros do painel, das tabelas analiticas e da documentacao
contam a mesma historia. Roda em segundos e deve ser executado antes de
qualquer entrega ou apresentacao.

    python src/verificar.py

Tres familias de checagem:
  1. Conciliacao entre fontes  - o total estadual bate com o cubo nacional?
  2. Coerencia dos indicadores - nenhum valor impossivel passou?
  3. Consistencia documental   - os numeros do README batem com os dados?
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"

falhas: list[str] = []
avisos: list[str] = []


def checar(condicao: bool, descricao: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  OK    {descricao}")
    else:
        falhas.append(f"{descricao} — {detalhe}")
        print(f"  FALHA {descricao}  {detalhe}")


def avisar(condicao: bool, descricao: str, detalhe: str = "") -> None:
    if condicao:
        print(f"  OK    {descricao}")
    else:
        avisos.append(f"{descricao} — {detalhe}")
        print(f"  AVISO {descricao}  {detalhe}")


def br(n) -> str:
    return f"{int(n):,}".replace(",", ".")


# --------------------------------------------------------------------------- #
def conciliacao_entre_fontes() -> None:
    print("\n[1] Conciliacao entre fontes")
    fato = pd.read_csv(PROC / "fato_internacao_mes.csv", dtype={"codigo": str})
    cid = pd.read_csv(PROC / "fato_cid_capitulo.csv", dtype={"codigo": str})
    uf = pd.read_csv(PROC / "fato_uf_mes.csv")
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv", dtype={"codigo": str})

    total_mensal = int(fato["internacoes"].sum())
    total_sp_nacional = int(uf.loc[uf["uf"] == "São Paulo", "internacoes"].sum())
    total_cid = int(cid["internacoes"].sum())
    total_ind = int(ind["internacoes_12m"].sum())

    # O cubo estadual e o cubo nacional sao tabulacoes independentes do mesmo
    # SIH. Se os dois batem exatamente, a extracao esta integra.
    checar(total_mensal == total_sp_nacional,
           "cubo estadual bate com o cubo nacional",
           f"estadual={br(total_mensal)} nacional={br(total_sp_nacional)}")

    checar(total_mensal == total_ind,
           "tabela analitica bate com o fato mensal",
           f"fato={br(total_mensal)} indicadores={br(total_ind)}")

    # O TabNet suprime celulas com contagem muito baixa ao cruzar duas
    # dimensoes. Uma diferenca pequena aqui e esperada, uma grande nao.
    dif = abs(total_mensal - total_cid)
    avisar(dif / total_mensal < 0.001,
           "perfil CID-10 dentro da tolerancia de supressao",
           f"diferenca de {dif} registros ({dif/total_mensal:.4%})")

    # Toda chave do fato precisa existir na dimensao.
    dim = pd.read_csv(PROC / "dim_municipio.csv", dtype={"codigo": str})
    orfas = set(fato["codigo"]) - set(dim["codigo"])
    checar(not orfas, "nenhuma chave orfa entre fato e dimensao",
           f"{len(orfas)} codigos sem municipio correspondente")


def coerencia_dos_indicadores() -> None:
    print("\n[2] Coerencia dos indicadores")
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv", dtype={"codigo": str})

    checar(len(ind) == 645, "645 municipios de Sao Paulo presentes", f"encontrados {len(ind)}")
    checar((ind["populacao"] >= 0).all(), "nenhuma populacao negativa")
    checar((ind["internacoes_12m"] >= 0).all(), "nenhuma internacao negativa")
    checar((ind["leitos_sus"] <= ind["leitos_existentes"]).all(),
           "leitos SUS nunca excedem os leitos existentes")

    # Ocupacao so existe onde ha leitos SUS.
    sem_leito = ind[(ind["leitos_sus"] == 0) & ind["ocupacao_estimada_pct"].notna()]
    checar(len(sem_leito) == 0,
           "ocupacao calculada apenas onde ha leitos SUS",
           f"{len(sem_leito)} municipios com ocupacao sem leito")

    # Municipios de longa permanencia nao podem receber alerta operacional.
    longa = ind[(ind["perfil_permanencia"] == "Longa permanência")
                & ind["alerta_capacidade"].isin(["Crítico", "Atenção", "Adequado"])]
    checar(len(longa) == 0,
           "municipios de longa permanencia excluidos do alerta",
           f"{len(longa)} classificados indevidamente")

    # Custo medio por internacao dentro de uma faixa plausivel para o SIH.
    ativos = ind[ind["internacoes_12m"] >= 100]
    fora = ativos[(ativos["custo_medio_internacao"] < 100)
                  | (ativos["custo_medio_internacao"] > 50_000)]
    avisar(len(fora) == 0, "custo medio dentro da faixa plausivel",
           f"{len(fora)} municipios fora de R$ 100 a R$ 50.000")


def consistencia_documental() -> None:
    print("\n[3] Consistencia entre dados e documentacao")
    ind = pd.read_csv(PROC / "mv_indicadores_municipio.csv", dtype={"codigo": str})
    metricas = json.loads((PROC / "modelo_metricas.json").read_text(encoding="utf-8"))
    readme = (BASE / "README.md").read_text(encoding="utf-8")

    esperados = {
        "internacoes": br(ind["internacoes_12m"].sum()),
        "leitos_sus": br(ind["leitos_sus"].sum()),
        "populacao": br(ind["populacao"].sum()),
        "municipios": str(len(ind)),
        "criticos": str(int((ind["alerta_capacidade"] == "Crítico").sum())),
        "atencao": str(int((ind["alerta_capacidade"] == "Atenção").sum())),
        "cluster_n": str(metricas["clusterizacao"]["n_municipios"]),
    }
    for nome, valor in esperados.items():
        checar(valor in readme, f"README cita o valor correto de {nome}",
               f"esperado '{valor}'")

    # O payload do dashboard precisa refletir a mesma execucao do pipeline.
    payload = json.loads((BASE / "dashboard" / "dados.json").read_text(encoding="utf-8"))
    checar(payload["kpis"]["internacoes_12m"] == int(ind["internacoes_12m"].sum()),
           "payload do dashboard esta atualizado",
           "rode `python src/viz/build_payload.py` apos mudar o pipeline")


def main() -> int:
    print("=" * 62)
    print("  PULSO — verificacao de consistencia da entrega")
    print("=" * 62)
    conciliacao_entre_fontes()
    coerencia_dos_indicadores()
    consistencia_documental()

    print("\n" + "=" * 62)
    if falhas:
        print(f"  {len(falhas)} FALHA(S) — corrigir antes de entregar")
        for f in falhas:
            print(f"    · {f}")
    else:
        print("  Todas as checagens obrigatorias passaram.")
    if avisos:
        print(f"\n  {len(avisos)} aviso(s) — verificar, mas nao bloqueiam a entrega:")
        for a in avisos:
            print(f"    · {a}")
    print("=" * 62)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
