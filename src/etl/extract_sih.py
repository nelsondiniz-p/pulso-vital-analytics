"""
PULSO - Extracao da Fonte 1: SIH/SUS (dados RELACIONAIS)
========================================================
Sistema de Informacoes Hospitalares do SUS, via TabNet/DATASUS.

Justificativa do formato relacional: o SIH e um fato transacional com grao bem
definido (internacao autorizada por AIH), metricas aditivas (internacoes, valor
pago) e dimensoes estaveis (municipio, periodo, CID-10, faixa etaria). Isso o
torna o candidato natural para modelagem relacional/dimensional e para
agregacoes SQL - que e exatamente o que o Select AI precisa consultar.

Saidas (data/raw):
    sih_sp_internacoes_mes.csv      municipio x mes  (internacoes)
    sih_sp_valor_mes.csv            municipio x mes  (valor total R$)
    sih_sp_permanencia_mes.csv      municipio x mes  (media de permanencia)
    sih_sp_cid_capitulo.csv         municipio x capitulo CID-10 (internacoes)
    sih_br_uf_mes.csv               UF x mes (internacoes) - visao nacional
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl.tabnet_client import TabNet, br_to_float, separar_codigo_nome  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

MESES = 12  # janela de analise: ultimos 12 meses disponiveis


def _salvar_longo(nome_arquivo: str, cabecalho: list, linhas: list,
                  col_chave: str, col_valor: str) -> int:
    """Converte a tabela cruzada do TabNet para formato longo (tidy) e grava CSV.

    O TabNet devolve uma matriz (linha = territorio, colunas = periodos). Para
    carga em banco relacional o formato longo e muito superior: uma linha por
    (territorio, periodo, medida).
    """
    periodos = [c for c in cabecalho[1:] if c.lower() != "total"]
    destino = RAW / nome_arquivo
    n = 0
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo", col_chave, "periodo", col_valor])
        for linha in linhas:
            if not linha or len(linha) < 2:
                continue
            rotulo = linha[0]
            if rotulo.upper().startswith("TOTAL") or "Morbidade Hospitalar" in rotulo:
                continue
            if "IGNORADO" in rotulo.upper():
                continue
            codigo, nome = separar_codigo_nome(rotulo)
            for i, periodo in enumerate(periodos, start=1):
                if i >= len(linha):
                    break
                valor = br_to_float(linha[i])
                if valor is None:
                    continue
                w.writerow([codigo, nome, periodo, valor])
                n += 1
    print(f"  -> {destino.name}: {n} registros")
    return n


def _salvar_cruzado(nome_arquivo: str, cabecalho: list, linhas: list,
                    col_chave: str, col_dim: str, col_valor: str) -> int:
    """Igual ao anterior, mas a coluna nao e periodo e sim outra dimensao."""
    dims = [c for c in cabecalho[1:] if c.lower() != "total"]
    destino = RAW / nome_arquivo
    n = 0
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo", col_chave, col_dim, col_valor])
        for linha in linhas:
            if not linha or len(linha) < 2:
                continue
            rotulo = linha[0]
            if rotulo.upper().startswith("TOTAL") or "Morbidade Hospitalar" in rotulo:
                continue
            if "IGNORADO" in rotulo.upper():
                continue
            codigo, nome = separar_codigo_nome(rotulo)
            for i, dim in enumerate(dims, start=1):
                if i >= len(linha):
                    break
                valor = br_to_float(linha[i])
                if valor is None:
                    continue
                w.writerow([codigo, nome, dim, valor])
                n += 1
    print(f"  -> {destino.name}: {n} registros")
    return n


def extrair() -> None:
    print("[SIH/SUS] Conectando ao cubo estadual (Sao Paulo)...")
    sp = TabNet("sih/cnv/nisp.def")
    print(f"  cubo: {sp.titulo}")
    print(f"  periodos disponiveis: {len(sp.arquivos)} | usando os {MESES} mais recentes")

    print("[SIH/SUS] 1/5 internacoes por municipio x mes")
    cab, lin = sp.tabular("Município", "Internações", "Ano/mês_processamento", MESES)
    _salvar_longo("sih_sp_internacoes_mes.csv", cab, lin, "municipio", "internacoes")

    print("[SIH/SUS] 2/5 valor total por municipio x mes")
    cab, lin = sp.tabular("Município", "Valor_total", "Ano/mês_processamento", MESES)
    _salvar_longo("sih_sp_valor_mes.csv", cab, lin, "municipio", "valor_total")

    print("[SIH/SUS] 3/5 media de permanencia por municipio x mes")
    cab, lin = sp.tabular("Município", "Média_permanência", "Ano/mês_processamento", MESES)
    _salvar_longo("sih_sp_permanencia_mes.csv", cab, lin, "municipio", "media_permanencia")

    print("[SIH/SUS] 4/5 internacoes por municipio x capitulo CID-10")
    cab, lin = sp.tabular("Município", "Internações", "Capítulo_CID-10", MESES)
    _salvar_cruzado("sih_sp_cid_capitulo.csv", cab, lin,
                    "municipio", "capitulo_cid10", "internacoes")

    print("[SIH/SUS] 5/5 visao nacional: internacoes por UF x mes")
    br = TabNet("sih/cnv/niuf.def")
    cab, lin = br.tabular("Unidade_da_Federação", "Internações",
                          "Ano/mês_processamento", MESES)
    _salvar_longo("sih_br_uf_mes.csv", cab, lin, "uf", "internacoes")

    print("[SIH/SUS] concluido.")


if __name__ == "__main__":
    extrair()
