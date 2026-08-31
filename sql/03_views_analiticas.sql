--------------------------------------------------------------------------------
-- PULSO · Equipe Vital Analytics · 1TSCOB · Challenge Oracle + FIAP 2026
--
-- 03_views_analiticas.sql
-- Camada de CONSUMO ANALÍTICO: as views que o dashboard e o Select AI leem.
--
-- Princípio de projeto: o Select AI só gera SQL correto se enxergar objetos com
-- nomes de negócio e granularidade única. Por isso a inteligência do modelo fica
-- nas views - o objeto exposto à IA é sempre a resposta pronta em uma linha por
-- município, nunca um join que ela precise inventar.
--------------------------------------------------------------------------------

-- =============================================================================
-- 1. VIEW PRINCIPAL — um município por linha, todos os indicadores de gestão
-- =============================================================================

CREATE OR REPLACE VIEW mv_indicadores_municipio AS
WITH agregado AS (
  SELECT codigo,
         SUM(internacoes)      AS internacoes_12m,
         SUM(valor_total)      AS valor_total_12m,
         AVG(media_permanencia) AS media_permanencia
  FROM   fato_internacao_mes
  GROUP  BY codigo
),
janelas AS (
  -- Compara o trimestre mais recente com o mais antigo da série de 12 meses.
  SELECT codigo,
         SUM(CASE WHEN periodo >= (SELECT MAX(periodo) FROM fato_internacao_mes)
                  THEN internacoes ELSE 0 END) AS ultimo_mes,
         SUM(CASE WHEN periodo IN (SELECT periodo FROM (
                       SELECT DISTINCT periodo FROM fato_internacao_mes
                       ORDER BY periodo DESC FETCH FIRST 3 ROWS ONLY))
                  THEN internacoes ELSE 0 END) AS ult_trimestre,
         SUM(CASE WHEN periodo IN (SELECT periodo FROM (
                       SELECT DISTINCT periodo FROM fato_internacao_mes
                       ORDER BY periodo ASC FETCH FIRST 3 ROWS ONLY))
                  THEN internacoes ELSE 0 END) AS prim_trimestre
  FROM   fato_internacao_mes
  GROUP  BY codigo
),
perfil AS (
  -- Capítulo CID-10 com maior volume em cada município.
  SELECT codigo, capitulo_cid10 AS perfil_dominante
  FROM  (SELECT codigo, capitulo_cid10,
                ROW_NUMBER() OVER (PARTITION BY codigo
                                   ORDER BY internacoes DESC) AS rn
         FROM   fato_cid_capitulo)
  WHERE rn = 1
)
SELECT
  d.codigo,
  d.municipio,
  d.regiao_imediata,
  d.regiao_intermediaria,
  d.populacao,
  d.leitos_existentes,
  d.leitos_sus,
  d.leitos_sus_10k_hab,
  NVL(a.internacoes_12m, 0)                                   AS internacoes_12m,
  NVL(a.valor_total_12m, 0)                                   AS valor_total_12m,
  ROUND(NVL(a.media_permanencia, 0), 2)                       AS media_permanencia,
  p.perfil_dominante,

  -- Demanda relativa à população atendida
  CASE WHEN d.populacao > 0
       THEN ROUND(NVL(a.internacoes_12m, 0) / d.populacao * 1000, 2) END
                                                              AS internacoes_mil_hab,

  -- Giro: quantas internações cada leito SUS absorveu no ano
  CASE WHEN d.leitos_sus > 0
       THEN ROUND(NVL(a.internacoes_12m, 0) / d.leitos_sus, 1) END
                                                              AS giro_leito_ano,

  -- Ocupação estimada = (internações x permanência média) / (leitos x 365)
  -- Aproximação padrão de taxa de ocupação a partir de dados agregados do SIH.
  CASE WHEN d.leitos_sus > 0
       THEN ROUND(NVL(a.internacoes_12m, 0) * NVL(a.media_permanencia, 0)
                  / (d.leitos_sus * 365) * 100, 1) END
                                                              AS ocupacao_estimada_pct,

  CASE WHEN NVL(a.internacoes_12m, 0) > 0
       THEN ROUND(a.valor_total_12m / a.internacoes_12m, 2) END
                                                              AS custo_medio_internacao,

  CASE WHEN j.prim_trimestre > 0
       THEN ROUND((j.ult_trimestre / j.prim_trimestre - 1) * 100, 1) END
                                                              AS variacao_trimestral_pct,

  -- Perfil de permanência: separa hospital de agudos de retaguarda/psiquiatria
  CASE WHEN NVL(a.internacoes_12m, 0) = 0        THEN 'Sem internações'
       WHEN NVL(a.media_permanencia, 0) >= 20    THEN 'Longa permanência'
       WHEN NVL(a.media_permanencia, 0) >= 8     THEN 'Permanência elevada'
       ELSE 'Agudos' END                                      AS perfil_permanencia,

  -- Alerta operacional. Municípios de longa permanência ficam fora: neles a
  -- ocupação alta é estrutural, não é crise assistencial.
  CASE WHEN NVL(a.internacoes_12m, 0) = 0     THEN 'Não aplicável'
       WHEN NVL(a.media_permanencia, 0) >= 20 THEN 'Não aplicável'
       WHEN d.leitos_sus = 0                  THEN 'Sem leitos SUS'
       WHEN NVL(a.internacoes_12m, 0) * NVL(a.media_permanencia, 0)
            / (d.leitos_sus * 365) * 100 >= 100 THEN 'Crítico'
       WHEN NVL(a.internacoes_12m, 0) * NVL(a.media_permanencia, 0)
            / (d.leitos_sus * 365) * 100 >= 85  THEN 'Atenção'
       ELSE 'Adequado' END                                    AS alerta_capacidade
