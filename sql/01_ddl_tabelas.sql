--------------------------------------------------------------------------------
-- PULSO - Painel Único de Leitos, Saúde e Ocupação
-- Equipe Vital Analytics · Turma 1TSCOB · Challenge Oracle + FIAP 2026
--
-- 01_ddl_tabelas.sql
-- Camada de PERSISTÊNCIA: modelo dimensional (esquema estrela) no
-- Oracle Autonomous Database 23ai.
--
-- Por que modelo dimensional e não normalizado: as perguntas do PULSO são
-- todas analíticas ("quanto", "onde", "em que período"), nunca transacionais.
-- Um esquema estrela com uma dimensão territorial e fatos aditivos é o que
-- permite ao Select AI gerar SQL correto sem precisar navegar joins profundos.
--
-- Executar em: Database Actions -> SQL (usuário ADMIN)
--------------------------------------------------------------------------------

-- =============================================================================
-- DIMENSÃO
-- =============================================================================

DROP TABLE dim_municipio CASCADE CONSTRAINTS PURGE;

CREATE TABLE dim_municipio (
  codigo                VARCHAR2(6)    NOT NULL,
  codigo_ibge           VARCHAR2(7),
  municipio             VARCHAR2(120)  NOT NULL,
  regiao_imediata       VARCHAR2(120),
  regiao_intermediaria  VARCHAR2(120),
  mesorregiao           VARCHAR2(120),
  populacao             NUMBER(10),
  ano_populacao         NUMBER(4),
  leitos_existentes     NUMBER(8),
  leitos_sus            NUMBER(8),
  leitos_sus_10k_hab    NUMBER(10,2),
  tem_rede_hospitalar   VARCHAR2(5),
  CONSTRAINT pk_dim_municipio PRIMARY KEY (codigo)
);

COMMENT ON TABLE  dim_municipio IS
  'Dimensão territorial: um registro por município de São Paulo. Integra malha e população do IBGE com capacidade instalada do CNES.';
COMMENT ON COLUMN dim_municipio.codigo IS
  'Código IBGE de 6 dígitos. É a chave de integração entre SIH/SUS, CNES e IBGE.';
COMMENT ON COLUMN dim_municipio.leitos_sus IS
  'Leitos de internação disponíveis ao SUS, competência mais recente do CNES.';
COMMENT ON COLUMN dim_municipio.leitos_sus_10k_hab IS
  'Oferta de leitos SUS por 10 mil habitantes. Indicador de densidade assistencial.';

-- =============================================================================
-- FATOS
-- =============================================================================

DROP TABLE fato_internacao_mes CASCADE CONSTRAINTS PURGE;

CREATE TABLE fato_internacao_mes (
  codigo                  VARCHAR2(6)   NOT NULL,
  periodo                 VARCHAR2(7)   NOT NULL,   -- AAAA-MM
  internacoes             NUMBER(10),
  valor_total             NUMBER(16,2),
  media_permanencia       NUMBER(8,2),
  custo_medio_internacao  NUMBER(12,2),
  CONSTRAINT pk_fato_internacao PRIMARY KEY (codigo, periodo),
  CONSTRAINT fk_fato_internacao_mun FOREIGN KEY (codigo)
    REFERENCES dim_municipio (codigo)
);

COMMENT ON TABLE  fato_internacao_mes IS
  'Fato mensal de internações do SIH/SUS por município de internação. Grão: município x mês.';
COMMENT ON COLUMN fato_internacao_mes.valor_total IS
  'Valor total pago pelas AIH no período, em reais.';
COMMENT ON COLUMN fato_internacao_mes.media_permanencia IS
  'Permanência média em dias. Entra no cálculo da ocupação estimada.';

DROP TABLE fato_cid_capitulo CASCADE CONSTRAINTS PURGE;

CREATE TABLE fato_cid_capitulo (
  codigo           VARCHAR2(6)    NOT NULL,
  codigo_capitulo  VARCHAR2(10)   NOT NULL,
  capitulo_cid10   VARCHAR2(120),
  internacoes      NUMBER(10),
  CONSTRAINT pk_fato_cid PRIMARY KEY (codigo, codigo_capitulo),
  CONSTRAINT fk_fato_cid_mun FOREIGN KEY (codigo)
    REFERENCES dim_municipio (codigo)
);

COMMENT ON TABLE fato_cid_capitulo IS
  'Perfil assistencial: internações por capítulo da CID-10 em 12 meses. Responde "quais perfis de atendimento pressionam a rede".';

DROP TABLE fato_uf_mes CASCADE CONSTRAINTS PURGE;

