# Dados do projeto

Snapshot completo dos dados que sustentam o painel: **estado de São Paulo,
12 meses — julho de 2025 a junho de 2026**. Nenhum valor é ilustrativo.

Os arquivos são versionados de propósito. São regeráveis com
`python src/run_pipeline.py`, mas reexecutar a extração meses depois traz outra
competência do SIH e outros totais. Publicar o snapshot é o que torna os
números do painel e da apresentação auditáveis.

---

## `raw/` — saída bruta das fontes

O que cada fonte devolveu, antes de qualquer integração. Um arquivo por
tabulação.

| Arquivo | Fonte | Conteúdo |
|---|---|---|
| `sih_sp_internacoes_mes.csv` | SIH/SUS · TabNet | Internações por município × mês |
| `sih_sp_valor_mes.csv` | SIH/SUS · TabNet | Valor pago das AIH por município × mês |
| `sih_sp_permanencia_mes.csv` | SIH/SUS · TabNet | Permanência média por município × mês |
| `sih_sp_cid_capitulo.csv` | SIH/SUS · TabNet | Internações por município × capítulo CID-10 |
| `sih_br_uf_mes.csv` | SIH/SUS · TabNet | Internações por UF × mês (contexto nacional) |
| `cnes_sp_leitos.csv` | CNES · TabNet | Leitos existentes e leitos SUS por município |
| `cnes_sp_estabelecimentos.json` | CNES · API de Dados Abertos | 905 documentos de estabelecimentos hospitalares |
| `cnes_sp_estabelecimentos.jsonl` | idem, em JSON Lines | Mesmo conteúdo, um documento por linha |
| `ibge_sp_municipios.csv` | IBGE · API de Localidades | Malha municipal e hierarquia territorial |
| `ibge_sp_populacao.csv` | IBGE · SIDRA t6579 | População residente estimada |

**Por que dois formatos do CNES.** O `.json` é um array único, legível no
navegador. O `.jsonl` tem um documento por linha, que é o formato consumido por
`DBMS_CLOUD.COPY_COLLECTION` na carga do Oracle. Mesmo conteúdo, dois destinos.

---

## `processed/` — modelo dimensional

Resultado da integração. **É esta pasta que se carrega no Autonomous Database**
(ver `sql/02_carga_dados.sql`).

| Arquivo | Papel | Linhas |
|---|---|---:|
| `dim_municipio.csv` | Dimensão territorial: IBGE + população + leitos do CNES | 645 |
| `fato_internacao_mes.csv` | Fato mensal: internações, valor, permanência | 3.847 |
| `fato_cid_capitulo.csv` | Perfil assistencial por capítulo CID-10 | 5.781 |
| `fato_uf_mes.csv` | Fato nacional por unidade da federação | 322 |
| `mv_indicadores_municipio.csv` | Tabela analítica principal, um município por linha | 645 |
| `mv_clusters_municipio.csv` | Saída do K-Means | 321 |
| `mv_ranking_criticidade.csv` | Índice composto de criticidade | 321 |
| `mv_tendencia_municipio.csv` | Regressão linear de tendência | 265 |
| `modelo_metricas.json` | Métricas de avaliação dos três modelos | — |

Descrição campo a campo, com as ressalvas metodológicas de cada indicador:
[`../docs/dicionario_dados.md`](../docs/dicionario_dados.md).

---

## Números de controle

Servem para conferir qualquer recarga. Se não baterem, a carga foi parcial.

```
internações em 12 meses ....  2.913.953
recurso executado ..........  R$ 5.686.834.532
leitos SUS .................  55.090
municípios .................  645
```

O total pelo cubo estadual e o total pelo cubo nacional são tabulações
independentes do mesmo SIH e batem exatamente — é a checagem de integridade da
extração. `python src/verificar.py` roda essa e outras 19 conferências.
