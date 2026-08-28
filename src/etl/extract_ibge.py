"""
PULSO - Extracao da Fonte 3: IBGE (dados TABULARES / CSV -> External Table)
===========================================================================
Malha municipal e populacao residente estimada.

Justificativa do formato CSV/External Table: sao dados de referencia, de baixo
volume, atualizacao anual e schema estavel. Nao ha ganho em carrega-los para
dentro do banco - o Oracle le o arquivo no Object Storage como se fosse tabela
(DBMS_CLOUD.CREATE_EXTERNAL_TABLE). Trocar o CSV atualiza a analise inteira sem
recarga. E tambem o denominador de todos os indicadores per capita do PULSO.

APIs usadas:
    servicodados.ibge.gov.br/api/v1/localidades  -> hierarquia territorial
    apisidra.ibge.gov.br  tabela 6579            -> populacao residente estimada

Saidas (data/raw):
    ibge_sp_municipios.csv   codigo, municipio, regiao_imediata, regiao_intermediaria
    ibge_sp_populacao.csv    codigo, municipio, populacao, ano
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; PULSO-ETL/1.0; projeto academico FIAP)"
UF_SP = 35


def _json(url: str, tentativas: int = 3):
    """GET JSON tolerante: as APIs do IBGE podem responder comprimidas (gzip)."""
    for i in range(tentativas):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, identity"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                bruto = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or bruto[:2] == b"\x1f\x8b":
                    bruto = gzip.decompress(bruto)
                return json.loads(bruto.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            if i == tentativas - 1:
                raise RuntimeError(f"Falha em {url}: {exc}") from exc
            time.sleep(3 * (i + 1))
    return None


def cod6(codigo_ibge) -> str:
    """IBGE usa 7 digitos (com verificador); o DATASUS usa 6. 3500105 -> 350010."""
    return str(codigo_ibge)[:6]


def extrair_municipios() -> int:
    print("[IBGE] malha municipal de Sao Paulo...")
    dados = _json(
        f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF_SP}/municipios"
    )
    destino = RAW / "ibge_sp_municipios.csv"
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo", "codigo_ibge", "municipio",
                    "regiao_imediata", "regiao_intermediaria", "mesorregiao"])
        for m in dados:
            imed = (m.get("regiao-imediata") or {})
            inter = (imed.get("regiao-intermediaria") or {})
            meso = (((m.get("microrregiao") or {}).get("mesorregiao")) or {})
            w.writerow([
                cod6(m["id"]), m["id"], m["nome"],
                imed.get("nome", ""), inter.get("nome", ""), meso.get("nome", ""),
            ])
    print(f"  -> {destino.name}: {len(dados)} municipios")
    return len(dados)


def extrair_populacao() -> int:
    """Tabela SIDRA 6579 - Populacao residente estimada, variavel 9324."""
    print("[IBGE] populacao residente estimada (SIDRA t6579)...")
    dados = _json(
        f"https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last%201"
    )
    cabecalho, registros = dados[0], dados[1:]
    destino = RAW / "ibge_sp_populacao.csv"
    n = 0
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo", "codigo_ibge", "municipio", "populacao", "ano"])
        for r in registros:
            cod_ibge = r.get("D1C", "")
            if not cod_ibge.startswith(str(UF_SP)):
                continue  # mantem apenas Sao Paulo
            valor = r.get("V", "")
            if not valor.isdigit():
                continue
            nome = r.get("D1N", "").split(" (")[0]
            w.writerow([cod6(cod_ibge), cod_ibge, nome, int(valor), r.get("D3N", "")])
            n += 1
    print(f"  -> {destino.name}: {n} municipios | referencia {registros[0].get('D3N')}")
    return n


if __name__ == "__main__":
    extrair_municipios()
    extrair_populacao()
