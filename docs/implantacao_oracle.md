# Implantação da camada Oracle

**PULSO · Equipe Vital Analytics · 1TSCOB**

Como colocar o modelo de dados e a camada Select AI no ar em um Oracle
Autonomous Database 23ai. O pipeline em Python produz os arquivos; este
documento cobre o que acontece depois deles.

---

## Pré-requisitos

| Item | Observação |
|---|---|
| Autonomous Database 23ai | Workload **Data Warehouse**. O tier Always Free atende ao volume do MVP (3.847 linhas no fato mensal, 905 documentos JSON). |
| Acesso ao Database Actions | É a interface web do banco. Não é necessário instalar SQL Developer. |
| Saída de `data/processed/` | Gerada por `python src/run_pipeline.py`. |
| Provedor de IA | OpenAI ou OCI Generative AI — apenas para a camada Select AI. O modelo de dados e as views funcionam sem ele. |

---

## Ordem de execução

Os scripts são idempotentes e devem ser executados na ordem numérica, com
**Run Script** (não com o *play* simples, que executa apenas a linha
selecionada).

```
sql/01_ddl_tabelas.sql        modelo dimensional + comentários de esquema
sql/02_carga_dados.sql        ingestão nos três mecanismos
sql/03_views_analiticas.sql   camada de consumo
sql/04_select_ai.sql          perfil de IA e permissões de rede
sql/05_perguntas_negocio.sql  perguntas de negócio, em Select AI e em SQL
```

Os `DROP TABLE` no início do script `01` falham na primeira execução, porque as
tabelas ainda não existem. É esperado — o script segue adiante.

---

## Ingestão: dois caminhos

O script `02` assume que os arquivos estão em um bucket do OCI Object Storage,
que é o desenho de produção. Ele espera uma credencial (`CRED_OBJ_STORAGE`,
criada com um Auth Token) e o `base_uri` do bucket.

Para uma implantação rápida sem bucket, o **Database Actions → Data Load →
From Local File** executa o equivalente pela interface: os CSV de
`data/processed/` viram tabelas relacionais e o `cnes_sp_estabelecimentos.jsonl`
vira a coleção JSON. A External Table do IBGE é o único objeto que exige
Object Storage, por definição — ela lê o arquivo onde ele está.

Em qualquer um dos caminhos, o *characterset* precisa ser `AL32UTF8`: os
arquivos do pipeline são gravados em UTF-8, e o padrão do assistente nem sempre
é esse.

---

## Validação da carga

Rode ao final do script `02` e confira contra os números do painel:

```sql
SELECT COUNT(*) AS linhas, SUM(internacoes) AS internacoes
FROM   fato_internacao_mes;
-- esperado: 3.847 linhas · 2.913.953 internações
```

```sql
SELECT COUNT(*) FROM mv_indicadores_municipio;
-- esperado: 645 municípios (após o script 03)
```

Se os números não baterem, a carga foi parcial — a view `copy$_log` registra as
linhas rejeitadas e o motivo de cada uma.

---

## Select AI

### O que a camada precisa

O Autonomous bloqueia chamadas de rede externas por padrão. Sem liberar o host
do provedor, toda consulta `SELECT AI` falha com `ORA-24247`:

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

Para OCI Generative AI, o host é
`inference.generativeai.<regiao>.oci.oraclecloud.com`.

### Por que o perfil é enxuto

O `object_list` do perfil expõe **oito views de negócio**, não as tabelas cruas.
Essa é uma decisão de projeto, não uma limitação: quanto menos objetos e mais
claros os nomes, menor a ambiguidade e melhor o SQL gerado. O atributo
`"comments": "true"` faz a IA ler os `COMMENT ON` do esquema — é o que permite a
ela entender que ocupação acima de 100% significa capacidade ultrapassada sem
que isso esteja escrito na pergunta.

### Verificação

```sql
SELECT AI showsql 'quais municipios estao com a capacidade hospitalar ultrapassada';
```

O modificador `showsql` devolve a consulta gerada em vez de executá-la. O
arquivo `sql/05_perguntas_negocio.sql` traz, abaixo de cada pergunta, o SQL
equivalente escrito à mão — a comparação entre os dois é o mecanismo de
auditoria da camada.

---

## Diagnóstico

| Sintoma | Causa | Correção |
|---|---|---|
| `ORA-24247: network access denied` | ACL de rede não configurada | Executar o `APPEND_HOST_ACE` acima |
| `ORA-20404: object not found` | Nome no `object_list` diverge do objeto real | Conferir maiúsculas e minúsculas dos nomes |
| SQL gerado incorreto | Esquema sem comentários descritivos | Confirmar que os `COMMENT ON` do script `01` foram aplicados |
| Resposta vazia ou inconsistente | `object_list` amplo demais | Reduzir a três ou quatro views e reavaliar |
| Erro de caractere na carga | Encoding diferente de UTF-8 | Definir `characterset` como `AL32UTF8` |
| Contagens abaixo do esperado | Carga parcial | Consultar `copy$_log` e recarregar o arquivo rejeitado |

---

## Nota sobre o ambiente Always Free

Uma instância Always Free sem acesso por sete dias é recuperada automaticamente
pela Oracle. Para uma implantação de demonstração, vale provisionar próximo ao
uso e manter acesso periódico.
