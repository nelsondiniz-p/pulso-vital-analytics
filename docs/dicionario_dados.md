# PULSO — Dicionário de dados

**Equipe Vital Analytics · 1TSCOB · Challenge Oracle + FIAP 2026**

Referência das tabelas produzidas pelo pipeline. Os arquivos ficam em
`data/processed/` e são carregados no Autonomous Database pelos scripts de
`sql/`.

---

## Convenções

- **`codigo`** — código IBGE do município com **6 dígitos** (`350010`). É a
  chave de integração entre as três fontes.
- **`codigo_ibge`** — código IBGE completo, com dígito verificador (`3500105`).
- **`periodo`** — competência no formato `AAAA-MM`.
- Valores monetários em **reais**; permanência em **dias**; percentuais em
  pontos percentuais (`105.0` = 105%).
- Ausência de dado é `NULL`, nunca zero — um município sem leitos SUS tem
  `ocupacao_estimada_pct` nula, não `0`.

---

## `dim_municipio` — dimensão territorial

Um registro por município de São Paulo (645).

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo` | texto(6) | Chave primária. Código IBGE truncado. |
| `codigo_ibge` | texto(7) | Código IBGE completo. |
| `municipio` | texto | Nome oficial, com acentuação (fonte IBGE). |
| `regiao_imediata` | texto | Região geográfica imediata (IBGE). |
| `regiao_intermediaria` | texto | Região geográfica intermediária (IBGE). É o grão de decisão da Secretaria Estadual. |
| `mesorregiao` | texto | Mesorregião (IBGE). |
| `populacao` | inteiro | População residente estimada. |
| `ano` | inteiro | Ano de referência da estimativa populacional. |
| `leitos_existentes` | inteiro | Total de leitos de internação cadastrados no CNES. |
| `leitos_sus` | inteiro | Leitos de internação disponíveis ao SUS. **É o denominador de toda análise de capacidade.** |
| `leitos_sus_10k_hab` | decimal | Oferta de leitos SUS por 10 mil habitantes. |
| `tem_rede_hospitalar` | booleano | `True` se o município tem ao menos um leito cadastrado. |

---

## `fato_internacao_mes` — fato mensal (SIH/SUS)

Grão: **município × mês**. 3.847 registros, 12 competências.

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo` | texto(6) | Município de internação. |
| `periodo` | texto(7) | Competência de processamento. |
| `internacoes` | inteiro | Internações registradas no período. |
| `valor_total` | decimal | Valor total pago pelas AIH, em reais. |
| `media_permanencia` | decimal | Permanência média em dias. |
| `custo_medio_internacao` | decimal | `valor_total ÷ internacoes`. |

> **Atenção ao interpretar.** O município aqui é o de **internação**, não o de
> residência do paciente. Um polo regional acumula internações de toda a
> microrregião — é justamente por isso que a análise por porte populacional
> isolada engana, e o agrupamento por perfil existe.

---

## `fato_cid_capitulo` — perfil assistencial