CREATE TABLE fato_uf_mes (
  codigo       VARCHAR2(6),
  uf           VARCHAR2(60)  NOT NULL,
  periodo      VARCHAR2(7)   NOT NULL,
  internacoes  NUMBER(12),
  CONSTRAINT pk_fato_uf PRIMARY KEY (uf, periodo)
);

COMMENT ON TABLE fato_uf_mes IS
  'Fato nacional por unidade da federação. Dá o contexto de comparação para o recorte paulista.';

-- =============================================================================
-- SAÍDAS DOS MODELOS ANALÍTICOS
-- Persistidas como tabelas porque são o resultado de processamento em Python
-- (scikit-learn) que roda fora do banco. O Select AI consulta o resultado.
-- =============================================================================

DROP TABLE mv_clusters_municipio CASCADE CONSTRAINTS PURGE;

CREATE TABLE mv_clusters_municipio (
  codigo                  VARCHAR2(6)   NOT NULL,
  municipio               VARCHAR2(120),
  cluster                 NUMBER(3),
  perfil_cluster          VARCHAR2(60),
  internacoes_mil_hab     NUMBER(12,2),
  leitos_sus_10k_hab      NUMBER(10,2),
  ocupacao_estimada_pct   NUMBER(8,2),
  media_permanencia       NUMBER(8,2),
  custo_medio_internacao  NUMBER(12,2),
  internacoes_12m         NUMBER(12),
  leitos_sus              NUMBER(8),
  populacao               NUMBER(10),
  alerta_capacidade       VARCHAR2(30),
  CONSTRAINT pk_mv_clusters PRIMARY KEY (codigo)
);

COMMENT ON TABLE mv_clusters_municipio IS
  'Resultado do K-Means: agrupamento de municípios por perfil de pressão assistencial.';
COMMENT ON COLUMN mv_clusters_municipio.perfil_cluster IS
  'Nome de negócio do grupo: Polo regional sob pressão, Rede local pressionada, Sede de hospital regional, Rede com folga.';

DROP TABLE mv_tendencia_municipio CASCADE CONSTRAINTS PURGE;

CREATE TABLE mv_tendencia_municipio (
  codigo                   VARCHAR2(6)  NOT NULL,
  municipio                VARCHAR2(120),
  media_mensal             NUMBER(12,2),
  inclinacao_mes           NUMBER(12,2),
  variacao_mensal_pct      NUMBER(8,2),
  variacao_anualizada_pct  NUMBER(8,2),
  r2                       NUMBER(5,3),
  classificacao            VARCHAR2(30),
  populacao                NUMBER(10),
  internacoes_12m          NUMBER(12),
  ocupacao_estimada_pct    NUMBER(8,2),
  alerta_capacidade        VARCHAR2(30),
  CONSTRAINT pk_mv_tendencia PRIMARY KEY (codigo)
);

COMMENT ON TABLE mv_tendencia_municipio IS
  'Resultado da regressão linear sobre 12 meses. Responde "onde as internações crescem mais rápido".';
COMMENT ON COLUMN mv_tendencia_municipio.r2 IS
  'Qualidade do ajuste (0 a 1). Abaixo de 0,4 a variação é oscilação, não tendência - use sempre como filtro.';

DROP TABLE mv_ranking_criticidade CASCADE CONSTRAINTS PURGE;

CREATE TABLE mv_ranking_criticidade (
  posicao                  NUMBER(5),
  codigo                   VARCHAR2(6)  NOT NULL,
  municipio                VARCHAR2(120),
  indice_criticidade       NUMBER(6,2),
  ocupacao_estimada_pct    NUMBER(8,2),
  internacoes_mil_hab      NUMBER(12,2),
  leitos_sus_10k_hab       NUMBER(10,2),
  variacao_trimestral_pct  NUMBER(8,2),
  internacoes_12m          NUMBER(12),
  leitos_sus               NUMBER(8),
  populacao                NUMBER(10),
  perfil_dominante         VARCHAR2(120),
  alerta_capacidade        VARCHAR2(30),
  CONSTRAINT pk_mv_ranking PRIMARY KEY (codigo)
);

COMMENT ON TABLE mv_ranking_criticidade IS
  'Índice composto 0-100 que prioriza onde a Secretaria deve agir primeiro.';

-- =============================================================================
-- ÍNDICES DE APOIO ÀS CONSULTAS DO PAINEL
-- =============================================================================

CREATE INDEX ix_fato_intern_periodo ON fato_internacao_mes (periodo);
CREATE INDEX ix_dim_regiao          ON dim_municipio (regiao_intermediaria);
CREATE INDEX ix_mv_rank_indice      ON mv_ranking_criticidade (indice_criticidade DESC);
CREATE INDEX ix_mv_tend_variacao    ON mv_tendencia_municipio (variacao_anualizada_pct DESC);

COMMIT;
