"""
PULSO - Extracao da Fonte 2: CNES (dados SEMIESTRUTURADOS / JSON)
=================================================================
Cadastro Nacional de Estabelecimentos de Saude.

Duas rotas complementares sao usadas de proposito:

  (a) API de Dados Abertos do Ministerio da Saude -> JSON puro.
      Justificativa do formato JSON: o cadastro de estabelecimento e um
      documento com atributos heterogeneos e opcionais (um hospital de ensino
      tem centro cirurgico e neonatal; um consultorio isolado nao tem nenhum
      dos dois). Modelar isso em colunas fixas geraria uma tabela esparsa. O
      Oracle 23ai consulta JSON nativamente, entao o documento e persistido
      como veio e "achatado" apenas na view analitica.

  (b) TabNet CNES -> capacidade instalada (leitos de internacao) por municipio.
      Necessario porque o indicador central do PULSO (pressao sobre a rede)
      exige o denominador de leitos, que nao vem no cadastro basico.

Saidas (data/raw):
    cnes_sp_estabelecimentos.json   documentos JSON (fonte semiestruturada)
    cnes_sp_leitos.csv              leitos existentes e SUS por municipio
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl.tabnet_client import TabNet, br_to_float, separar_codigo_nome  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

API = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
UA = "Mozilla/5.0 (compatible; PULSO-ETL/1.0; projeto academico FIAP)"

# Tipos de unidade com internacao/urgencia - o recorte que interessa ao PULSO.
# 05 Hospital Geral | 07 Hospital Especializado | 20 Pronto Socorro Geral
# 21 Pronto Socorro Especializado | 73 Pronto Atendimento
TIPOS_HOSPITALARES = [5, 7, 20, 21, 73]


def _api(params: dict, tentativas: int = 3):
    url = f"{API}?{urllib.parse.urlencode(params)}"
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            time.sleep(2 * (i + 1))
    return {"estabelecimentos": []}


def extrair_estabelecimentos(municipios: list, max_por_municipio: int = 400) -> int:
    """Baixa documentos JSON de estabelecimentos hospitalares dos municipios dados."""
    print(f"[CNES/JSON] baixando estabelecimentos de {len(municipios)} municipios...")
    documentos = []
    vistos = set()
    for n, cod in enumerate(municipios, start=1):
        for tipo in TIPOS_HOSPITALARES:
            offset = 0
            while offset < max_por_municipio:
                lote = _api({
                    "codigo_municipio": cod,
                    "codigo_tipo_unidade": tipo,
                    "limit": 20,
                    "offset": offset,
                }).get("estabelecimentos", [])
                if not lote:
                    break
                for doc in lote:
                    chave = doc.get("codigo_cnes")
                    if chave not in vistos:
                        vistos.add(chave)
                        documentos.append(doc)
                if len(lote) < 20:
                    break
                offset += 20
        if n % 10 == 0:
            print(f"    {n}/{len(municipios)} municipios | {len(documentos)} documentos")

    destino = RAW / "cnes_sp_estabelecimentos.json"
    destino.write_text(
        json.dumps(documentos, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"  -> {destino.name}: {len(documentos)} documentos JSON")

    # Formato JSON Lines: e o que o DBMS_CLOUD.COPY_COLLECTION do Oracle consome.
    jsonl = RAW / "cnes_sp_estabelecimentos.jsonl"
    with jsonl.open("w", encoding="utf-8") as fh:
        for doc in documentos:
            fh.write(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f"  -> {jsonl.name}: pronto para DBMS_CLOUD.COPY_COLLECTION")
    return len(documentos)


def extrair_leitos() -> int:
    """Capacidade instalada: leitos de internacao por municipio (competencia mais recente)."""
    print("[CNES/leitos] consultando TabNet...")
    tn = TabNet("cnes/cnv/leiintsp.def")
    competencia = tn.arquivos[0]
    print(f"  cubo: {tn.titulo}")
    print(f"  competencia: {competencia}")

    resultado: dict[str, dict] = {}
    for medida, campo in [("Qtd_existente", "leitos_existentes"),
                          ("Qtd_SUS", "leitos_sus")]:
        cab, lin = tn.tabular("Município", medida, arquivos=[competencia])
        for linha in lin:
            if not linha or len(linha) < 2:
                continue
            rotulo = linha[0]
            if rotulo.upper().startswith("TOTAL") or "CNES" in rotulo:
                continue
            if "IGNORADO" in rotulo.upper():
                continue
            codigo, nome = separar_codigo_nome(rotulo)
            if not codigo:
                continue
            valor = br_to_float(linha[-1])
            reg = resultado.setdefault(
                codigo, {"codigo": codigo, "municipio": nome,
                         "leitos_existentes": 0, "leitos_sus": 0}
            )
            reg[campo] = int(valor or 0)

    destino = RAW / "cnes_sp_leitos.csv"
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["codigo", "municipio", "leitos_existentes", "leitos_sus"]
        )
        w.writeheader()
        for reg in sorted(resultado.values(), key=lambda r: r["codigo"]):
            w.writerow(reg)
    print(f"  -> {destino.name}: {len(resultado)} municipios")
    return len(resultado)


def municipios_prioritarios(n: int = 45) -> list:
    """Seleciona o recorte de municipios para a carga JSON.

    Criterio: todos os municipios em alerta Critico ou Atencao (o publico-alvo
    direto do painel) mais os maiores em volume de internacoes, ate n. Puxar os
    645 municipios de SP custaria ~4 mil chamadas de API sem ganho analitico.
    """
    import csv as _csv
    proc = Path(__file__).resolve().parents[2] / "data" / "processed"
    with (proc / "mv_indicadores_municipio.csv").open(encoding="utf-8") as fh:
        linhas = list(_csv.DictReader(fh))
    alerta = [r for r in linhas if r["alerta_capacidade"] in ("Crítico", "Atenção")]
    volume = sorted(linhas, key=lambda r: int(r["internacoes_12m"] or 0), reverse=True)
    escolhidos, vistos = [], set()
    for r in alerta + volume:
        cod = r["codigo_ibge"]
        if cod and cod not in vistos:
            vistos.add(cod)
            escolhidos.append(int(cod[:6]))
        if len(escolhidos) >= n:
            break
    return escolhidos


if __name__ == "__main__":
    extrair_leitos()
    extrair_estabelecimentos(municipios_prioritarios(45))
