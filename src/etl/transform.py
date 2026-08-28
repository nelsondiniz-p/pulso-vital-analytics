"""
PULSO - Camada de transformacao (T do ETL)
==========================================
Integra as tres fontes num modelo analitico com grao unico e chaves conciliadas.

Problema central resolvido aqui: as tres fontes NAO compartilham chave primaria.
  * SIH/SUS e CNES usam o codigo IBGE de 6 digitos (350010)
  * IBGE usa o codigo de 7 digitos com digito verificador (3500105)
  * os nomes de municipio divergem em acentuacao e caixa ("SAO PAULO" x "Sao Paulo")
A conciliacao e feita SEMPRE pelo codigo de 6 digitos, nunca por nome - decisao
que evita o erro classico de perder municipios homonimos ou acentuados.

Modelo de saida (data/processed):
  dim_municipio.csv        dimensao territorial + populacao + leitos
  fato_internacao_mes.csv  fato mensal: internacoes, valor, permanencia
  fato_cid_capitulo.csv    fato por perfil assistencial (CID-10)
  fato_uf_mes.csv          fato nacional por UF
  mv_indicadores_municipio.csv   tabela analitica consolidada (a que alimenta
                                 o dashboard e o Select AI)
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

MES_PT = {"Jan": "01", "Fev": "02", "Mar": "03", "Abr": "04", "Mai": "05", "Jun": "06",
          "Jul": "07", "Ago": "08", "Set": "09", "Out": "10", "Nov": "11", "Dez": "12"}

# O TabNet abrevia o capitulo CID-10 no cabecalho ("Cap 15"). Para que a tabela
# seja legivel por um gestor - e para que o Select AI gere respostas em
# linguagem de negocio - o nome completo e restituido aqui.
CAPITULOS_CID10 = {
    "Cap 01": "I. Doenças infecciosas e parasitárias",
    "Cap 02": "II. Neoplasias (tumores)",
    "Cap 03": "III. Doenças do sangue e transtornos imunitários",
    "Cap 04": "IV. Doenças endócrinas, nutricionais e metabólicas",
    "Cap 05": "V. Transtornos mentais e comportamentais",
    "Cap 06": "VI. Doenças do sistema nervoso",
    "Cap 07": "VII. Doenças do olho e anexos",
    "Cap 08": "VIII. Doenças do ouvido e da apófise mastóide",
    "Cap 09": "IX. Doenças do aparelho circulatório",
    "Cap 10": "X. Doenças do aparelho respiratório",
    "Cap 11": "XI. Doenças do aparelho digestivo",
    "Cap 12": "XII. Doenças da pele e do tecido subcutâneo",
    "Cap 13": "XIII. Doenças osteomusculares e do tecido conjuntivo",
    "Cap 14": "XIV. Doenças do aparelho geniturinário",
    "Cap 15": "XV. Gravidez, parto e puerpério",
    "Cap 16": "XVI. Afecções originadas no período perinatal",
    "Cap 17": "XVII. Malformações congênitas e anomalias cromossômicas",
    "Cap 18": "XVIII. Sintomas e achados anormais não classificados",
    "Cap 19": "XIX. Lesões e envenenamentos por causas externas",
    "Cap 20": "XX. Causas externas de morbidade e mortalidade",
    "Cap 21": "XXI. Contatos com serviços de saúde",
}


def normalizar_texto(s: str) -> str:
    """Remove acentos e padroniza caixa - usado apenas para exibicao."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def titulo(s: str) -> str:
    """'SAO JOSE DO RIO PRETO' -> 'Sao Jose do Rio Preto'."""
    minusculas = {"de", "da", "do", "das", "dos", "e", "d'"}
    partes = normalizar_texto(s).lower().split()
    return " ".join(p if p in minusculas and i > 0 else p.capitalize()
                    for i, p in enumerate(partes))


def periodo_iso(p: str) -> str:
    """'2026/Jan' -> '2026-01'."""
    if "/" not in str(p):
        return str(p)
    ano, mes = str(p).split("/", 1)
    return f"{ano}-{MES_PT.get(mes.strip()[:3].title(), '01')}"


def _ler(nome: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / nome, dtype={"codigo": str, "codigo_ibge": str})
    return df


# --------------------------------------------------------------------------- #
# 1. Dimensao municipio                                                        #
# --------------------------------------------------------------------------- #
def construir_dim_municipio() -> pd.DataFrame:
    print("[T] dimensao municipio (IBGE + CNES)...")
    mun = _ler("ibge_sp_municipios.csv")
    pop = _ler("ibge_sp_populacao.csv")[["codigo", "populacao", "ano"]]
    lei = _ler("cnes_sp_leitos.csv")[["codigo", "leitos_existentes", "leitos_sus"]]

    dim = (mun.merge(pop, on="codigo", how="left")
              .merge(lei, on="codigo", how="left"))
    # O nome vem do IBGE ja acentuado e e o que aparece para o gestor:
    # preserva-se a grafia oficial. A conciliacao entre fontes usa o codigo.
    dim["municipio"] = dim["municipio"].str.strip()
    dim[["leitos_existentes", "leitos_sus"]] = (
        dim[["leitos_existentes", "leitos_sus"]].fillna(0).astype(int)
    )
    dim["populacao"] = dim["populacao"].fillna(0).astype(int)
    dim["leitos_sus_10k_hab"] = np.where(
        dim["populacao"] > 0,
        (dim["leitos_sus"] / dim["populacao"] * 10_000).round(2),
        0.0,
    )
    dim["tem_rede_hospitalar"] = dim["leitos_existentes"] > 0
    dim.to_csv(PROC / "dim_municipio.csv", index=False)
    print(f"  -> dim_municipio.csv: {len(dim)} municipios "
          f"({int(dim['tem_rede_hospitalar'].sum())} com rede hospitalar)")
    return dim


