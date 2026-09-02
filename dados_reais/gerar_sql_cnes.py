# -*- coding: utf-8 -*-
"""
Gera a carga do padrão "JSON via API" (CNES) a partir do dump público de
estabelecimentos do CNES (Ministério da Saúde / dadosabertos.saude.gov.br,
arquivo hospedado em ckan.saude.gov.br).

Por que "unidades de saúde" e não "leitos": o dump de Estabelecimentos do CNES
não traz contagem de leitos (isso fica numa tabela CNES separada, "Leitos",
disponível só em CSV, não em JSON) — confirmado inspecionando uma amostra real
do arquivo. O que o dump de Estabelecimentos tem, de forma confiável, é um
registro por unidade de saúde com UF (CO_UF) e esfera administrativa
(DS_ESFERA_ADMINISTRATIVA); agregado por estado, isso preenche exatamente a
lacuna que o README already registra como não implementada na aba Recursos
("Unidades de Saúde" no mapa).

Não conecta em nenhum banco (mesma razão do gerar_sql_relacional.py: o FreeSQL
não libera conexão externa) — só baixa o JSON público, agrega localmente e
escreve dois arquivos:
  - oracle/carga_cnes.sql        (INSERT com 1 documento JSON por UF, para
                                   colar no worksheet depois de oracle/cnes_json.sql)
  - dados/cnes_estabelecimentos_estado.csv  (uf, total_estabelecimentos —
                                   consumido pelo dashboard, aba Recursos)

O arquivo de origem é grande (~640 MB descompactado) — o download e o parsing
levam alguns minutos. Processado em streaming (sem carregar tudo em memória).

Uso:
    cd dados_reais
    python gerar_sql_cnes.py
"""
import io
import os
import re
import urllib.request
import zipfile

URL_CNES_ZIP = 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/CNES/cnes_estabelecimentos_json.zip'
NOME_ARQUIVO_NO_ZIP = 'cnes_estabelecimentos.json'

OUT_SQL = os.path.join(os.path.dirname(__file__), '..', 'oracle', 'carga_cnes.sql')
OUT_CSV = os.path.join(os.path.dirname(__file__), '..', 'dados', 'cnes_estabelecimentos_estado.csv')

# Código IBGE de UF -> nome completo, no mesmo formato usado nos outros CSVs
# de dados/ (ver acidentes_estado.csv) — precisa bater para o dashboard casar
# os dados por nome do estado.
UF_POR_CODIGO = {
    '11': 'Rondônia', '12': 'Acre', '13': 'Amazonas', '14': 'Roraima',
    '15': 'Pará', '16': 'Amapá', '17': 'Tocantins', '21': 'Maranhão',
    '22': 'Piauí', '23': 'Ceará', '24': 'Rio Grande do Norte',
    '25': 'Paraíba', '26': 'Pernambuco', '27': 'Alagoas', '28': 'Sergipe',
    '29': 'Bahia', '31': 'Minas Gerais', '32': 'Espírito Santo',
    '33': 'Rio de Janeiro', '35': 'São Paulo', '41': 'Paraná',
    '42': 'Santa Catarina', '43': 'Rio Grande do Sul',
    '50': 'Mato Grosso do Sul', '51': 'Mato Grosso', '52': 'Goiás',
    '53': 'Distrito Federal',
}

RE_UF = re.compile(r'"CO_UF":"(\d{2})"')
RE_ESFERA = re.compile(r'"DS_ESFERA_ADMINISTRATIVA":"([^"]*)"')
CHUNK = 8 * 1024 * 1024


def baixar_zip():
    caminho_local = os.path.join(os.path.dirname(__file__), 'cnes_estabelecimentos_json.zip')
    if os.path.exists(caminho_local):
        print(f'Usando zip já baixado em {caminho_local}')
        return caminho_local
    print(f'Baixando {URL_CNES_ZIP} ...')
    urllib.request.urlretrieve(URL_CNES_ZIP, caminho_local)
    print('Download concluído.')
    return caminho_local


