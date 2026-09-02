-- =============================================================================
-- SEDAT-SUS — carga do padrão "JSON via API" (CNES)
-- Gerado por dados_reais/gerar_sql_cnes.py — NÃO editar à mão, rode o script
-- de novo para atualizar (o CNES é atualizado periodicamente pelo Ministério
-- da Saúde).
-- Rode DEPOIS de oracle/cnes_json.sql (que cria a tabela cnes_estabelecimentos_raw
-- e a view recursos_cnes_estado), conectado como sedat_app.
-- =============================================================================

TRUNCATE TABLE cnes_estabelecimentos_raw;
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('11', '{"uf": "Rondônia", "total_estabelecimentos": 7320, "por_esfera": {"DUPLA": 60, "ESTADUAL": 405, "MUNICIPAL": 6848, "SEM": 7}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('12', '{"uf": "Acre", "total_estabelecimentos": 2093, "por_esfera": {"DUPLA": 5, "ESTADUAL": 305, "MUNICIPAL": 1783}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('13', '{"uf": "Amazonas", "total_estabelecimentos": 4549, "por_esfera": {"DUPLA": 11, "ESTADUAL": 1259, "MUNICIPAL": 3279}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('14', '{"uf": "Roraima", "total_estabelecimentos": 1829, "por_esfera": {"DUPLA": 31, "ESTADUAL": 70, "MUNICIPAL": 1727, "SEM": 1}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('15', '{"uf": "Pará", "total_estabelecimentos": 12677, "por_esfera": {"DUPLA": 87, "ESTADUAL": 213, "MUNICIPAL": 12377, "SEM": 1}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('16', '{"uf": "Amapá", "total_estabelecimentos": 1343, "por_esfera": {"DUPLA": 3, "ESTADUAL": 100, "MUNICIPAL": 1239}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('17', '{"uf": "Tocantins", "total_estabelecimentos": 3598, "por_esfera": {"DUPLA": 56, "ESTADUAL": 93, "MUNICIPAL": 3449}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('21', '{"uf": "Maranhão", "total_estabelecimentos": 9457, "por_esfera": {"DUPLA": 59, "ESTADUAL": 259, "MUNICIPAL": 9129, "SEM": 11}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('22', '{"uf": "Piauí", "total_estabelecimentos": 6419, "por_esfera": {"DUPLA": 89, "ESTADUAL": 283, "MUNICIPAL": 6047}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('23', '{"uf": "Ceará", "total_estabelecimentos": 19268, "por_esfera": {"DUPLA": 30, "ESTADUAL": 424, "MUNICIPAL": 18811, "SEM": 4}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('24', '{"uf": "Rio Grande do Norte", "total_estabelecimentos": 7784, "por_esfera": {"DUPLA": 108, "ESTADUAL": 71, "MUNICIPAL": 7605}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('25', '{"uf": "Paraíba", "total_estabelecimentos": 10691, "por_esfera": {"DUPLA": 59, "ESTADUAL": 163, "MUNICIPAL": 10466, "SEM": 3}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('26', '{"uf": "Pernambuco", "total_estabelecimentos": 18151, "por_esfera": {"DUPLA": 100, "ESTADUAL": 343, "MUNICIPAL": 17701, "SEM": 6}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('27', '{"uf": "Alagoas", "total_estabelecimentos": 5530, "por_esfera": {"DUPLA": 6, "ESTADUAL": 210, "MUNICIPAL": 5314}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('28', '{"uf": "Sergipe", "total_estabelecimentos": 6035, "por_esfera": {"DUPLA": 7, "ESTADUAL": 240, "MUNICIPAL": 5788}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('29', '{"uf": "Bahia", "total_estabelecimentos": 29896, "por_esfera": {"DUPLA": 825, "ESTADUAL": 471, "MUNICIPAL": 28598, "SEM": 3}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('31', '{"uf": "Minas Gerais", "total_estabelecimentos": 78252, "por_esfera": {"DUPLA": 268, "ESTADUAL": 841, "MUNICIPAL": 77138, "SEM": 5}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('32', '{"uf": "Espírito Santo", "total_estabelecimentos": 13172, "por_esfera": {"DUPLA": 142, "ESTADUAL": 926, "MUNICIPAL": 12103, "SEM": 1}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('33', '{"uf": "Rio de Janeiro", "total_estabelecimentos": 58205, "por_esfera": {"DUPLA": 36, "ESTADUAL": 369, "MUNICIPAL": 57796, "SEM": 4}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('35', '{"uf": "São Paulo", "total_estabelecimentos": 153435, "por_esfera": {"DUPLA": 100, "ESTADUAL": 807, "MUNICIPAL": 152493, "SEM": 34}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('41', '{"uf": "Paraná", "total_estabelecimentos": 43667, "por_esfera": {"DUPLA": 532, "ESTADUAL": 971, "MUNICIPAL": 42157, "SEM": 7}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('42', '{"uf": "Santa Catarina", "total_estabelecimentos": 36110, "por_esfera": {"DUPLA": 81, "ESTADUAL": 390, "MUNICIPAL": 35623, "SEM": 12}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('43', '{"uf": "Rio Grande do Sul", "total_estabelecimentos": 50435, "por_esfera": {"DUPLA": 535, "ESTADUAL": 809, "MUNICIPAL": 49091}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('50', '{"uf": "Mato Grosso do Sul", "total_estabelecimentos": 9550, "por_esfera": {"DUPLA": 50, "ESTADUAL": 60, "MUNICIPAL": 9440}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('51', '{"uf": "Mato Grosso", "total_estabelecimentos": 13889, "por_esfera": {"DUPLA": 44, "ESTADUAL": 135, "MUNICIPAL": 13710}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('52', '{"uf": "Goiás", "total_estabelecimentos": 18562, "por_esfera": {"DUPLA": 5, "ESTADUAL": 141, "MUNICIPAL": 18412, "SEM": 3}}');
INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('53', '{"uf": "Distrito Federal", "total_estabelecimentos": 12536, "por_esfera": {"DUPLA": 18, "ESTADUAL": 12202, "FEDERAL": 122, "MUNICIPAL": 194}}');
