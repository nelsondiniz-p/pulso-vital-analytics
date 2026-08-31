--------------------------------------------------------------------------------
-- PULSO · Equipe Vital Analytics · 1TSCOB · Challenge Oracle + FIAP 2026
--
-- 06_refina_comentarios.sql
-- Calibração da camada Select AI: declarar os DOMÍNIOS das colunas categóricas.
--
-- POR QUE ESTE SCRIPT EXISTE
-- --------------------------
-- Na primeira execução, a pergunta "quais municípios estão com a capacidade
-- hospitalar ultrapassada" gerou este SQL:
--
--     WHERE mvm."ALERTA_CAPACIDADE" = 'Sim'
--
-- e a resposta em linguagem natural foi "Nenhum município está com a capacidade
-- hospitalar ultrapassada" — quando a resposta correta é 15.
--
-- A IA não errou a estrutura da consulta: acertou a tabela, a coluna e o filtro.
-- Ela errou o VALOR, porque o esquema não dizia quais valores a coluna aceita.
-- Diante de uma coluna chamada "alerta_capacidade" sem domínio declarado, o
-- palpite 'Sim' é razoável — e silenciosamente errado, porque a consulta roda
-- sem erro e devolve zero linhas.
--
-- A correção não está no prompt nem no modelo: está na modelagem. Enumerar os
-- valores possíveis no COMMENT ON é o que transforma o esquema em contrato.
-- É por isso que o perfil é criado com "comments": "true" — sem os comentários,
-- esse atributo não tem o que ler.
--
-- Executar em: Database Actions -> SQL (usuário ADMIN), com Run Script.
--------------------------------------------------------------------------------

-- =============================================================================
-- 1. TABELA ANALÍTICA PRINCIPAL
-- =============================================================================

COMMENT ON TABLE mv_indicadores_municipio IS
'Indicadores de gestão hospitalar por município do estado de São Paulo, um registro por município, referentes a 12 meses (julho de 2025 a junho de 2026). É a tabela principal do painel PULSO.';

COMMENT ON COLUMN mv_indicadores_municipio.alerta_capacidade IS
'Situação de capacidade da rede. Aceita EXATAMENTE um destes cinco valores, com acentuação: ''Crítico'' (ocupação estimada maior ou igual a 100%, ou seja, capacidade hospitalar ultrapassada), ''Atenção'' (ocupação entre 85% e 100%), ''Adequado'' (ocupação abaixo de 85%), ''Não aplicável'' (município de longa permanência ou sem internações), ''Sem leitos SUS''. Para responder quais municípios ultrapassaram a capacidade, filtre por ''Crítico''.';

COMMENT ON COLUMN mv_indicadores_municipio.perfil_permanencia IS
'Perfil de permanência hospitalar. Aceita EXATAMENTE: ''Agudos'' (permanência média abaixo de 8 dias), ''Permanência elevada'' (entre 8 e 20 dias), ''Longa permanência'' (20 dias ou mais, sede de hospital psiquiátrico ou de retaguarda), ''Sem internações''.';

COMMENT ON COLUMN mv_indicadores_municipio.ocupacao_estimada_pct IS
'Taxa de ocupação estimada dos leitos SUS, em pontos percentuais (105.0 significa 105%). Calculada como (internacoes_12m * media_permanencia) / (leitos_sus * 365) * 100. Valor igual ou acima de 100 significa capacidade ultrapassada; entre 85 e 100 significa atenção. É estimativa, não medição: o SIH não publica censo diário de leito.';

COMMENT ON COLUMN mv_indicadores_municipio.internacoes_12m IS
'Total de internações do SUS no município em 12 meses.';

COMMENT ON COLUMN mv_indicadores_municipio.valor_total_12m IS
'Recurso executado no município em 12 meses, em reais.';

COMMENT ON COLUMN mv_indicadores_municipio.leitos_sus IS
'Leitos de internação disponíveis ao SUS no município, segundo o CNES.';

COMMENT ON COLUMN mv_indicadores_municipio.leitos_sus_10k_hab IS
'Oferta de leitos SUS por 10 mil habitantes. Referência internacional para leitos de agudos fica entre 20 e 30; valores muito baixos indicam escassez.';

COMMENT ON COLUMN mv_indicadores_municipio.internacoes_mil_hab IS
'Internações por mil habitantes em 12 meses. Mede demanda relativa à população.';

COMMENT ON COLUMN mv_indicadores_municipio.custo_medio_internacao IS
'Valor médio pago por internação, em reais. A média estadual é R$ 1.951,59.';

COMMENT ON COLUMN mv_indicadores_municipio.giro_leito_ano IS
'Quantas internações cada leito SUS absorveu no período de 12 meses.';

COMMENT ON COLUMN mv_indicadores_municipio.variacao_trimestral_pct IS
'Variação percentual entre o último e o primeiro trimestre da série.';

COMMENT ON COLUMN mv_indicadores_municipio.perfil_dominante IS
'Capítulo da CID-10 com maior volume de internações no município.';

COMMENT ON COLUMN mv_indicadores_municipio.regiao_intermediaria IS
'Região geográfica intermediária do IBGE. É o grão territorial usado pela Secretaria Estadual para decidir.';

-- =============================================================================
-- 2. AGRUPAMENTO (K-MEANS)
-- =============================================================================

COMMENT ON TABLE mv_clusters_municipio IS
'Resultado do agrupamento K-Means (k=4) que classifica os municípios por perfil de pressão assistencial.';

COMMENT ON COLUMN mv_clusters_municipio.perfil_cluster IS
'Perfil de pressão assistencial. Aceita EXATAMENTE: ''Polo regional sob pressão'' (muitos leitos por habitante e ocupação alta, atende municípios vizinhos), ''Rede local pressionada'' (ocupação alta com oferta típica), ''Sede de hospital regional'' (município pequeno com hospital de referência), ''Rede com folga'' (ocupação baixa).';