# --------------------------------------------------------------------------- #
# 2. Fato mensal                                                               #
# --------------------------------------------------------------------------- #
def construir_fato_mensal() -> pd.DataFrame:
    print("[T] fato mensal de internacoes (SIH/SUS)...")
    intern = _ler("sih_sp_internacoes_mes.csv")
    valor = _ler("sih_sp_valor_mes.csv")
    perman = _ler("sih_sp_permanencia_mes.csv")

    for df in (intern, valor, perman):
        df["periodo"] = df["periodo"].map(periodo_iso)

    fato = (intern[["codigo", "periodo", "internacoes"]]
            .merge(valor[["codigo", "periodo", "valor_total"]],
                   on=["codigo", "periodo"], how="outer")
            .merge(perman[["codigo", "periodo", "media_permanencia"]],
                   on=["codigo", "periodo"], how="outer"))
    fato["internacoes"] = fato["internacoes"].fillna(0).astype(int)
    fato["valor_total"] = fato["valor_total"].fillna(0.0).round(2)
    fato["media_permanencia"] = fato["media_permanencia"].fillna(0.0).round(2)
    fato["custo_medio_internacao"] = np.where(
        fato["internacoes"] > 0,
        (fato["valor_total"] / fato["internacoes"]).round(2),
        0.0,
    )
    fato = fato.sort_values(["codigo", "periodo"])
    fato.to_csv(PROC / "fato_internacao_mes.csv", index=False)
    print(f"  -> fato_internacao_mes.csv: {len(fato)} linhas | "
          f"{fato['periodo'].nunique()} meses "
          f"({fato['periodo'].min()} a {fato['periodo'].max()})")
    return fato


# --------------------------------------------------------------------------- #
# 3. Fato perfil assistencial                                                  #
# --------------------------------------------------------------------------- #
def construir_fato_cid() -> pd.DataFrame:
    print("[T] fato perfil assistencial (CID-10)...")
    cid = _ler("sih_sp_cid_capitulo.csv")
    cid["capitulo_cid10"] = cid["capitulo_cid10"].str.strip()
    cid = cid[~cid["capitulo_cid10"].str.lower().isin(["total", "nan"])]
    cid["codigo_capitulo"] = cid["capitulo_cid10"]
    cid["capitulo_cid10"] = cid["codigo_capitulo"].map(
        lambda c: CAPITULOS_CID10.get(c, c)
    )
    cid["internacoes"] = cid["internacoes"].fillna(0).astype(int)
    cid = cid[cid["internacoes"] > 0]
    cid[["codigo", "codigo_capitulo", "capitulo_cid10", "internacoes"]].to_csv(
        PROC / "fato_cid_capitulo.csv", index=False
    )
    print(f"  -> fato_cid_capitulo.csv: {len(cid)} linhas | "
          f"{cid['capitulo_cid10'].nunique()} capitulos CID-10")
    return cid


# --------------------------------------------------------------------------- #
# 4. Fato nacional                                                             #
# --------------------------------------------------------------------------- #
def construir_fato_uf() -> pd.DataFrame:
    print("[T] fato nacional por UF...")
    uf = _ler("sih_br_uf_mes.csv")
    uf["periodo"] = uf["periodo"].map(periodo_iso)
    uf["internacoes"] = uf["internacoes"].fillna(0).astype(int)
    uf.to_csv(PROC / "fato_uf_mes.csv", index=False)
    print(f"  -> fato_uf_mes.csv: {len(uf)} linhas | {uf['uf'].nunique()} UFs")
    return uf


