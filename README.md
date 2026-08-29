# PULSO — Painel Único de Leitos, Saúde e Ocupação

**Equipe Vital Analytics · Turma 1TSCOA · Challenge Oracle + FIAP 2026 · Sprint 2**

Painel inteligente de acesso hospitalar construído sobre dados públicos do SUS.
Responde, sem intermediação de analista, as três perguntas que a gestão de saúde
precisa fazer toda semana: **onde a capacidade foi ultrapassada**, **quais perfis
de atendimento pressionam a rede** e **onde a demanda cresce mais rápido**.

O diferencial é a camada **Select AI** do Oracle Autonomous Database 23ai: o
gestor pergunta em português e o banco gera e executa o SQL.

---

## O problema

Uma Secretaria de Saúde tem os dados. O que ela não tem é o caminho entre a
pergunta e a resposta. Hoje esse caminho passa por um analista que escreve SQL,
extrai planilha e devolve dias depois — quando a pergunta já mudou. O resultado
prático é que a decisão de abrir leito, redirecionar ambulância ou realocar
equipe é tomada com o dado do mês passado.

O PULSO encurta esse caminho para uma pergunta em linguagem natural.

---

## Resultados obtidos com dados reais

Recorte do MVP: **estado de São Paulo, 12 meses (jul/2025 a jun/2026)**.
Todos os números abaixo saem das fontes públicas, não são ilustrativos.

| Indicador | Valor |
|---|---|
| Internações SUS processadas | **2.913.953** |
| Recurso executado | **R$ 5.686.834.532** |
| Custo médio por internação | **R$ 1.951,59** |
| Leitos SUS de internação | **55.090** (de 96.589 existentes) |
| Municípios analisados | **645** (346 com rede hospitalar) |
| População de referência | **46.081.801** |
| Permanência média | **5,07 dias** |

**O que o painel encontrou:**

- **15 municípios** operam com ocupação estimada **acima de 100%** da capacidade
  de leitos SUS; outros **31** estão entre 85% e 100%.
- Três capítulos da CID-10 concentram **35,2%** de toda a demanda hospitalar:
  gravidez e parto (369 mil), aparelho digestivo (335 mil) e aparelho
  circulatório (322 mil).
- **20 municípios** apresentam crescimento de demanda estatisticamente
  consistente (R² ≥ 0,5) — Guaratinguetá lidera com **+119% anualizados** e
  R² 0,71.
- O K-Means separou a rede em quatro perfis de gestão distintos, incluindo dois
  municípios pequenos que sediam hospital de referência regional e que qualquer
  análise por porte populacional classificaria errado.

**Aplicação funcionando:** <https://nelsondiniz-p.github.io/pulso-vital-analytics/>

---

## Arquitetura implementada

