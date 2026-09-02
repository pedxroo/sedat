-- =============================================================================
-- SEDAT-SUS — padrão "CSV como External Table"
-- Rode DEPOIS de oracle/schema.sql, conectado como sedat_app (ou ADMIN com
-- ALTER SESSION SET CURRENT_SCHEMA = sedat_app).
--
-- Diferença para as tabelas de oracle/schema.sql: aqui o CSV não é copiado para
-- dentro do banco via INSERT. O Oracle lê o arquivo ao vivo, direto do
-- repositório GitHub público do projeto (raw.githubusercontent.com), toda vez
-- que a tabela é consultada — para atualizar o dado basta dar `git push` com o
-- CSV novo, sem tocar no banco.
--
-- Não usa OCI Object Storage nem exige conta OCI completa: para um arquivo
-- público (como o repositório github.com/pedxroo/sedat, que já é público),
-- credential_name pode ficar NULL. Funciona em qualquer Oracle Database com
-- DBMS_CLOUD habilitado, incluindo o FreeSQL (sql.oraclecloud.com).
--
-- Antes de rodar: confirme que dados/populacao_uf.csv e
-- dados/clima_mensal_2025.csv estão publicados no branch main do repositório
-- (sedat/dados/, que é a cópia versionada no GitHub — ver README).
--
-- Teste rápido de compatibilidade (rode isto primeiro; se der
-- "ORA-01031: insufficient privileges" ou "PLS-00201: identifier DBMS_CLOUD
-- must be declared", esse ambiente não libera DBMS_CLOUD e este arquivo não
-- pode ser usado — nesse caso, mantenha populacao_uf e clima_mensal_2025 como
-- tabelas comuns em oracle/schema.sql e documente esse padrão só como projeto,
-- não como algo rodando de fato):
--   SELECT COUNT(*) FROM ALL_PROCEDURES WHERE OBJECT_NAME = 'DBMS_CLOUD';
-- =============================================================================

-- 1) External table: populacao_uf.csv (IBGE)
-- Troque "pedxroo/sedat" e "main" se o usuário/repositório/branch for outro.
BEGIN
  DBMS_CLOUD.CREATE_EXTERNAL_TABLE(
    table_name      => 'populacao_uf',
    credential_name => NULL,
    file_uri_list   => 'https://raw.githubusercontent.com/pedxroo/sedat/main/dados/populacao_uf.csv',
    format          => JSON_OBJECT('type' VALUE 'CSV', 'skipheaders' VALUE 1),
    column_list     => 'uf VARCHAR2(60), populacao NUMBER, ano NUMBER'
  );
END;
/

COMMENT ON TABLE populacao_uf IS 'População estimada por UF (IBGE) — External Table lida direto do repositório GitHub público do projeto, usada para calcular taxas per capita';

-- 2) External table: clima_mensal_2025.csv (INMET)
BEGIN
  DBMS_CLOUD.CREATE_EXTERNAL_TABLE(
    table_name      => 'clima_mensal_2025',
    credential_name => NULL,
    file_uri_list   => 'https://raw.githubusercontent.com/pedxroo/sedat/main/dados/clima_mensal_2025.csv',
    format          => JSON_OBJECT('type' VALUE 'CSV', 'skipheaders' VALUE 1),
    column_list     => 'mes VARCHAR2(20), temperatura_media_c NUMBER, precipitacao_media_mm NUMBER'
  );
END;
/

COMMENT ON TABLE clima_mensal_2025 IS 'Temperatura e precipitação médias mensais (INMET) — External Table lida direto do repositório GitHub público do projeto, variável do modelo preditivo';

-- 3) Teste rápido (deve retornar as linhas do CSV direto do GitHub)
-- SELECT * FROM populacao_uf;
-- SELECT * FROM clima_mensal_2025;

-- Se DBMS_CLOUD não estiver disponível nesta conta (ver teste de
-- compatibilidade no topo do arquivo), rode em vez disso, como fallback, os
-- dois CREATE TABLE comuns abaixo (voltando ao padrão relacional só para esses
-- dois conjuntos de dados) e carregue-os junto com o resto por
-- dados_reais/carregar_oracle.py:
--
-- CREATE TABLE populacao_uf (uf VARCHAR2(60), populacao NUMBER, ano NUMBER);
-- CREATE TABLE clima_mensal_2025 (mes VARCHAR2(20), temperatura_media_c NUMBER, precipitacao_media_mm NUMBER);
