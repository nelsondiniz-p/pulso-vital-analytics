--------------------------------------------------------------------------------
-- PULSO · Equipe Vital Analytics · 1TSCOB · Challenge Oracle + FIAP 2026
--
-- 02_carga_dados.sql
-- Camada de INGESTÃO: as três fontes entram no Autonomous Database, cada uma
-- pelo mecanismo adequado ao seu formato.
--
--   Fonte 1  SIH/SUS   CSV  -> tabela relacional  (DBMS_CLOUD.COPY_DATA)
--   Fonte 2  CNES      JSON -> coleção de documentos (DBMS_CLOUD.COPY_COLLECTION)
--   Fonte 3  IBGE      CSV  -> EXTERNAL TABLE (arquivo permanece no Object Storage)
--
-- Pré-requisito: subir os arquivos de data/processed e data/raw para um bucket
-- do OCI Object Storage. Alternativa sem bucket: usar o assistente
-- Database Actions -> Data Load -> "Carregar dados do computador" (arrastar os
-- CSV), que executa o equivalente deste script pela interface.
--------------------------------------------------------------------------------

-- =============================================================================
-- 0. CREDENCIAL DE ACESSO AO OBJECT STORAGE
--    O token é gerado em: OCI Console -> Perfil -> Auth Tokens
-- =============================================================================

BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'CRED_OBJ_STORAGE',
    username        => 'SEU_USUARIO_OCI',
    password        => 'SEU_AUTH_TOKEN'
  );
END;
/

-- Endereço base do bucket. Substituir região, namespace e nome do bucket.
-- Formato: https://objectstorage.<regiao>.oraclecloud.com/n/<namespace>/b/<bucket>/o/
DEFINE base_uri = 'https://objectstorage.sa-saopaulo-1.oraclecloud.com/n/SEU_NAMESPACE/b/pulso-dados/o/'

-- =============================================================================
-- 1. FONTE RELACIONAL — SIH/SUS
--    Justificativa do formato: fato transacional com grão definido, métricas
--    aditivas e dimensões estáveis. É o caso clássico de tabela relacional.
-- =============================================================================

BEGIN
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'FATO_INTERNACAO_MES',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.fato_internacao_mes.csv',
    format          => JSON_OBJECT(
                         'type'             VALUE 'csv',
                         'skipheaders'      VALUE '1',
                         'delimiter'        VALUE ',',
                         'characterset'     VALUE 'AL32UTF8',
                         'ignoremissingcolumns' VALUE 'true',
                         'blankasnull'      VALUE 'true'
                       )
  );
END;
/

BEGIN
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'FATO_CID_CAPITULO',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.fato_cid_capitulo.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
END;
/

BEGIN
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'FATO_UF_MES',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.fato_uf_mes.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
END;
/

-- Dimensão e saídas dos modelos seguem o mesmo mecanismo.
BEGIN
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'DIM_MUNICIPIO',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.dim_municipio.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'MV_CLUSTERS_MUNICIPIO',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.mv_clusters_municipio.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'MV_TENDENCIA_MUNICIPIO',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.mv_tendencia_municipio.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
  DBMS_CLOUD.COPY_DATA(
    table_name      => 'MV_RANKING_CRITICIDADE',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.mv_ranking_criticidade.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true')
  );
END;
/

-- Conferência de erros de carga (a view é criada automaticamente quando há rejeições)
-- SELECT * FROM copy$_log ORDER BY log_timestamp DESC FETCH FIRST 20 ROWS ONLY;

-- =============================================================================
-- 2. FONTE SEMIESTRUTURADA — CNES em JSON
--    Justificativa do formato: o cadastro do estabelecimento tem atributos
--    heterogêneos e opcionais (centro cirúrgico, obstétrico, neonatal existem
--    só em parte das unidades). Em colunas fixas seria uma tabela esparsa.
--    O 23ai consulta JSON nativamente, então o documento é guardado como veio.
-- =============================================================================

DROP TABLE cnes_estabelecimentos PURGE;

CREATE TABLE cnes_estabelecimentos (
  id        VARCHAR2(64) DEFAULT SYS_GUID() PRIMARY KEY,
  documento JSON
);

COMMENT ON TABLE cnes_estabelecimentos IS
  'Documentos JSON do CNES, como retornados pela API de Dados Abertos do Ministério da Saúde.';

-- Carga a partir do arquivo JSON Lines (um documento por linha)
BEGIN
  DBMS_CLOUD.COPY_COLLECTION(
    collection_name => 'CNES_ESTABELECIMENTOS',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.cnes_sp_estabelecimentos.jsonl',
    format          => JSON_OBJECT('recorddelimiter' VALUE '''\n''',
                                   'characterset'    VALUE 'AL32UTF8')
  );
END;
/