```
┌── ORIGEM ────────────────────────────────────────────────────────────┐
│                                                                       │
│  SIH/SUS               CNES                    IBGE                   │
│  (DATASUS/TabNet)      (API Dados Abertos)     (Localidades + SIDRA)  │
│  CSV → relacional      JSON → documento        CSV → external table   │
│                                                                       │
└───────────┬───────────────────┬───────────────────┬───────────────────┘
            │                   │                   │
┌───────────▼───────────────────▼───────────────────▼───────────────────┐
│  INGESTÃO E PROCESSAMENTO          Python 3.11 · pandas · urllib      │
│                                                                       │
│  src/etl/tabnet_client.py     cliente do CGI de tabulação do DATASUS  │
│  src/etl/extract_*.py         extração das três fontes                │
│  src/etl/transform.py         conciliação de chaves + modelo estrela  │
│                                                                       │
│  Decisão-chave: as três fontes NÃO compartilham chave. SIH e CNES     │
│  usam o código IBGE de 6 dígitos, o IBGE usa 7 com verificador. A      │
│  integração é sempre por código, nunca por nome de município.          │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│  ARMAZENAMENTO      Oracle Autonomous Database 23ai · Object Storage  │
│                                                                       │
│  dim_municipio              dimensão territorial + capacidade         │
│  fato_internacao_mes        fato mensal (município × mês)             │
│  fato_cid_capitulo          perfil assistencial (CID-10)              │
│  fato_uf_mes                contexto nacional                         │
│  cnes_estabelecimentos      coleção JSON nativa (23ai)                │
│  ext_ibge_populacao         EXTERNAL TABLE sobre o Object Storage     │
│                                                                       │
│  sql/01_ddl_tabelas.sql · sql/02_carga_dados.sql                      │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│  MODELAGEM ANALÍTICA                        scikit-learn · SQL         │
│                                                                       │
│  K-Means (k=4)          agrupa municípios por perfil de pressão       │
│  Índice de criticidade  ranking priorizado 0–100                      │
│  Regressão linear       tendência de demanda em 12 meses              │
│                                                                       │
│  src/analytics/modelos.py · sql/03_views_analiticas.sql               │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│  CONSUMO                                                              │
│                                                                       │
│  Select AI     pergunta em português → SQL gerado → resposta          │
│                sql/04_select_ai.sql · sql/05_perguntas_negocio.sql    │
│                                                                       │
│  Dashboard     painel navegável com filtros e drill-down por município│
│                dashboard/index.html                                    │
└───────────────────────────────────────────────────────────────────────┘
```

Descrição narrativa completa, incluindo o que ficou fora do MVP e por quê:
[`docs/arquitetura.md`](docs/arquitetura.md).

---

## As três fontes e por que cada formato

O desafio exige uso justificado de dados relacionais, semiestruturados e
tabulares. A escolha aqui não é decorativa — cada fonte está no formato que a
natureza dela pede.

| Fonte | Formato | Por que este formato |
|---|---|---|
| **SIH/SUS** — internações, valor pago, permanência, CID-10 | **Relacional** | Fato transacional com grão definido (internação autorizada por AIH), métricas aditivas e dimensões estáveis. É o caso clássico de modelo dimensional, e é o que o Select AI consulta melhor. |
| **CNES** — cadastro de estabelecimentos | **JSON** | O documento tem atributos heterogêneos e opcionais: um hospital de ensino tem centro cirúrgico, obstétrico e neonatal; um pronto-atendimento não tem nenhum. Em colunas fixas viraria tabela esparsa. O 23ai consulta JSON nativamente. |
| **IBGE** — malha municipal e população | **CSV / External Table** | Dado de referência, baixo volume, atualização anual, schema estável. Não há ganho em carregá-lo para dentro do banco: o Oracle lê o arquivo no Object Storage como se fosse tabela, e trocar o CSV atualiza a análise inteira sem recarga. |

Além disso, o CNES entra por **duas rotas**: a API JSON (cadastro) e o TabNet
(leitos de internação por município). A segunda é necessária porque o indicador
central do painel — pressão sobre a rede — exige o denominador de leitos, que
não vem no cadastro básico.

---

## Modelos analíticos

### 1. K-Means — agrupamento por perfil de pressão

Cinco atributos padronizados: internações por mil habitantes, leitos por 10 mil
habitantes, ocupação estimada, permanência média e custo médio. O modelo roda
sobre os **321 municípios** com rede hospitalar e internações registradas —
municípios sem leitos SUS e sedes de hospital de longa permanência ficam fora,
pelos motivos descritos adiante.

| Perfil identificado | Municípios | Ocupação média | Leitos/10 mil hab. |
|---|---:|---:|---:|
| Polo regional sob pressão | 22 | 79,0% | 38,4 |
| Rede local pressionada | 114 | 77,0% | 11,1 |
| Sede de hospital regional | 2 | 76,7% | 117,7 |
| Rede com folga | 183 | 31,2% | 15,6 |

