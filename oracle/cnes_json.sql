-- =============================================================================
-- SEDAT-SUS — padrão "JSON via API" (CNES — unidades de saúde por UF)
-- Rode depois de oracle/schema.sql, conectado como sedat_app (ou ADMIN com
-- ALTER SESSION SET CURRENT_SCHEMA = sedat_app). Depois deste arquivo, rode
-- oracle/carga_cnes.sql (gerado por dados_reais/gerar_sql_cnes.py) para
-- preencher a tabela.
--
-- Fonte: dump público de Estabelecimentos do CNES (Ministério da Saúde,
-- dadosabertos.saude.gov.br / ckan.saude.gov.br), baixado em JSON. O dump de
-- Estabelecimentos não traz contagem de leitos (isso fica numa tabela CNES
-- separada, só disponível em CSV) — o que ele tem, verificado numa amostra
-- real do arquivo, é um registro por unidade de saúde com UF e esfera
-- administrativa. Agregado por estado, isso alimenta a métrica "Unidades de
-- Saúde" que a aba Recursos do dashboard hoje mostra como não implementada.
--
-- Diferente das tabelas de schema.sql (colunas tipadas, uma por campo do
-- CSV), aqui o resultado da agregação (total por UF + detalhamento por
-- esfera administrativa) é guardado como está, numa coluna JSON nativa — é
-- isso que caracteriza o padrão "JSON via API" como diferente do padrão
-- relacional: o dado chega semi-estruturado de uma API/fonte pública e é
-- preservado nesse formato, não normalizado em colunas fixas.
-- =============================================================================

CREATE TABLE cnes_estabelecimentos_raw (
  co_uf         VARCHAR2(2),
  payload       JSON,
  carregado_em  TIMESTAMP DEFAULT SYSTIMESTAMP
);

COMMENT ON TABLE cnes_estabelecimentos_raw IS 'Payload bruto (JSON) agregado por UF a partir do dump público de Estabelecimentos do CNES/Ministério da Saúde — total de unidades de saúde e detalhamento por esfera administrativa (municipal/estadual/federal)';

-- View que extrai o total de unidades de saúde por UF a partir do JSON bruto,
-- usando JSON_TABLE (SQL nativo do Oracle para consultar JSON sem precisar
-- normalizar a tabela) — é essa view que dados_reais/gerar_sql_cnes.py também
-- usa como referência para gerar dados/cnes_estabelecimentos_estado.csv, que
-- o dashboard estático consome.
CREATE OR REPLACE VIEW recursos_cnes_estado AS
SELECT
  r.co_uf,
  jt.uf,
  jt.total_estabelecimentos
FROM cnes_estabelecimentos_raw r,
     JSON_TABLE(
       r.payload, '$'
       COLUMNS (
         uf                     VARCHAR2(60) PATH '$.uf',
         total_estabelecimentos NUMBER       PATH '$.total_estabelecimentos'
       )
     ) jt;

COMMENT ON TABLE recursos_cnes_estado IS 'Total de unidades de saúde por UF (CNES/Ministério da Saúde), extraído do JSON bruto de cnes_estabelecimentos_raw';

-- Teste rápido depois de rodar oracle/carga_cnes.sql:
-- SELECT uf, total_estabelecimentos FROM recursos_cnes_estado ORDER BY total_estabelecimentos DESC;

-- Exemplo de consulta que aproveita o detalhamento por esfera administrativa,
-- ainda dentro do JSON bruto (mostra que o dado semi-estruturado continua
-- consultável mesmo sem ter sido normalizado em colunas) — JSON_VALUE lê uma
-- chave específica do objeto "por_esfera" direto do JSON:
-- SELECT co_uf,
--        JSON_VALUE(payload, '$.por_esfera.MUNICIPAL') AS municipal,
--        JSON_VALUE(payload, '$.por_esfera.ESTADUAL')  AS estadual,
--        JSON_VALUE(payload, '$.por_esfera.FEDERAL')   AS federal
-- FROM cnes_estabelecimentos_raw
-- ORDER BY co_uf;
