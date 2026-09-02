# -*- coding: utf-8 -*-
"""
Gera oracle/carga_dados.sql a partir dos CSVs de /dados — INSERTs prontos para
colar no worksheet do FreeSQL (sql.oraclecloud.com) ou do Database Actions de
um Autonomous Database. Não conecta em nada: o FreeSQL não libera conexão
externa (Python/oracledb), então em vez de carregar os dados por conexão, este
script só monta o texto do SQL localmente.

Cobre o padrão "tabela relacional" (oracle/schema.sql). Não gera INSERT para
populacao_uf nem clima_mensal_2025 (viraram External Table, ver
oracle/external_table.sql) nem para o CNES (padrão "JSON via API", ver
dados_reais/gerar_sql_cnes.py).

Uso:
    cd dados_reais
    python gerar_sql_relacional.py
    -> escreve ../oracle/carga_dados.sql

Depois: abra o SQL Worksheet do FreeSQL (ou Database Actions), conectado como
sedat_app (rode oracle/schema.sql antes, como ADMIN), cole o conteúdo do
arquivo gerado e rode.
"""
import csv
import os

DADOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'dados')
SAIDA = os.path.join(os.path.dirname(__file__), '..', 'oracle', 'carga_dados.sql')

# tabela -> (arquivo csv, colunas numéricas dentre as colunas do csv)
TABELAS = {
    'acidentes_estado':          ('acidentes_estado.csv', ['acidentes']),
    'acidentes_estado_tipo':     ('acidentes_estado_tipo.csv', ['acidentes']),
    'acidentes_mensal':          ('acidentes_mensal.csv', ['acidentes']),
    'acidentes_mensal_estado':   ('acidentes_mensal_estado.csv', ['acidentes']),
    'causas_acidente':           ('causas_acidente.csv', ['percentual']),
    'comparacao_real_previsto':  ('comparacao_real_previsto.csv', ['real', 'previsto']),
    'condicao_metereologica':    ('condicao_metereologica.csv', ['percentual']),
    'dia_semana':                ('dia_semana.csv', ['percentual']),
    'faixa_horaria':             ('faixa_horaria.csv', ['percentual']),
    'fatores_impacto':           ('fatores_impacto.csv', ['importancia']),
    'gravidade_acidente':        ('gravidade_acidente.csv', ['percentual']),
    'kpis':                      ('kpis.csv', ['valor']),
    'kpis_analises':             ('kpis_analises.csv', ['valor']),
    'kpis_previsao':             ('kpis_previsao.csv', ['valor']),
    'kpis_previsao_estado':      ('kpis_previsao_estado.csv', ['acidentes_valor', 'leitos_valor', 'atendimentos_valor', 'obitos_valor']),
    'mortos_feridos_mensal':     ('mortos_feridos_mensal.csv', ['mortos', 'feridos_graves', 'feridos_leves']),
    'municipios':                ('municipios.csv', ['acidentes']),
    'municipios_estado':         ('municipios_estado.csv', ['acidentes']),
    'previsao_mensal':           ('previsao_mensal.csv', ['real', 'previsto']),
    'previsao_mensal_estado':    ('previsao_mensal_estado.csv', ['previsto_acidentes', 'previsto_leitos', 'previsto_atendimentos', 'previsto_obitos']),
    'previsao_semestre':         ('previsao_semestre.csv', ['previsto']),
    'recursos_estado':           ('recursos_estado.csv', ['leitos_estim', 'atendimentos_estim', 'obitos']),
    'rodovias':                  ('rodovias.csv', ['acidentes', 'percentual']),
    'serie_mensal_estado':       ('serie_mensal_estado.csv', ['acidentes', 'leitos_estim', 'atendimentos_estim', 'obitos']),
    'tipos_acidente':            ('tipos_acidente.csv', ['percentual']),
}


def parse_numero(v):
    """Mesma tolerância a formato do dashboard: aceita '17.8%', '1.234,5' ou vazio."""
    if v is None:
        return None
    s = str(v).strip().replace('%', '')
    if s == '' or s.lower() == 'nan':
        return None
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def sql_literal(valor):
    if valor is None:
        return 'NULL'
    if isinstance(valor, float):
        texto = ('%r' % valor).rstrip('0').rstrip('.')
        return texto if texto else '0'
    texto = str(valor).replace("'", "''")
    return f"'{texto}'"


def gerar_inserts(tabela, arquivo, colunas_numericas):
    caminho = os.path.join(DADOS_DIR, arquivo)
    if not os.path.exists(caminho):
        return f"-- [pulado] {arquivo} não encontrado em dados/\n"

    with open(caminho, encoding='utf-8-sig', newline='') as f:
        linhas = list(csv.DictReader(f))

    if not linhas:
        return f"-- [vazio] {arquivo} não tem linhas\n"

    colunas = list(linhas[0].keys())
    partes = [f"TRUNCATE TABLE {tabela};\n"]
    for linha in linhas:
        valores = []
        for col in colunas:
            bruto = linha.get(col)
            valor = parse_numero(bruto) if col in colunas_numericas else bruto
            valores.append(sql_literal(valor))
        cols_sql = ', '.join(colunas)
        vals_sql = ', '.join(valores)
        partes.append(f"INSERT INTO {tabela} ({cols_sql}) VALUES ({vals_sql});\n")
    partes.append(f"-- {len(linhas)} linhas em {tabela}\n\n")
    return ''.join(partes)


def main():
    blocos = [
        "-- =============================================================================\n",
        "-- SEDAT-SUS — carga do padrão \"tabela relacional\"\n",
        "-- Gerado por dados_reais/gerar_sql_relacional.py — NÃO editar à mão, rode o\n",
        "-- script de novo depois de atualizar os CSVs em dados/.\n",
        "-- Cole no SQL Worksheet do FreeSQL/Database Actions, conectado como sedat_app\n",
        "-- (rode oracle/schema.sql antes, como ADMIN, se ainda não rodou).\n",
        "-- =============================================================================\n\n",
    ]
    for tabela, (arquivo, numericas) in TABELAS.items():
        blocos.append(gerar_inserts(tabela, arquivo, numericas))

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, 'w', encoding='utf-8') as f:
        f.write(''.join(blocos))
    print(f'Gerado {SAIDA}')


if __name__ == '__main__':
    main()