**Silhueta:** 0,35 em k=4. É menor que em k=2 (0,38), e a escolha foi
deliberada: k=2 divide a rede em "cheia" e "vazia", o que não orienta decisão.
Com k=4 aparecem situações que exigem ações opostas — um polo regional lotado
pede regulação de fluxo entre hospitais; uma rede com folga, no mesmo estado,
pede realocação de recurso e não mais leito.

### 2. Índice composto de criticidade

Normalização min-max entre os percentis 5 e 95 (para que um outlier não domine),
com pesos explícitos: ocupação 40%, demanda por habitante 25%, escassez de
leitos 20%, aceleração recente 15%. Não é caixa-preta: o gestor consegue
auditar por que um município subiu no ranking.

### 3. Regressão linear de tendência

Reta ajustada sobre 12 observações mensais por município, com a inclinação
normalizada pela média — o que torna municípios de portes diferentes
comparáveis. **O R² é usado como filtro, não como enfeite:** das 265 séries
ajustadas, apenas 20 têm R² ≥ 0,5. As demais oscilam em torno da média sem
tendência real, e entrariam num ranking ingênuo como "crescimento de +48%"
quando são apenas ruído sazonal.

### Uma decisão de método que mudou o resultado

Municípios com permanência média acima de 20 dias — sedes de hospital
psiquiátrico e de retaguarda, como Itapira e Jaci — são **excluídos** dos
modelos de capacidade. Neles a ocupação alta é estrutural, não é crise
assistencial. Sem esse corte, eles dominavam o topo de qualquer ranking de
ocupação e escondiam os municípios que de fato precisam de ação.

O corte foi calibrado em 20 dias, não em 8: hospitais gerais de maior
complexidade (Guarulhos, por exemplo, com 8,2 dias) precisam permanecer na
análise, porque são exatamente parte da rede que mais importa para o gestor.

---

## Como executar

### Requisitos

Python 3.11+ e acesso à internet (as fontes são consultadas ao vivo).

```bash
git clone https://github.com/nelsondiniz-p/pulso-vital-analytics.git
cd pulso-vital-analytics
pip install -r requirements.txt
```

### Pipeline completo

```bash
python src/run_pipeline.py
```

Executa extração, transformação, modelagem e geração do dashboard. Leva de 12 a
20 minutos — o tempo é dominado pelas consultas ao TabNet, que é um CGI legado
sem paginação.

Para reprocessar sem baixar tudo de novo:

```bash
python src/run_pipeline.py --sem-extracao
```

### Etapas isoladas

```bash
python src/etl/extract_sih.py      # SIH/SUS via TabNet
python src/etl/extract_cnes.py     # CNES: leitos + cadastro JSON
python src/etl/extract_ibge.py     # IBGE: malha e população
python src/etl/transform.py        # integração e indicadores
python src/analytics/modelos.py    # K-Means, índice, tendência
python src/viz/graficos.py         # evidências em PNG
python src/viz/build_dashboard.py  # dashboard navegável
```

### Ambiente Oracle

Os scripts em `sql/` são executados na ordem numérica, no **Database Actions →
SQL** do Autonomous Database:

1. `01_ddl_tabelas.sql` — modelo dimensional
2. `02_carga_dados.sql` — ingestão das três fontes (CSV, JSON, External Table)
3. `03_views_analiticas.sql` — camada de consumo
4. `04_select_ai.sql` — perfil de IA e permissões
5. `05_perguntas_negocio.sql` — as perguntas de gestão, em Select AI e em SQL

Pré-requisitos, validação da carga e diagnóstico da camada Select AI:
[`docs/implantacao_oracle.md`](docs/implantacao_oracle.md).

---

## Estrutura do repositório

