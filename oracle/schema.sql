-- =============================================================================
-- SEDAT-SUS — schema Oracle, padrão "tabela relacional"
-- Rode como ADMIN no Oracle Autonomous Database (SQL Worksheet do Database Actions,
-- ou sqlplus/sqlcl). Cria um usuário de aplicação dedicado (SEDAT_APP), só com
-- privilégio de leitura nas próprias tabelas — é esse usuário que a função
-- serverless (api/select-ai.js) usa para conectar, e é o object_list do profile
-- do Select AI (oracle/select_ai_setup.sql) que limita as consultas geradas pelo
-- LLM só a essas tabelas (SELECT, nunca DDL/DML).
--
-- Este arquivo cobre só o padrão "tabela relacional" (dado processado da
-- PRF/SIH, carregado via INSERT por dados_reais/carregar_oracle.py) — um dos
-- três padrões de fonte de dados do desafio. Os outros dois:
--   - CSV como External Table (populacao_uf, clima_mensal_2025, lidas direto de
--     um bucket do Object Storage, sem INSERT) -> oracle/external_table.sql
--   - JSON via API (CNES/leitos) -> oracle/cnes_json.sql
-- Rode os três, nessa ordem, para o schema ficar completo.
-- =============================================================================

-- 1) Usuário de aplicação (troque a senha antes de rodar; ela vai para o
--    ORACLE_PASSWORD da Vercel depois, nunca para o código)
CREATE USER sedat_app IDENTIFIED BY "TrocarEssaSenhaForte#123";
GRANT CREATE SESSION TO sedat_app;
ALTER USER sedat_app QUOTA UNLIMITED ON DATA;

-- 2) Tabelas — nomes e colunas espelham exatamente os CSVs de dados/ (ver
--    README.md, seção "Arquivos esperados em dados/"), para o carregador
--    (dados_reais/carregar_oracle.py) e o Select AI mapearem 1:1.
ALTER SESSION SET CURRENT_SCHEMA = sedat_app;

CREATE TABLE acidentes_estado (
  uf         VARCHAR2(60),
  acidentes  NUMBER
);

CREATE TABLE acidentes_estado_tipo (
  uf         VARCHAR2(60),
  tipo       VARCHAR2(100),
  acidentes  NUMBER
);

CREATE TABLE acidentes_mensal (
  mes        VARCHAR2(20),
  acidentes  NUMBER
);

CREATE TABLE acidentes_mensal_estado (
  uf         VARCHAR2(60),
  mes        VARCHAR2(20),
  acidentes  NUMBER
);

CREATE TABLE causas_acidente (
  causa       VARCHAR2(200),
  percentual  NUMBER
);

-- clima_mensal_2025 não é criada aqui: virou External Table em
-- oracle/external_table.sql (padrão "CSV como External Table").

CREATE TABLE comparacao_real_previsto (
  recurso    VARCHAR2(100),
  icone      VARCHAR2(20),
  real       NUMBER,
  previsto   NUMBER,
  variacao   VARCHAR2(20)
);

CREATE TABLE condicao_metereologica (
  condicao    VARCHAR2(100),
  percentual  NUMBER
);

CREATE TABLE dia_semana (
  dia         VARCHAR2(20),
  percentual  NUMBER
);

CREATE TABLE faixa_horaria (
  faixa       VARCHAR2(20),
  percentual  NUMBER
);

CREATE TABLE fatores_impacto (
  fator        VARCHAR2(100),
  importancia  NUMBER
);

CREATE TABLE gravidade_acidente (
  classificacao  VARCHAR2(100),
  percentual     NUMBER
);

CREATE TABLE kpis (
  indicador  VARCHAR2(100),
  valor      NUMBER,
  variacao   VARCHAR2(20),
  tendencia  VARCHAR2(10)
);

CREATE TABLE kpis_analises (
  indicador  VARCHAR2(100),
  valor      NUMBER
);

