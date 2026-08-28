# Guia de provisionamento — Oracle Autonomous Database + Select AI

**PULSO · Equipe Vital Analytics · 1TSCOA**

Passo a passo para colocar o ambiente Oracle no ar e capturar as evidências.
Tempo estimado: **60 a 90 minutos**, sem instalar nada na máquina.

Cada etapa traz o que fazer **quando dá errado** — é onde a maioria trava.

---

## Etapa 1 — Conta Oracle Cloud (≈ 15 min)

1. Acesse **oracle.com/cloud/free** e crie uma conta.
2. Escolha a região **South America East (São Paulo)** — menor latência e é onde
   o Always Free costuma ter capacidade.
3. O cartão de crédito é pedido apenas para validação de identidade. O tier
   Always Free não gera cobrança.

**Se travar:** a validação de cartão às vezes recusa cartões virtuais. Use um
cartão físico. A conta leva de 5 a 20 minutos para ser liberada após o cadastro.

---

## Etapa 2 — Provisionar o Autonomous Database (≈ 10 min)

1. No console OCI: **Menu → Oracle Database → Autonomous Database**.
2. **Create Autonomous Database**.
3. Configuração:

   | Campo | Valor |
   |---|---|
   | Display name | `PULSO` |
   | Database name | `PULSO` |
   | Workload type | **Data Warehouse** |
   | Deployment | Serverless |
   | Configure database | marque **Always Free** |
   | Database version | **23ai** |
   | Password ADMIN | anote — não há recuperação simples |
   | Network access | **Secure access from everywhere** |

4. **Create**. O provisionamento leva de 2 a 5 minutos.

**Se travar:** se "Always Free" estiver indisponível na região, a capacidade
gratuita daquela região esgotou. Troque para outra região (Ashburn ou Phoenix
funcionam) — a latência não afeta o projeto.

> **Não derrube a instância.** Uma Always Free parada por mais de 7 dias é
> recuperada automaticamente pela Oracle. Provisione perto da entrega e acesse
> ao menos uma vez a cada poucos dias.

---

## Etapa 3 — Criar as tabelas (≈ 5 min)

1. Na página do banco: **Database Actions → SQL**.
2. Abra `sql/01_ddl_tabelas.sql`, cole o conteúdo e execute com **Run Script**
   (o ícone de "play" com folha, não o "play" simples — este roda só a linha
   selecionada).
3. Confirme que as tabelas apareceram no navegador de objetos à esquerda.

**Se travar:** os `DROP TABLE` no início falham na primeira execução, porque as
tabelas ainda não existem. É esperado — o script segue adiante.

---

## Etapa 4 — Carregar os dados (≈ 20 min)

Há dois caminhos. **O caminho B é mais rápido e não exige bucket.**

### Caminho A — Object Storage (mais próximo de produção)

1. **Menu → Storage → Buckets → Create Bucket**, nome `pulso-dados`.
2. Suba os arquivos de `data/processed/` (todos os `.csv`) e
   `data/raw/cnes_sp_estabelecimentos.jsonl`.
3. Gere um Auth Token: **ícone de perfil → My profile → Auth tokens → Generate**.
   Copie o token — ele só aparece uma vez.
4. Descubra seu namespace: **Menu → Storage → Buckets**, coluna *Namespace*.
5. Edite `sql/02_carga_dados.sql` substituindo `SEU_USUARIO_OCI`,
   `SEU_AUTH_TOKEN`, `SEU_NAMESPACE` e a região no `base_uri`.
6. Execute o script.

### Caminho B — Data Load pelo navegador (mais rápido)

1. **Database Actions → Data Load → Load Data → From Local File**.
2. Arraste os CSVs de `data/processed/`.
3. Para cada arquivo, confira o mapeamento de colunas e clique em **Run**.
4. Para o JSON do CNES, use a aba **Load JSON** apontando para
   `cnes_sp_estabelecimentos.jsonl`.

**Se travar:** erro de caractere inválido geralmente é encoding. Confirme que o
formato está como `AL32UTF8` — os arquivos do pipeline são gravados em UTF-8.

### Validação obrigatória

Rode ao final e confira contra o painel:

```sql
SELECT COUNT(*) AS municipios,
       SUM(internacoes) AS internacoes
FROM   fato_internacao_mes;
-- esperado: 3847 linhas, 2.913.953 internações
```

