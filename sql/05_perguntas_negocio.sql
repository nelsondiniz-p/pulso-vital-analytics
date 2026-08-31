--------------------------------------------------------------------------------
-- PULSO · Equipe Vital Analytics · 1TSCOB · Challenge Oracle + FIAP 2026
--
-- 05_perguntas_negocio.sql
-- As perguntas de gestão que o painel responde, em três formas:
--
--   (a) SELECT AI            -> resposta direta
--   (b) SELECT AI showsql    -> mostra o SQL gerado  (usar para as evidências)
--   (c) SELECT AI narrate    -> resposta em linguagem de negócio
--
-- Abaixo de cada pergunta está o SQL EQUIVALENTE escrito à mão. Serve para dois
-- propósitos: validar se a IA gerou a consulta certa, e garantir que o painel
-- funcione mesmo sem provedor de IA configurado.
--------------------------------------------------------------------------------

BEGIN
  DBMS_CLOUD_AI.SET_PROFILE(profile_name => 'PULSO_AI');
END;
/

-- =============================================================================
-- PERGUNTA 1 — Quais regiões têm a capacidade hospitalar ultrapassada?
--              (pergunta central do desafio Oracle)
-- =============================================================================

SELECT AI showsql 'quais municipios estao com a capacidade hospitalar ultrapassada';
SELECT AI narrate 'quais municipios estao com a capacidade hospitalar ultrapassada';

-- SQL equivalente:
SELECT municipio,
       leitos_sus,
       internacoes_12m,
       ocupacao_estimada_pct
FROM   mv_indicadores_municipio
WHERE  alerta_capacidade = 'Crítico'
ORDER  BY ocupacao_estimada_pct DESC
FETCH FIRST 10 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 2 — Quais perfis de atendimento pressionam mais o sistema?
-- =============================================================================

SELECT AI showsql 'quais perfis de atendimento geram mais internacoes no estado';

-- SQL equivalente:
SELECT capitulo_cid10,
       internacoes,
       participacao_pct
FROM   vw_perfil_assistencial
FETCH FIRST 6 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 3 — Onde as internações crescem mais rápido?
--              O filtro de R² é o que separa tendência real de ruído sazonal.
-- =============================================================================

SELECT AI showsql 'em quais municipios as internacoes mais cresceram no ultimo ano';

-- SQL equivalente:
SELECT municipio,
       internacoes_12m,
       variacao_anualizada_pct,
       r2
FROM   mv_tendencia_municipio
WHERE  internacoes_12m >= 600
AND    variacao_anualizada_pct > 0
AND    r2 >= 0.4                       -- descarta oscilação sem tendência
ORDER  BY variacao_anualizada_pct DESC
FETCH FIRST 8 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 4 — Quais municípios têm poucos leitos para a população?
-- =============================================================================

SELECT AI showsql 'municipios com mais de 100 mil habitantes e menor oferta de leitos por habitante';

-- SQL equivalente:
SELECT municipio,
       populacao,
       leitos_sus,
       leitos_sus_10k_hab,
       ocupacao_estimada_pct
FROM   mv_indicadores_municipio
WHERE  leitos_sus > 0
AND    populacao >= 100000
AND    perfil_permanencia <> 'Longa permanência'
ORDER  BY leitos_sus_10k_hab ASC
FETCH FIRST 8 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 5 — Onde o custo médio de internação é mais alto?
-- =============================================================================

SELECT AI showsql 'qual o custo medio de internacao por municipio e onde ele e mais alto';

-- SQL equivalente:
SELECT municipio,
       internacoes_12m,
       ROUND(valor_total_12m / 1000000, 1) AS recurso_milhoes,
       custo_medio_internacao
FROM   mv_indicadores_municipio
WHERE  internacoes_12m >= 2000
ORDER  BY custo_medio_internacao DESC
FETCH FIRST 8 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 6 — Qual região concentra mais municípios em situação crítica?
-- =============================================================================

SELECT AI narrate 'qual regiao do estado tem mais municipios em situacao critica de capacidade';

-- SQL equivalente:
SELECT regiao,
       municipios,
       municipios_criticos,
       municipios_atencao,
       leitos_10k_hab,
       internacoes_12m
FROM   vw_painel_regional
FETCH FIRST 10 ROWS ONLY;

-- =============================================================================
-- PERGUNTA 7 — Como os municípios se agrupam por perfil de pressão?
--              (expõe o resultado do K-Means ao gestor em linguagem natural)
-- =============================================================================

SELECT AI showsql 'quantos municipios existem em cada perfil de pressao assistencial';

-- SQL equivalente:
SELECT perfil_cluster,
       COUNT(*)                              AS municipios,
       ROUND(AVG(ocupacao_estimada_pct), 1)  AS ocupacao_media,
       ROUND(AVG(leitos_sus_10k_hab), 1)     AS leitos_10k_hab_media,
       SUM(internacoes_12m)                  AS internacoes_12m
FROM   mv_clusters_municipio
GROUP  BY perfil_cluster
ORDER  BY ocupacao_media DESC;

-- =============================================================================
-- PERGUNTA 8 — A rede de um município tem estrutura para o que ela atende?
--              Cruza a fonte relacional (SIH) com a semiestruturada (CNES/JSON).
-- =============================================================================

SELECT municipio,
       leitos_sus,
       ocupacao_estimada_pct,
       estabelecimentos_hospitalares,
       unidades_com_centro_cirurgico,
       unidades_com_centro_obstetrico
FROM   vw_capacidade_rede
WHERE  alerta_capacidade IN ('Crítico', 'Atenção')
ORDER  BY ocupacao_estimada_pct DESC
FETCH FIRST 15 ROWS ONLY;

-- =============================================================================
-- CONTROLE — números que devem bater com o dashboard
-- =============================================================================

SELECT COUNT(*)                                                   AS municipios,
       SUM(internacoes_12m)                                       AS internacoes_12m,
       ROUND(SUM(valor_total_12m) / 1000000000, 2)                AS recurso_bilhoes,
       SUM(leitos_sus)                                            AS leitos_sus,
       SUM(CASE WHEN alerta_capacidade = 'Crítico' THEN 1 ELSE 0 END) AS criticos,
       SUM(CASE WHEN alerta_capacidade = 'Atenção' THEN 1 ELSE 0 END) AS atencao
FROM   mv_indicadores_municipio;