CREATE TABLE kpis_previsao (
  indicador  VARCHAR2(100),
  valor      NUMBER,
  variacao   VARCHAR2(20)
);

CREATE TABLE kpis_previsao_estado (
  uf                     VARCHAR2(60),
  acidentes_valor        NUMBER,
  acidentes_variacao     VARCHAR2(20),
  leitos_valor           NUMBER,
  leitos_variacao        VARCHAR2(20),
  atendimentos_valor     NUMBER,
  atendimentos_variacao  VARCHAR2(20),
  obitos_valor           NUMBER,
  obitos_variacao        VARCHAR2(20)
);

CREATE TABLE mortos_feridos_mensal (
  mes             VARCHAR2(20),
  mortos          NUMBER,
  feridos_graves  NUMBER,
  feridos_leves   NUMBER
);

CREATE TABLE municipios (
  municipio  VARCHAR2(150),
  uf         VARCHAR2(60),
  acidentes  NUMBER
);

CREATE TABLE municipios_estado (
  uf         VARCHAR2(60),
  municipio  VARCHAR2(150),
  acidentes  NUMBER
);

-- populacao_uf não é criada aqui: virou External Table em
-- oracle/external_table.sql (padrão "CSV como External Table").

CREATE TABLE previsao_mensal (
  mes       VARCHAR2(20),
  real      NUMBER,
  previsto  NUMBER
);

CREATE TABLE previsao_mensal_estado (
  uf                     VARCHAR2(60),
  mes                    VARCHAR2(20),
  previsto_acidentes     NUMBER,
  previsto_leitos        NUMBER,
  previsto_atendimentos  NUMBER,
  previsto_obitos        NUMBER
);

CREATE TABLE previsao_semestre (
  mes       VARCHAR2(20),
  previsto  NUMBER
);

CREATE TABLE recursos_estado (
  uf                   VARCHAR2(60),
  leitos_estim         NUMBER,
  atendimentos_estim   NUMBER,
  obitos               NUMBER
);

CREATE TABLE rodovias (
  rodovia     VARCHAR2(50),
  trecho      VARCHAR2(200),
  acidentes   NUMBER,
  percentual  NUMBER
);

CREATE TABLE serie_mensal_estado (
  uf                   VARCHAR2(60),
  mes                  VARCHAR2(20),
  acidentes            NUMBER,
  leitos_estim         NUMBER,
  atendimentos_estim   NUMBER,
  obitos               NUMBER
);

CREATE TABLE tipos_acidente (
  tipo        VARCHAR2(100),
  percentual  NUMBER
);

-- 3) Comentários nas tabelas/colunas — o Select AI usa isso (junto com os nomes)
--    para entender o schema ao converter linguagem natural em SQL. Vale a pena
--    manter esses comentários atualizados se o schema mudar.
COMMENT ON TABLE acidentes_estado IS 'Total de acidentes de trânsito por unidade federativa (UF) no período carregado';
COMMENT ON TABLE municipios IS 'Ranking nacional de municípios por número de acidentes de trânsito';
COMMENT ON TABLE causas_acidente IS 'Distribuição percentual das causas de acidente de trânsito (dados PRF)';
COMMENT ON TABLE condicao_metereologica IS 'Distribuição percentual dos acidentes por condição meteorológica no momento do acidente';
COMMENT ON TABLE faixa_horaria IS 'Distribuição percentual dos acidentes por faixa de horário do dia';
COMMENT ON TABLE kpis IS 'Indicadores-chave (KPIs) do período atual: Acidentes, Leitos Ocupados, Acidentes com Vítimas, Atendimentos, Óbitos';
COMMENT ON TABLE kpis_previsao IS 'Indicadores-chave previstos para o próximo semestre, por modelo de regressão linear';
COMMENT ON TABLE rodovias IS 'Ranking de rodovias federais por número de acidentes';
-- populacao_uf comentada em oracle/external_table.sql, junto com a criação da
-- external table (comentário de tabela só pode ser feito depois dela existir).
