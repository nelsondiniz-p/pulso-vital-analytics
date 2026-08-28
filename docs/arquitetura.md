# PULSO — Arquitetura da solução

**Equipe Vital Analytics · 1TSCOA · Challenge Oracle + FIAP 2026 · Sprint 2**

Este documento descreve a arquitetura **final implementada**, separando com
clareza o que foi construído do que ficou planejado para a próxima evolução.

---

## 1. Visão em camadas

A solução tem cinco camadas. O dado entra por fontes públicas heterogêneas e sai
como resposta em linguagem natural.

### Camada 1 — Origem dos dados

| Fonte | Conteúdo | Acesso | Formato |
|---|---|---|---|
| SIH/SUS | Internações, valor pago, permanência média, capítulo CID-10 | TabNet/DATASUS (CGI de tabulação) | CSV derivado |
| CNES | Cadastro de estabelecimentos hospitalares | API de Dados Abertos do Ministério da Saúde | JSON |
| CNES | Leitos de internação por município | TabNet/DATASUS | CSV derivado |
| IBGE | Malha municipal e hierarquia territorial | API de Localidades | JSON → CSV |
| IBGE | População residente estimada | SIDRA, tabela 6579 | JSON → CSV |

**Obstáculo técnico real e como foi resolvido.** O DATASUS não publica API REST
para o SIH. A via oficial é o TabNet: um CGI dos anos 2000 que responde HTML 3.2
em ISO-8859-1, com tags `<TR>` e `<TD>` não fechadas, números em formato
brasileiro e ausências marcadas com hífen. O download direto dos microdados
(`.dbc`) por FTP não estava acessível a partir do ambiente de execução.

A solução foi escrever um cliente próprio (`src/etl/tabnet_client.py`) que lê o
formulário de definição do cubo, descobre dimensões e medidas disponíveis, monta
o POST correto e faz varredura tolerante do HTML. O resultado é uma interface
programática sobre uma fonte que não foi feita para ser consumida por programa:

```python
tn = TabNet("sih/cnv/nisp.def")
cabecalho, linhas = tn.tabular(
    linha="Município",
    coluna="Ano/mês_processamento",
    incremento="Internações",
    n_arquivos=12,
)
```

Isso é o que tornou possível trabalhar com dados reais em vez de amostra
ilustrativa.

### Camada 2 — Ingestão e processamento

Python 3.11 com pandas. A extração usa apenas a biblioteca padrão (`urllib`),
decisão tomada porque o TabNet exige controle fino de encoding e corpo de POST,
o que fica mais legível sem camada de abstração.

**O problema central desta camada é de integração, não de volume.** As três
fontes não compartilham chave primária:

- SIH/SUS e CNES usam o código IBGE de **6 dígitos** (`350010`)
- IBGE usa o código de **7 dígitos** com dígito verificador (`3500105`)
- Os nomes divergem em acentuação e caixa (`SAO PAULO` × `São Paulo`)

A conciliação é feita **sempre pelo código truncado em 6 dígitos, nunca por
nome**. Integrar por nome é o erro clássico nesse tipo de projeto: perde
municípios homônimos, quebra em acentuação e falha silenciosamente — a linha
some do resultado sem erro nenhum.

Para exibição, prevalece a grafia oficial do IBGE, que é acentuada.

### Camada 3 — Armazenamento

Oracle Autonomous Database 23ai, esquema estrela.

```
                    ┌──────────────────────┐
                    │    dim_municipio     │
                    │  ────────────────    │
                    │  codigo (PK)         │
                    │  municipio           │
                    │  regiao_intermediaria│
                    │  populacao           │
                    │  leitos_sus          │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼──────────┐  ┌────────▼─────────┐  ┌─────────▼──────────┐
│fato_internacao_  │  │ fato_cid_capitulo│  │  cnes_estabeleci-  │
│      mes         │  │  ──────────────  │  │      mentos        │
│  ──────────────  │  │  codigo (FK)     │  │  ──────────────    │
│  codigo (FK)     │  │  codigo_capitulo │  │  documento JSON    │
│  periodo         │  │  capitulo_cid10  │  │                    │
│  internacoes     │  │  internacoes     │  │  (coleção nativa   │
│  valor_total     │  │                  │  │   do 23ai)         │
│  media_permanen. │  └──────────────────┘  └────────────────────┘
└──────────────────┘

        ┌──────────────────────────────────────────┐
        │  ext_ibge_populacao / ext_ibge_municipios│
        │  EXTERNAL TABLE sobre o Object Storage   │
        │  (o arquivo permanece fora do banco)     │
        └──────────────────────────────────────────┘
```