Se os números não baterem, a carga foi parcial. Verifique `copy$_log`.

---

## Etapa 5 — Criar as views (≈ 2 min)

Execute `sql/03_views_analiticas.sql` com **Run Script**.

Confira:

```sql
SELECT COUNT(*) FROM mv_indicadores_municipio;  -- esperado: 645
```

---

## Etapa 6 — Configurar o Select AI (≈ 20 min)

Esta é a etapa que mais trava. Vá com calma.

### 6.1 — Escolher o provedor de IA

| Opção | Vantagem | Desvantagem |
|---|---|---|
| **OpenAI** | Configuração em 3 minutos, só precisa de uma API key | Custo por chamada (centavos), exige conta externa |
| **OCI Generative AI** | Fica dentro do ecossistema Oracle — ponto positivo na avaliação | Configuração mais longa (exige OCID, chave privada, fingerprint) |

Para o MVP, **OpenAI é o caminho de menor risco**. Se sobrar tempo, migrar para
OCI Generative AI vale como diferencial de aderência ao parceiro.

### 6.2 — Liberar a saída de rede

O Autonomous bloqueia chamadas externas por padrão. Sem este passo o Select AI
falha com erro de rede:

```sql
BEGIN
  DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
    host => 'api.openai.com',
    ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                        principal_name => 'ADMIN',
                        principal_type => xs_acl.ptype_db)
  );
END;
/
```

### 6.3 — Executar o script

Edite `sql/04_select_ai.sql` colocando sua API key e execute.

### 6.4 — Testar

```sql
SELECT AI 'quantos municipios estao com a capacidade hospitalar ultrapassada';
```

**Se travar:**

| Erro | Causa provável | Solução |
|---|---|---|
| `ORA-24247: network access denied` | ACL não configurada | Repita o passo 6.2 |
| `ORA-20404: object not found` | Nome no `object_list` diferente do objeto real | Confira maiúsculas/minúsculas dos nomes |
| SQL gerado errado | Poucos comentários no esquema | Confirme que os `COMMENT ON` do script 01 rodaram |
| Resposta vazia | `object_list` grande demais | Reduza para 3 ou 4 views e teste de novo |

---

## Etapa 7 — Capturar as evidências (≈ 15 min)

Estas capturas vão para o PPT (5ª entrega) e para o vídeo pitch. Tire todas.

| # | O que capturar | Onde |
|---|---|---|
| 1 | Console OCI mostrando o ADB `PULSO` com status **AVAILABLE** | Autonomous Database |
| 2 | Navegador de objetos com as tabelas criadas | Database Actions → SQL |
| 3 | Resultado da consulta de validação (contagens) | SQL Worksheet |
| 4 | `SELECT AI showsql` mostrando o SQL gerado | SQL Worksheet |
| 5 | `SELECT AI narrate` com resposta em português | SQL Worksheet |
| 6 | Data Load concluído com os arquivos carregados | Database Actions → Data Load |
| 7 | Consulta ao JSON do CNES retornando resultado | SQL Worksheet |

**A captura 4 é a mais importante do projeto.** É ela que prova o diferencial:
pergunta em português entrando, SQL saindo. Deixe a pergunta e o SQL gerado
visíveis na mesma tela.

Salve tudo em `docs/evidencias/` com nomes descritivos
(`oracle_01_adb_provisionado.png`, `oracle_04_selectai_showsql.png`).

---

## Etapa 8 — Executar as perguntas de negócio

Rode `sql/05_perguntas_negocio.sql` bloco a bloco. Cada pergunta traz o SQL
equivalente escrito à mão logo abaixo — compare o que a IA gerou com ele.

Quando divergirem, o valor está na explicação: mostrar na banca que vocês sabem
**verificar** o que a IA gerou é mais forte do que mostrar que ela acertou.

---

## Ordem de execução resumida

```
1. Conta Oracle Cloud Always Free
2. Autonomous Database 23ai, workload Data Warehouse
3. sql/01_ddl_tabelas.sql          → cria o modelo dimensional
4. Data Load ou sql/02_carga_dados.sql → carrega as três fontes
5. sql/03_views_analiticas.sql     → cria a camada de consumo
6. APPEND_HOST_ACE                 → libera a rede
7. sql/04_select_ai.sql            → cria o perfil de IA
8. sql/05_perguntas_negocio.sql    → executa e captura as evidências
```