Grão: **município × capítulo CID-10**. 5.781 registros, 20 capítulos.

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo` | texto(6) | Município de internação. |
| `codigo_capitulo` | texto | Código do capítulo como o TabNet devolve (`Cap 15`). |
| `capitulo_cid10` | texto | Nome por extenso (`XV. Gravidez, parto e puerpério`). |
| `internacoes` | inteiro | Internações do capítulo no município, 12 meses. |

---

## `fato_uf_mes` — contexto nacional

Grão: **UF × mês**. 322 registros, 27 unidades da federação.

| Campo | Tipo | Descrição |
|---|---|---|
| `uf` | texto | Unidade da federação. |
| `periodo` | texto(7) | Competência. |
| `internacoes` | inteiro | Internações registradas. |

---

## `mv_indicadores_municipio` — tabela analítica principal

É a view que alimenta o dashboard e que o Select AI consulta. Um registro por
município, com todos os indicadores de gestão calculados.

Herda todos os campos de `dim_municipio` e acrescenta:

| Campo | Tipo | Cálculo e leitura |
|---|---|---|
| `internacoes_12m` | inteiro | Soma das internações nos 12 meses. |
| `valor_total_12m` | decimal | Recurso executado no período. |
| `media_permanencia` | decimal | Média das permanências mensais. |
| `perfil_dominante` | texto | Capítulo CID-10 com maior volume no município. |
| `internacoes_mil_hab` | decimal | `internacoes_12m ÷ populacao × 1.000`. Demanda relativa à população. |
| `giro_leito_ano` | decimal | `internacoes_12m ÷ leitos_sus`. Quantas internações cada leito absorveu. |
| `ocupacao_estimada_pct` | decimal | `(internacoes_12m × media_permanencia) ÷ (leitos_sus × 365) × 100`. **Estimativa**, ver ressalva abaixo. |
| `custo_medio_internacao` | decimal | `valor_total_12m ÷ internacoes_12m`. |
| `variacao_trimestral_pct` | decimal | Último trimestre contra o primeiro da série. |
| `perfil_permanencia` | texto | `Agudos` (< 8 d) · `Permanência elevada` (8 a 20 d) · `Longa permanência` (≥ 20 d) · `Sem internações`. |
| `alerta_capacidade` | texto | `Crítico` (≥ 100%) · `Atenção` (85–100%) · `Adequado` (< 85%) · `Não aplicável` (longa permanência) · `Sem leitos SUS`. |

### Ressalva metodológica sobre `ocupacao_estimada_pct`

O SIH não publica censo diário de leito. A fórmula usada é a aproximação padrão
para dados agregados, e tem dois vieses conhecidos:

- **Superestima** onde há muita internação de curta permanência com alta
  rotatividade (o leito é reocupado no mesmo dia e a conta assume ocupação
  contínua).
- **Subestima** onde há leitos não cadastrados ou em ampliação recente.

O indicador serve para **priorizar**, não para auditar. Um município marcado
como Crítico é um município que merece verificação, não uma conclusão fechada.

### Por que `Longa permanência` fica fora do alerta

Municípios sede de hospital psiquiátrico ou de retaguarda — Itapira (25 dias),
Jaci (98 dias) — apresentam ocupação estruturalmente alta. Incluí-los no
alerta de capacidade faria com que dominassem o topo de qualquer ranking por um
motivo que não é crise assistencial, escondendo os municípios que de fato
precisam de ação.

O corte é 20 dias, não 8: hospitais gerais de maior complexidade (Guarulhos,
8,2 dias) precisam permanecer na análise.

---

## `mv_clusters_municipio` — agrupamento (K-Means)

Um registro por município incluído no modelo (321).

| Campo | Tipo | Descrição |
|---|---|---|
| `cluster` | inteiro | Identificador numérico do grupo. |
| `perfil_cluster` | texto | Nome de negócio: `Polo regional sob pressão`, `Rede local pressionada`, `Sede de hospital regional`, `Rede com folga`. |
| *(atributos do modelo)* | decimal | Os cinco indicadores padronizados usados no agrupamento. |

---

## `mv_ranking_criticidade` — priorização

| Campo | Tipo | Descrição |
|---|---|---|
| `posicao` | inteiro | Colocação no ranking (1 = mais crítico). |
| `indice_criticidade` | decimal | Índice 0–100. Pesos: ocupação 40%, demanda por habitante 25%, escassez de leitos 20%, aceleração recente 15%. |

Normalização min-max entre os **percentis 5 e 95**, para que um outlier não
comprima toda a escala.

---

## `mv_tendencia_municipio` — tendência de demanda

Municípios com ao menos 600 internações no ano (265).

| Campo | Tipo | Descrição |
|---|---|---|
| `media_mensal` | decimal | Média de internações por mês. |
| `inclinacao_mes` | decimal | Coeficiente angular da reta ajustada (internações por mês). |
| `variacao_mensal_pct` | decimal | Inclinação normalizada pela média. Torna municípios de portes diferentes comparáveis. |
| `variacao_anualizada_pct` | decimal | `variacao_mensal_pct × 12`. |
| `r2` | decimal | Qualidade do ajuste (0 a 1). |
| `classificacao` | texto | `Alta forte` · `Alta` · `Estável` · `Queda` · `Queda forte`. |

> **Use sempre o R² como filtro.** Abaixo de 0,4 a variação é oscilação, não
> tendência. Um município com `+48%` e R² 0,14 está balançando em torno da
> média — apresentá-lo como "o que mais cresce" seria erro de leitura, não de
> cálculo.

---

## `cnes_estabelecimentos` — documentos JSON

Coleção nativa do Oracle 23ai. 905 documentos de estabelecimentos hospitalares
dos 45 municípios prioritários (todos em alerta Crítico ou Atenção, mais os
maiores em volume).

Campos relevantes do documento, expostos pela view `vw_cnes_estabelecimentos`:

| Caminho no JSON | Descrição |
|---|---|
| `codigo_cnes` | Identificador nacional do estabelecimento. |
| `nome_fantasia` | Nome pelo qual a unidade é conhecida. |
| `codigo_municipio` | Município — chave de integração (6 dígitos). |
| `codigo_tipo_unidade` | 5 = hospital geral · 7 = hospital especializado · 20/21 = pronto-socorro · 73 = pronto-atendimento. |
| `descricao_esfera_administrativa` | Municipal, estadual, federal ou privada. |
| `estabelecimento_possui_centro_cirurgico` | 0 ou 1. |
| `estabelecimento_possui_centro_obstetrico` | 0 ou 1. |
| `estabelecimento_possui_centro_neonatal` | 0 ou 1. |
| `latitude` / `longitude` | Coordenadas para georreferenciamento. |

Estes três últimos campos booleanos são a razão de a fonte ser JSON: existem em
parte das unidades e ausentes em outra parte. Em colunas fixas produziriam uma
tabela majoritariamente vazia.