```
pulso-vital-analytics/
├── README.md
├── requirements.txt
├── src/
│   ├── run_pipeline.py             orquestrador ponta a ponta
│   ├── etl/
│   │   ├── tabnet_client.py        cliente do CGI de tabulação do DATASUS
│   │   ├── extract_sih.py          fonte relacional
│   │   ├── extract_cnes.py         fonte JSON + leitos
│   │   ├── extract_ibge.py         fonte tabular
│   │   └── transform.py            conciliação e modelo dimensional
│   ├── analytics/
│   │   └── modelos.py              K-Means, índice, regressão
│   └── viz/
│       ├── graficos.py             evidências em PNG
│       ├── build_payload.py        payload do dashboard
│       └── build_dashboard.py      empacotamento da página
├── sql/                            scripts do Autonomous Database (01 a 05)
├── notebooks/
│   └── 01_analise_exploratoria.ipynb
├── data/
│   ├── README.md                   o que há em cada camada
│   ├── raw/                        saída bruta das três fontes
│   └── processed/                  modelo dimensional — é o que carrega no Oracle
├── dashboard/
│   ├── index.html                  aplicação (autocontida)
│   └── dados.json                  payload
└── docs/
    ├── arquitetura.md
    ├── dicionario_dados.md
    ├── implantacao_oracle.md
    └── evidencias/                 gráficos usados no PPT e no pitch
```

---

## Entregáveis da Sprint 2

| Item | Onde está |
|---|---|
| Apresentação (PPT) | `EC_Sprint_2_1TSCO_EvidenciasConstrucao_PULSO_VitalAnalytics.pptx` |
| Vídeo pitch (YouTube) | `link_video_pitch.txt` |
| Aplicação funcionando | <https://nelsondiniz-p.github.io/pulso-vital-analytics/> |
| Repositório técnico | <https://github.com/nelsondiniz-p/pulso-vital-analytics> |
| Evidências visuais | `docs/evidencias/` |
| Dados tratados do projeto | `data/processed/` · `data/raw/` |
| Scripts SQL do Oracle | `sql/` |

---

## Limitações conhecidas

Declaradas de propósito — um MVP que esconde o que não fez é pior do que um que
diz onde está o limite.

- **Ocupação é estimada, não medida.** O SIH não publica censo diário de leito.
  A aproximação usada — `(internações × permanência média) ÷ (leitos × 365)` —
  é o padrão para dados agregados, mas superestima onde há muita internação de
  curta permanência e subestima onde há alta rotatividade não capturada.
- **Só o SUS.** O SIH cobre internações públicas. A rede suplementar não entra,
  o que subestima a capacidade real em municípios com forte presença privada.
- **Defasagem do dado.** Competências recentes do SIH ainda recebem correções
  por até três meses.
- **Recorte estadual.** O MVP cobre São Paulo. A expansão para as demais UFs é
  troca de parâmetro no `tabnet_client`, não mudança de arquitetura.
- **Ingestão manual.** O pipeline roda sob demanda. O agendamento automático
  (OCI Data Integration ou `DBMS_SCHEDULER`) está planejado, não implementado.

---

## Fontes de dados

- **SIH/SUS** — Sistema de Informações Hospitalares do SUS, Ministério da Saúde,
  via TabNet/DATASUS (`tabnet.datasus.gov.br`).
- **CNES** — Cadastro Nacional de Estabelecimentos de Saúde, via API de Dados
  Abertos (`apidadosabertos.saude.gov.br`) e TabNet.
- **IBGE** — Malha municipal (API de Localidades) e população residente estimada
  (SIDRA, tabela 6579).

---

## Equipe

| Integrante | RM | Responsabilidade na Sprint 2 |
|---|---|---|
| Giovanny da Silva Santana | 570646 | Extração e tratamento das três fontes |
| Marco Aurélio da Silva Oliveira | 569185 | Modelos analíticos e validação |
| Nélson Martins Diniz Neto | 573273 | Arquitetura, Oracle e Select AI |
| Pedro Henrique Inocente | 570201 | Dashboard, evidências e vídeo pitch |

---

Projeto acadêmico desenvolvido para o Challenge Oracle + FIAP 2026.
Os dados utilizados são públicos e de livre acesso.