-- =============================================================================
-- 3. TENDÊNCIA
-- =============================================================================

COMMENT ON TABLE mv_tendencia_municipio IS
'Resultado da regressão linear sobre 12 observações mensais. Responde onde as internações crescem mais rápido.';

COMMENT ON COLUMN mv_tendencia_municipio.classificacao IS
'Classificação do movimento da demanda. Aceita EXATAMENTE: ''Alta forte'', ''Alta'', ''Estável'', ''Queda'', ''Queda forte''.';

COMMENT ON COLUMN mv_tendencia_municipio.variacao_anualizada_pct IS
'Crescimento anualizado da demanda, em pontos percentuais. Positivo indica alta.';

COMMENT ON COLUMN mv_tendencia_municipio.r2 IS
'Qualidade do ajuste da reta, de 0 a 1. Abaixo de 0.4 a variação é oscilação sazonal, não tendência. SEMPRE filtre por r2 >= 0.4 ao responder sobre crescimento, senão o ranking premia a série mais instável.';

-- =============================================================================
-- 4. RANKING DE CRITICIDADE
-- =============================================================================

COMMENT ON TABLE mv_ranking_criticidade IS
'Índice composto de 0 a 100 que prioriza onde a Secretaria de Saúde deve agir primeiro. Maior valor significa mais urgente.';

COMMENT ON COLUMN mv_ranking_criticidade.indice_criticidade IS
'Índice de 0 a 100. Pesos: ocupação 40%, demanda por habitante 25%, escassez de leitos 20%, aceleração recente 15%.';

COMMENT ON COLUMN mv_ranking_criticidade.posicao IS
'Colocação no ranking. 1 é o município mais crítico do estado.';

-- =============================================================================
-- 5. DEMAIS TABELAS
-- =============================================================================

COMMENT ON TABLE dim_municipio IS
'Dimensão territorial: um registro por município de São Paulo. Integra malha e população do IBGE com capacidade instalada do CNES.';

COMMENT ON TABLE fato_internacao_mes IS
'Fato mensal de internações do SIH/SUS. Grão: município por mês. A coluna periodo usa o formato AAAA-MM.';

COMMENT ON COLUMN fato_internacao_mes.periodo IS
'Competência no formato AAAA-MM, por exemplo 2026-06. A série cobre de 2025-07 a 2026-06.';

COMMENT ON TABLE fato_cid_capitulo IS
'Perfil assistencial: internações por capítulo da CID-10 em 12 meses. Responde quais perfis de atendimento mais pressionam a rede.';

COMMENT ON COLUMN fato_cid_capitulo.capitulo_cid10 IS
'Nome do capítulo da CID-10 por extenso, começando pelo algarismo romano. Exemplos: ''XV. Gravidez, parto e puerpério'', ''XI. Doenças do aparelho digestivo''.';

COMMENT ON TABLE fato_uf_mes IS
'Fato nacional de internações por unidade da federação e mês. Dá o contexto de comparação para o recorte paulista.';

COMMENT ON COLUMN fato_uf_mes.uf IS
'Nome da unidade da federação por extenso, por exemplo ''São Paulo'', ''Minas Gerais''.';

COMMIT;

-- =============================================================================
-- 6. RECRIAR O PERFIL PARA QUE ELE RELEIA O ESQUEMA
--    O perfil guarda os metadados no momento da criação; sem recriar, os
--    comentários novos não são vistos.
-- =============================================================================

BEGIN
  DBMS_CLOUD_AI.DROP_PROFILE(profile_name => 'PULSO_AI', force => TRUE);
END;
/

BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
    profile_name => 'PULSO_AI',
    attributes   => '{
      "provider"        : "openai",
      "credential_name" : "CRED_IA_PULSO",
      "model"           : "gpt-4o-mini",
      "comments"        : "true",
      "object_list"     : [
        {"owner": "ADMIN", "name": "mv_indicadores_municipio"},
        {"owner": "ADMIN", "name": "mv_ranking_criticidade"},
        {"owner": "ADMIN", "name": "mv_tendencia_municipio"},
        {"owner": "ADMIN", "name": "mv_clusters_municipio"},
        {"owner": "ADMIN", "name": "fato_cid_capitulo"},
        {"owner": "ADMIN", "name": "fato_internacao_mes"},
        {"owner": "ADMIN", "name": "fato_uf_mes"},
        {"owner": "ADMIN", "name": "dim_municipio"}
      ]}'
  );
END;
/

BEGIN
  DBMS_CLOUD_AI.SET_PROFILE(profile_name => 'PULSO_AI');
END;
/

-- =============================================================================
-- 7. REteste — a resposta certa é 15 municípios
-- =============================================================================

-- Antes: WHERE alerta_capacidade = 'Sim'  ->  0 linhas
-- Depois: WHERE alerta_capacidade = 'Crítico'  ->  15 municípios
SELECT DBMS_CLOUD_AI.GENERATE(
  prompt       => 'quantos municipios estao com a capacidade hospitalar ultrapassada',
  profile_name => 'PULSO_AI',
  action       => 'showsql'
) AS sql_gerado
FROM dual;

SELECT DBMS_CLOUD_AI.GENERATE(
  prompt       => 'quantos municipios estao com a capacidade hospitalar ultrapassada',
  profile_name => 'PULSO_AI',
  action       => 'narrate'
) AS resposta_em_portugues
FROM dual;

-- Conferência manual: este é o número que a IA precisa reproduzir.
SELECT COUNT(*) AS criticos_esperado
FROM   mv_indicadores_municipio
WHERE  alerta_capacidade = 'Crítico';