FROM       dim_municipio d
LEFT JOIN  agregado a ON a.codigo = d.codigo
LEFT JOIN  janelas  j ON j.codigo = d.codigo
LEFT JOIN  perfil   p ON p.codigo = d.codigo;

COMMENT ON TABLE mv_indicadores_municipio IS
  'Indicadores de gestão hospitalar por município: ocupação estimada, giro de leito, demanda por habitante, custo médio e alerta de capacidade. É a view principal do PULSO.';

-- =============================================================================
-- 2. SÉRIE TEMPORAL DO ESTADO
-- =============================================================================

CREATE OR REPLACE VIEW vw_serie_estado AS
SELECT periodo,
       SUM(internacoes)                        AS internacoes,
       SUM(valor_total)                        AS valor_total,
       ROUND(SUM(valor_total) / NULLIF(SUM(internacoes), 0), 2) AS custo_medio
FROM   fato_internacao_mes
GROUP  BY periodo
ORDER  BY periodo;

COMMENT ON TABLE vw_serie_estado IS
  'Evolução mensal das internações e do recurso executado no estado de São Paulo.';

-- =============================================================================
-- 3. PERFIL ASSISTENCIAL DO ESTADO
-- =============================================================================

CREATE OR REPLACE VIEW vw_perfil_assistencial AS
SELECT capitulo_cid10,
       SUM(internacoes) AS internacoes,
       ROUND(100 * SUM(internacoes) / SUM(SUM(internacoes)) OVER (), 1)
                        AS participacao_pct
FROM   fato_cid_capitulo
GROUP  BY capitulo_cid10
ORDER  BY internacoes DESC;

COMMENT ON TABLE vw_perfil_assistencial IS
  'Quais perfis de atendimento (capítulos CID-10) mais pressionam a rede paulista.';

-- =============================================================================
-- 4. CAPACIDADE INSTALADA COM CADASTRO DO CNES
--    Junta a fonte relacional (SIH) com a semiestruturada (CNES em JSON).
-- =============================================================================

CREATE OR REPLACE VIEW vw_capacidade_rede AS
SELECT i.codigo,
       i.municipio,
       i.regiao_intermediaria,
       i.populacao,
       i.leitos_sus,
       i.ocupacao_estimada_pct,
       i.alerta_capacidade,
       COUNT(c.codigo_cnes)                  AS estabelecimentos_hospitalares,
       SUM(NVL(c.tem_centro_cirurgico, 0))   AS unidades_com_centro_cirurgico,
       SUM(NVL(c.tem_centro_obstetrico, 0))  AS unidades_com_centro_obstetrico,
       SUM(NVL(c.tem_centro_neonatal, 0))    AS unidades_com_centro_neonatal
FROM       mv_indicadores_municipio i
LEFT JOIN  vw_cnes_estabelecimentos c ON c.codigo = i.codigo
GROUP  BY  i.codigo, i.municipio, i.regiao_intermediaria, i.populacao,
           i.leitos_sus, i.ocupacao_estimada_pct, i.alerta_capacidade;

COMMENT ON TABLE vw_capacidade_rede IS
  'Capacidade instalada por município cruzando leitos do SIH com o cadastro de estabelecimentos do CNES (JSON).';

-- =============================================================================
-- 5. PAINEL REGIONAL — o grão que a Secretaria Estadual usa para decidir
-- =============================================================================

CREATE OR REPLACE VIEW vw_painel_regional AS
SELECT regiao_intermediaria                                  AS regiao,
       COUNT(*)                                              AS municipios,
       SUM(populacao)                                        AS populacao,
       SUM(leitos_sus)                                       AS leitos_sus,
       SUM(internacoes_12m)                                  AS internacoes_12m,
       ROUND(SUM(valor_total_12m) / 1000000, 1)              AS recurso_milhoes,
       ROUND(SUM(valor_total_12m)
             / NULLIF(SUM(internacoes_12m), 0), 2)           AS custo_medio,
       ROUND(SUM(leitos_sus) / NULLIF(SUM(populacao), 0) * 10000, 2)
                                                             AS leitos_10k_hab,
       SUM(CASE WHEN alerta_capacidade = 'Crítico' THEN 1 ELSE 0 END)
                                                             AS municipios_criticos,
       SUM(CASE WHEN alerta_capacidade = 'Atenção' THEN 1 ELSE 0 END)
                                                             AS municipios_atencao
FROM   mv_indicadores_municipio
WHERE  regiao_intermediaria IS NOT NULL
GROUP  BY regiao_intermediaria
ORDER  BY municipios_criticos DESC, internacoes_12m DESC;

COMMENT ON TABLE vw_painel_regional IS
  'Consolidação por região intermediária do IBGE: onde a pressão está concentrada no território.';

COMMIT;