def agregar_por_uf(caminho_zip):
    """
    Lê cnes_estabelecimentos.json de dentro do zip em blocos (sem extrair nem
    carregar tudo em memória) e conta estabelecimentos por UF e por esfera
    administrativa. Cada registro tem exatamente um CO_UF seguido, mais
    adiante no mesmo objeto, de um DS_ESFERA_ADMINISTRATIVA — então basta
    lembrar o último CO_UF visto e atribuir a próxima esfera encontrada a ele.
    """
    contagem = {cod: {'total': 0, 'por_esfera': {}} for cod in UF_POR_CODIGO}
    uf_atual = None
    resto = ''

    with zipfile.ZipFile(caminho_zip) as z:
        with z.open(NOME_ARQUIVO_NO_ZIP) as f:
            while True:
                bloco = f.read(CHUNK)
                if not bloco:
                    break
                texto = resto + bloco.decode('utf-8', errors='ignore')

                # processa UFs e esferas na ordem em que aparecem no texto
                eventos = []
                for m in RE_UF.finditer(texto):
                    eventos.append((m.start(), 'uf', m.group(1)))
                for m in RE_ESFERA.finditer(texto):
                    eventos.append((m.start(), 'esfera', m.group(1).strip() or 'NÃO INFORMADA'))
                eventos.sort(key=lambda e: e[0])

                for _, tipo, valor in eventos:
                    if tipo == 'uf':
                        uf_atual = valor if valor in UF_POR_CODIGO else None
                        if uf_atual:
                            contagem[uf_atual]['total'] += 1
                    elif tipo == 'esfera' and uf_atual:
                        d = contagem[uf_atual]['por_esfera']
                        d[valor] = d.get(valor, 0) + 1

                # guarda a cauda do texto (pode conter um campo cortado ao meio)
                resto = texto[-200:]

    return contagem


def escrever_sql(contagem):
    linhas = [
        "-- =============================================================================\n",
        "-- SEDAT-SUS — carga do padrão \"JSON via API\" (CNES)\n",
        "-- Gerado por dados_reais/gerar_sql_cnes.py — NÃO editar à mão, rode o script\n",
        "-- de novo para atualizar (o CNES é atualizado periodicamente pelo Ministério\n",
        "-- da Saúde).\n",
        "-- Rode DEPOIS de oracle/cnes_json.sql (que cria a tabela cnes_estabelecimentos_raw\n",
        "-- e a view recursos_cnes_estado), conectado como sedat_app.\n",
        "-- =============================================================================\n\n",
        "TRUNCATE TABLE cnes_estabelecimentos_raw;\n",
    ]
    for cod, nome in UF_POR_CODIGO.items():
        dados = contagem[cod]
        esferas = ', '.join(f'"{k}": {v}' for k, v in sorted(dados['por_esfera'].items()))
        payload = f'{{"uf": "{nome}", "total_estabelecimentos": {dados["total"]}, "por_esfera": {{{esferas}}}}}'
        payload_sql = payload.replace("'", "''")
        linhas.append(
            f"INSERT INTO cnes_estabelecimentos_raw (co_uf, payload) VALUES ('{cod}', '{payload_sql}');\n"
        )
    os.makedirs(os.path.dirname(OUT_SQL), exist_ok=True)
    with open(OUT_SQL, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    print(f'Gerado {OUT_SQL}')


def escrever_csv(contagem):
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        f.write('uf,total_estabelecimentos\n')
        for cod, nome in UF_POR_CODIGO.items():
            f.write(f'{nome},{contagem[cod]["total"]}\n')
    print(f'Gerado {OUT_CSV}')


def main():
    caminho_zip = baixar_zip()
    print('Processando (streaming, pode levar alguns minutos)...')
    contagem = agregar_por_uf(caminho_zip)
    total_geral = sum(c['total'] for c in contagem.values())
    print(f'Total de estabelecimentos contados: {total_geral}')
    escrever_sql(contagem)
    escrever_csv(contagem)


if __name__ == '__main__':
    main()