**Por que dimensional e não normalizado.** Todas as perguntas do PULSO são
analíticas — "quanto", "onde", "em que período". Nenhuma é transacional. Um
esquema estrela com dimensão territorial única e fatos aditivos é o que permite
ao Select AI gerar SQL correto sem precisar navegar joins profundos, que é
exatamente onde a geração automática de SQL costuma errar.

**Três mecanismos de ingestão, um por natureza de dado:**

| Mecanismo | Fonte | Justificativa |
|---|---|---|
| `DBMS_CLOUD.COPY_DATA` | SIH/SUS (CSV) | Fato com grão definido e métricas aditivas: pertence a tabela relacional. |
| `DBMS_CLOUD.COPY_COLLECTION` | CNES (JSON) | Documento com atributos opcionais e heterogêneos; em colunas fixas viraria tabela esparsa. O 23ai consulta JSON nativamente. |
| `DBMS_CLOUD.CREATE_EXTERNAL_TABLE` | IBGE (CSV) | Dado de referência, anual, schema estável. Trocar o arquivo atualiza a análise inteira sem recarga. |

### Camada 4 — Modelagem analítica

Três técnicas, cada uma respondendo a uma pergunta de gestão específica.
Detalhamento em [`../README.md`](../README.md#modelos-analíticos).

| Técnica | Biblioteca | Pergunta que responde |
|---|---|---|
| K-Means (k=4) | scikit-learn | Quais municípios se parecem em pressão assistencial? |
| Índice composto | pandas / NumPy | Por onde a Secretaria deve começar? |
| Regressão linear | NumPy | Onde a demanda cresce de verdade? |

Os resultados são persistidos como tabelas no Autonomous Database
(`mv_clusters_municipio`, `mv_ranking_criticidade`, `mv_tendencia_municipio`),
porque o Select AI precisa poder consultá-los como qualquer outro objeto.

**Decisão que separou modelo de ruído.** A regressão devolve inclinação e R².
Usar só a inclinação produziria um ranking que premia a série mais instável: um
município com +48% de "crescimento" e R² 0,14 está oscilando, não crescendo. O
painel filtra por R² ≥ 0,4 em todo lugar onde apresenta tendência.

### Camada 5 — Consumo

**Select AI.** O gestor pergunta em português; o `DBMS_CLOUD_AI` gera o SQL, o
banco executa e devolve o resultado. O modificador `showsql` expõe a consulta
gerada — o que serve tanto para auditoria quanto para evidência de avaliação.

O `object_list` do perfil é deliberadamente enxuto: oito views de negócio, não
as tabelas cruas. Quanto menos objetos e mais claros os nomes, melhor o SQL
gerado. O atributo `"comments": "true"` faz a IA ler os `COMMENT ON` do
esquema — é o que permite a ela entender que `ocupacao_estimada_pct` acima de
100 significa capacidade ultrapassada, sem que isso esteja na pergunta.

**Dashboard.** Página autocontida, sem servidor e sem dependência externa, com
quatro visões: geral, municípios com drill-down, "Pergunte ao PULSO" e modelos
analíticos. Roda em GitHub Pages e funciona offline — requisito prático para a
demonstração do vídeo pitch, que não pode depender de rede.

---

## 2. Fluxo do dado ponta a ponta

```
 [1] TabNet SIH/SUS ──┐
     API CNES ────────┼──> extract_*.py ──> data/raw/*.csv, *.jsonl
     API IBGE ────────┘         │
                                │
 [2]                            ▼
     transform.py ──> conciliação por código IBGE de 6 dígitos
                  ──> dim_municipio + 3 tabelas fato
                  ──> indicadores de gestão (ocupação, giro, custo)
                                │
 [3]                            ▼
     modelos.py ──> K-Means ──────────> mv_clusters_municipio
                ──> índice composto ──> mv_ranking_criticidade
                ──> regressão linear ─> mv_tendencia_municipio
                                │
 [4]                            ▼
     Object Storage ──> DBMS_CLOUD.COPY_DATA / COPY_COLLECTION
                                │        CREATE_EXTERNAL_TABLE
                                ▼
                    Autonomous Database 23ai
                                │
 [5]                            ▼
     views analíticas ──> Select AI ──> resposta em português
                      └─> dashboard ──> painel navegável
```

**Exemplo concreto de um dado percorrendo o caminho.** A internação de um
paciente em Jundiaí em março de 2026 é agregada pelo TabNet no total mensal do
município; é extraída pelo `extract_sih.py` como uma linha
`(350340, 2026-03, internações)`; é conciliada com a população do IBGE e com os
443 leitos SUS do CNES; entra no cálculo de ocupação estimada, que resulta em
105,0% e classifica o município como **Crítico**; alimenta o K-Means, que o
agrupa em "Rede local pressionada"; e chega ao gestor quando ele pergunta
*"quais municípios estão com a capacidade ultrapassada"* e Jundiaí aparece na
resposta com a consulta SQL que a produziu.

---

## 3. O que foi implementado e o que não foi

### Implementado no MVP

- [x] Extração automatizada das três fontes públicas, com cliente próprio para o TabNet
- [x] Conciliação de chaves entre fontes heterogêneas
- [x] Modelo dimensional (1 dimensão, 3 fatos) com DDL e comentários
- [x] Ingestão nos três mecanismos do Oracle (COPY_DATA, COPY_COLLECTION, EXTERNAL TABLE)
- [x] Indicadores de gestão: ocupação estimada, giro de leito, demanda por habitante, custo médio, alerta de capacidade
- [x] Três modelos analíticos com métricas de avaliação
- [x] Views analíticas de consumo
- [x] Perfil Select AI com oito objetos e sete perguntas de negócio
- [x] Dashboard navegável com filtros, ordenação e drill-down por município
- [x] Evidências visuais reprodutíveis

### Planejado para a próxima evolução

| Item | Como está planejado |
|---|---|
| **Ingestão agendada** | `DBMS_SCHEDULER` no Autonomous Database disparando o pipeline mensalmente, na competência de fechamento do SIH. A alternativa é OCI Data Integration com trigger no Object Storage. |
| **Cobertura nacional** | O `tabnet_client` já é genérico: trocar `sih/cnv/nisp.def` pelo cubo da UF desejada replica todo o pipeline. O custo é tempo de extração, não mudança de arquitetura. |
| **Modelo preditivo** | Previsão de demanda por município com Oracle AutoML (`DBMS_DATA_MINING`), usando as 12 observações mensais como base e expandindo a janela para 36 meses. Não entrou no MVP porque 12 pontos são poucos para validar previsão com honestidade. |
| **Ocupação medida** | Substituir a estimativa pelo censo diário de leitos, quando houver integração com sistema de regulação estadual (CROSS, em São Paulo). |
| **Alertas ativos** | Notificação ao gestor quando um município cruza o limite de 85%, em vez de exigir consulta ao painel. |
| **Autenticação por perfil** | Oracle APEX com controle de acesso por região de saúde, para que cada gestor veja o próprio território. |

---

## 4. Tecnologias e o papel de cada uma

| Tecnologia | Camada | Papel |
|---|---|---|
| Python 3.11 | Ingestão, processamento | Orquestração do pipeline |
| pandas / NumPy | Processamento | Conciliação, agregação, cálculo de indicadores |
| scikit-learn | Modelagem | K-Means, padronização, métrica de silhueta |
| matplotlib | Visualização | Geração das evidências estáticas |
| Oracle Autonomous Database 23ai | Armazenamento, consumo | Persistência relacional e JSON nativo |
| OCI Object Storage | Armazenamento | Camada de arquivos para COPY_DATA e External Table |
| DBMS_CLOUD | Ingestão | Carga CSV, JSON e criação de tabelas externas |
| DBMS_CLOUD_AI (Select AI) | Consumo | Tradução de pergunta em português para SQL |
| SQL / PL-SQL | Modelagem, consumo | DDL, views analíticas, perguntas de negócio |
| HTML / CSS / JavaScript | Consumo | Dashboard autocontido, sem framework |
| GitHub Pages | Publicação | Hospedagem da aplicação |