-- View que "achata" o JSON para consumo analítico. A modelagem fica aqui,
-- não na ingestão: assim mudanças no cadastro do CNES não quebram a carga.
CREATE OR REPLACE VIEW vw_cnes_estabelecimentos AS
SELECT
  j.documento.codigo_cnes.number()                            AS codigo_cnes,
  j.documento.nome_fantasia.string()                          AS nome_fantasia,
  j.documento.nome_razao_social.string()                      AS razao_social,
  TO_CHAR(j.documento.codigo_municipio.number())              AS codigo,
  j.documento.codigo_tipo_unidade.number()                    AS codigo_tipo_unidade,
  j.documento.descricao_turno_atendimento.string()            AS turno_atendimento,
  j.documento.descricao_esfera_administrativa.string()        AS esfera_administrativa,
  j.documento.estabelecimento_possui_centro_cirurgico.number()  AS tem_centro_cirurgico,
  j.documento.estabelecimento_possui_centro_obstetrico.number() AS tem_centro_obstetrico,
  j.documento.estabelecimento_possui_centro_neonatal.number()   AS tem_centro_neonatal,
  j.documento.estabelecimento_possui_atendimento_hospitalar.number() AS tem_atend_hospitalar,
  j.documento.latitude_estabelecimento_decimo_grau.number()   AS latitude,
  j.documento.longitude_estabelecimento_decimo_grau.number()  AS longitude
FROM cnes_estabelecimentos j;

COMMENT ON TABLE vw_cnes_estabelecimentos IS
  'Visão colunar dos documentos JSON do CNES: hospitais e prontos-socorros dos municípios prioritários.';

-- =============================================================================
-- 3. FONTE TABULAR DE REFERÊNCIA — IBGE via EXTERNAL TABLE
--    Justificativa do formato: dado de referência, baixo volume, atualização
--    anual e schema estável. Não há ganho em carregar para dentro do banco -
--    o Oracle lê o arquivo no Object Storage como se fosse tabela. Trocar o
--    CSV atualiza a análise inteira sem recarga.
-- =============================================================================

BEGIN
  DBMS_CLOUD.CREATE_EXTERNAL_TABLE(
    table_name      => 'EXT_IBGE_POPULACAO',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.ibge_sp_populacao.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true'),
    column_list     => 'codigo      VARCHAR2(6),
                        codigo_ibge VARCHAR2(7),
                        municipio   VARCHAR2(120),
                        populacao   NUMBER(10),
                        ano         NUMBER(4)'
  );
END;
/

BEGIN
  DBMS_CLOUD.CREATE_EXTERNAL_TABLE(
    table_name      => 'EXT_IBGE_MUNICIPIOS',
    credential_name => 'CRED_OBJ_STORAGE',
    file_uri_list   => '&base_uri.ibge_sp_municipios.csv',
    format          => JSON_OBJECT('type' VALUE 'csv', 'skipheaders' VALUE '1',
                                   'characterset' VALUE 'AL32UTF8',
                                   'blankasnull' VALUE 'true'),
    column_list     => 'codigo               VARCHAR2(6),
                        codigo_ibge          VARCHAR2(7),
                        municipio            VARCHAR2(120),
                        regiao_imediata      VARCHAR2(120),
                        regiao_intermediaria VARCHAR2(120),
                        mesorregiao          VARCHAR2(120)'
  );
END;
/

-- =============================================================================
-- 4. VALIDAÇÃO DA CARGA
--    Conferir estes números contra os do dashboard antes de seguir.
-- =============================================================================

SELECT 'dim_municipio'          AS tabela, COUNT(*) AS registros FROM dim_municipio
UNION ALL SELECT 'fato_internacao_mes',    COUNT(*) FROM fato_internacao_mes
UNION ALL SELECT 'fato_cid_capitulo',      COUNT(*) FROM fato_cid_capitulo
UNION ALL SELECT 'fato_uf_mes',            COUNT(*) FROM fato_uf_mes
UNION ALL SELECT 'cnes_estabelecimentos',  COUNT(*) FROM cnes_estabelecimentos
UNION ALL SELECT 'ext_ibge_populacao',     COUNT(*) FROM ext_ibge_populacao
UNION ALL SELECT 'mv_clusters_municipio',  COUNT(*) FROM mv_clusters_municipio
UNION ALL SELECT 'mv_tendencia_municipio', COUNT(*) FROM mv_tendencia_municipio
UNION ALL SELECT 'mv_ranking_criticidade', COUNT(*) FROM mv_ranking_criticidade;

-- Totais de controle (devem bater com o painel):
--   internações em 12 meses .......... 2.913.953
--   recurso executado ................ R$ 5.686.834.532
--   leitos SUS ....................... 55.090
--   municípios ....................... 645
SELECT SUM(internacoes)  AS internacoes_12m,
       SUM(valor_total)  AS recurso_executado
FROM   fato_internacao_mes;

COMMIT;
