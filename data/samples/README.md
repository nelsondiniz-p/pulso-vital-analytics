# Amostras de dados

Recortes das tabelas produzidas pelo pipeline, versionados para que o
repositório seja navegável sem executar a extração completa.

| Arquivo | O que é |
|---|---|
| `dim_municipio__amostra.csv` | Dimensão territorial (IBGE + CNES) |
| `fato_internacao_mes__amostra.csv` | Fato mensal do SIH/SUS |
| `fato_cid_capitulo__amostra.csv` | Perfil assistencial por CID-10 |
| `fato_uf_mes__amostra.csv` | Contexto nacional por UF |
| `mv_indicadores_municipio__amostra.csv` | Tabela analítica principal |
| `mv_clusters_municipio__amostra.csv` | Saída do K-Means |
| `mv_ranking_criticidade__amostra.csv` | Índice composto de criticidade |
| `mv_tendencia_municipio__amostra.csv` | Regressão linear de tendência |
| `cnes_estabelecimentos__amostra.json` | Documentos JSON do CNES (fonte semiestruturada) |
| `cnes_sp_leitos__amostra.csv` | Leitos de internação por município |
| `ibge_sp_populacao__amostra.csv` | População residente estimada (SIDRA t6579) |

Para regenerar as tabelas completas:

```bash
python src/run_pipeline.py
```

Descrição de cada campo: [`../../docs/dicionario_dados.md`](../../docs/dicionario_dados.md).
