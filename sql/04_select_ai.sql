--------------------------------------------------------------------------------
-- PULSO · Equipe Vital Analytics · 1TSCOA · Challenge Oracle + FIAP 2026
--
-- 04_select_ai.sql
-- O DIFERENCIAL DA SOLUÇÃO: o gestor pergunta em português, o banco gera e
-- executa o SQL.
--
-- Este é o ponto do projeto em que a modelagem de dados vira usabilidade. O
-- Select AI só produz SQL confiável se o `object_list` apontar para objetos com
-- nomes de negócio, grão único e comentários descritivos - por isso os scripts
-- 01 e 03 investem em COMMENT ON e em views de uma linha por município.
--------------------------------------------------------------------------------

-- =============================================================================
-- 1. PERMISSÕES
-- =============================================================================

GRANT EXECUTE ON DBMS_CLOUD_AI TO ADMIN;

-- Liberar a saída de rede para o provedor de IA (obrigatório no Autonomous).
-- Para OCI Generative AI, trocar o host por 'inference.generativeai.<regiao>.oci.oraclecloud.com'.
BEGIN
  DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
    host => 'api.openai.com',
    ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                        principal_name => 'ADMIN',
                        principal_type => xs_acl.ptype_db)
  );
END;
/

-- =============================================================================
-- 2. CREDENCIAL DO PROVEDOR DE IA
--    Opção A (usada aqui): OpenAI - basta uma API key.
--    Opção B: OCI Generative AI - fica dentro do ecossistema Oracle e não
--    exige provedor externo; troque o bloco abaixo pelo da opção B.
-- =============================================================================

BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => 'CRED_IA_PULSO',
    username        => 'PULSO',
    password        => 'SUA_API_KEY_AQUI'
  );
END;
/

-- Opção B - OCI Generative AI (sem provedor externo):
-- BEGIN
--   DBMS_CLOUD.CREATE_CREDENTIAL(
--     credential_name => 'CRED_IA_PULSO',
--     user_ocid       => 'ocid1.user.oc1..xxxx',
--     tenancy_ocid    => 'ocid1.tenancy.oc1..xxxx',
--     private_key     => 'SUA_CHAVE_PRIVADA_SEM_CABECALHO',
--     fingerprint     => 'xx:xx:xx:xx'
--   );
-- END;
-- /

-- =============================================================================
-- 3. PERFIL DE IA
--    O `object_list` é a fronteira do que a IA enxerga. Manter enxuto é decisão
--    de projeto: quanto menos objetos, menos ambiguidade e melhor o SQL gerado.
--    As `description` são o que ensina a IA sobre o negócio.
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
        {"owner": "ADMIN", "name": "vw_serie_estado"},
        {"owner": "ADMIN", "name": "vw_perfil_assistencial"},
        {"owner": "ADMIN", "name": "vw_painel_regional"},
        {"owner": "ADMIN", "name": "vw_capacidade_rede"}
      ]
    }'
  );
END;
/

-- "comments": "true" faz a IA ler os COMMENT ON das tabelas e colunas. É o que
-- permite a ela entender que ocupacao_estimada_pct acima de 100 significa
-- capacidade ultrapassada, sem que isso precise estar na pergunta.

BEGIN
  DBMS_CLOUD_AI.SET_PROFILE(profile_name => 'PULSO_AI');
END;
/

-- =============================================================================
-- 4. TESTE DE FUMAÇA
-- =============================================================================

SELECT AI 'quantos municipios estao com a capacidade hospitalar ultrapassada';

-- Se retornar erro de rede, revisar o APPEND_HOST_ACE do passo 1.
-- Se retornar SQL incorreto, revisar os COMMENT ON e reduzir o object_list.

COMMIT;
