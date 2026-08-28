"""
PULSO - Orquestrador do pipeline completo
=========================================
Executa a solucao ponta a ponta, na ordem em que os dados percorrem a
arquitetura. Um unico comando reproduz todo o MVP a partir das fontes publicas:

    python src/run_pipeline.py                # tudo
    python src/run_pipeline.py --sem-extracao # so transformacao em diante

Etapas:
    1. EXTRACAO      SIH/SUS (TabNet) · CNES (API JSON + TabNet) · IBGE (APIs)
    2. TRANSFORMACAO conciliacao das chaves, modelo dimensional, indicadores
    3. MODELAGEM     K-Means, indice de criticidade, regressao de tendencia
    4. VISUALIZACAO  evidencias PNG + payload + dashboard

Tempo aproximado com extracao: 12 a 20 minutos (dominado pelo TabNet).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def faixa(titulo: str) -> None:
    print("\n" + "=" * 66)
    print(f"  {titulo}")
    print("=" * 66)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline do projeto PULSO")
    ap.add_argument("--sem-extracao", action="store_true",
                    help="reaproveita data/raw e pula as chamadas as APIs")
    args = ap.parse_args()

    inicio = time.time()

    if not args.sem_extracao:
        faixa("ETAPA 1/4 - EXTRACAO DAS FONTES PUBLICAS")
        from etl import extract_sih, extract_cnes, extract_ibge
        extract_sih.extrair()
        extract_cnes.extrair_leitos()
        extract_ibge.extrair_municipios()
        extract_ibge.extrair_populacao()
    else:
        faixa("ETAPA 1/4 - EXTRACAO (pulada, usando data/raw existente)")

    faixa("ETAPA 2/4 - TRANSFORMACAO E INTEGRACAO")
    from etl import transform
    transform.executar()

    faixa("ETAPA 3/4 - MODELOS ANALITICOS")
    from analytics import modelos
    modelos.executar()

    if not args.sem_extracao:
        # Depende dos indicadores: o recorte de municipios da carga JSON e
        # definido pelo resultado do alerta de capacidade.
        faixa("ETAPA 3.5/4 - CARGA JSON DO CNES (municipios prioritarios)")
        from etl import extract_cnes as ec
        ec.extrair_estabelecimentos(ec.municipios_prioritarios(45))

    faixa("ETAPA 4/4 - EVIDENCIAS E DASHBOARD")
    from viz import graficos, build_payload, build_dashboard
    graficos.executar()
    build_payload.montar()
    build_dashboard.construir()

    faixa(f"PIPELINE CONCLUIDO EM {time.time() - inicio:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