# --------------------------------------------------------------------------- #
# 5. Tabela analitica consolidada                                              #
# --------------------------------------------------------------------------- #
def construir_indicadores(dim: pd.DataFrame, fato: pd.DataFrame,
                          cid: pd.DataFrame) -> pd.DataFrame:
    """Consolida o grao municipio com os indicadores de gestao do PULSO."""
    print("[T] tabela analitica de indicadores...")
    meses = sorted(fato["periodo"].unique())
    ultimos3, primeiros3 = meses[-3:], meses[:3]

    agr = fato.groupby("codigo").agg(
        internacoes_12m=("internacoes", "sum"),
        valor_total_12m=("valor_total", "sum"),
        media_permanencia=("media_permanencia", "mean"),
    ).reset_index()

    rec = (fato[fato["periodo"].isin(ultimos3)].groupby("codigo")["internacoes"]
           .sum().rename("internacoes_ult_trim"))
    ant = (fato[fato["periodo"].isin(primeiros3)].groupby("codigo")["internacoes"]
           .sum().rename("internacoes_prim_trim"))
    agr = agr.merge(rec, on="codigo", how="left").merge(ant, on="codigo", how="left")
    agr[["internacoes_ult_trim", "internacoes_prim_trim"]] = (
        agr[["internacoes_ult_trim", "internacoes_prim_trim"]].fillna(0)
    )

    agr["variacao_trimestral_pct"] = np.where(
        agr["internacoes_prim_trim"] > 0,
        ((agr["internacoes_ult_trim"] / agr["internacoes_prim_trim"] - 1) * 100).round(1),
        np.nan,
    )

    # perfil assistencial dominante do municipio
    top_cid = (cid.sort_values("internacoes", ascending=False)
                  .groupby("codigo").head(1)[["codigo", "capitulo_cid10"]]
                  .rename(columns={"capitulo_cid10": "perfil_dominante"}))

    ind = (dim.merge(agr, on="codigo", how="left")
              .merge(top_cid, on="codigo", how="left"))
    ind["internacoes_12m"] = ind["internacoes_12m"].fillna(0).astype(int)
    ind["valor_total_12m"] = ind["valor_total_12m"].fillna(0.0).round(2)
    ind["media_permanencia"] = ind["media_permanencia"].fillna(0.0).round(2)

    # ---- indicadores de gestao ------------------------------------------- #
    # Taxa de internacao por mil habitantes: demanda relativa a populacao.
    ind["internacoes_mil_hab"] = np.where(
        ind["populacao"] > 0,
        (ind["internacoes_12m"] / ind["populacao"] * 1_000).round(2), 0.0)

    # Giro de leito: quantas internacoes cada leito SUS absorveu no ano.
    # E o indicador que responde "a capacidade esta sendo ultrapassada?".
    ind["giro_leito_ano"] = np.where(
        ind["leitos_sus"] > 0,
        (ind["internacoes_12m"] / ind["leitos_sus"]).round(1), np.nan)

    # Taxa de ocupacao estimada = (internacoes x permanencia media) / (leitos x 365)
    # Aproximacao classica de ocupacao a partir de dados agregados do SIH.
    ind["ocupacao_estimada_pct"] = np.where(
        ind["leitos_sus"] > 0,
        ((ind["internacoes_12m"] * ind["media_permanencia"]) /
         (ind["leitos_sus"] * 365) * 100).round(1), np.nan)

    ind["custo_medio_internacao"] = np.where(
        ind["internacoes_12m"] > 0,
        (ind["valor_total_12m"] / ind["internacoes_12m"]).round(2), 0.0)

    # ---- classificacao do perfil de permanencia --------------------------- #
    # Municipios sede de hospital psiquiatrico ou de longa permanencia (ex.:
    # Itapira, Jaci) apresentam permanencia media de 25 a 100 dias. Sem esta
    # marcacao eles apareceriam como "rede em colapso" no ranking de ocupacao,
    # quando na verdade tem um perfil assistencial estruturalmente diferente.
    # Regra: permanencia media >= 20 dias (a mediana estadual fica perto de 5).
    ind["perfil_permanencia"] = np.select(
        [ind["media_permanencia"] >= 20, ind["media_permanencia"] >= 8],
        ["Longa permanência", "Permanência elevada"],
        default="Agudos",
    )
    ind.loc[ind["internacoes_12m"] == 0, "perfil_permanencia"] = "Sem internações"

    # Alerta operacional. So os municipios de LONGA permanencia (>= 20 dias,
    # sede de hospital psiquiatrico ou de retaguarda) ficam de fora: neles a
    # ocupacao alta e estrutural. Municipios com permanencia elevada mas ainda
    # compativel com hospital geral de maior complexidade (8 a 20 dias, caso de
    # Guarulhos por exemplo) permanecem na analise - excluir esses esconderia
    # exatamente parte da rede que mais importa para o gestor.
    ind["alerta_capacidade"] = np.select(
        [
            (ind["perfil_permanencia"].isin(["Longa permanência", "Sem internações"])),
            (ind["ocupacao_estimada_pct"] >= 100),
            (ind["ocupacao_estimada_pct"] >= 85),
            (ind["ocupacao_estimada_pct"].notna()),
        ],
        ["Não aplicável", "Crítico", "Atenção", "Adequado"],
        default="Sem leitos SUS",
    )

    ind.to_csv(PROC / "mv_indicadores_municipio.csv", index=False)
    print(f"  -> mv_indicadores_municipio.csv: {len(ind)} municipios")
    return ind


def executar() -> dict:
    dim = construir_dim_municipio()
    fato = construir_fato_mensal()
    cid = construir_fato_cid()
    uf = construir_fato_uf()
    ind = construir_indicadores(dim, fato, cid)
    return {"dim": dim, "fato": fato, "cid": cid, "uf": uf, "ind": ind}


if __name__ == "__main__":
    executar()
