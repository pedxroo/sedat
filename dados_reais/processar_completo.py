# -*- coding: utf-8 -*-
"""
Gera todos os CSVs de /dados a partir dos dados reais da PRF (datatran2025 + datatran2026).

Substitui processar.py (que só usava datatran2026 e reaproveitava dados de exemplo para
KPIs e previsões). Este script:
  - combina todos os meses reais disponíveis em datatran2025.csv + datatran2026/*.csv;
  - calcula KPIs comparando o ano corrente com o ano anterior, no mesmo recorte de meses
    (ex.: Jan-Jul/2026 vs Jan-Jul/2025) — o recorte se ajusta sozinho ao mês mais recente
    disponível nos dados, então basta baixar um datatran2026.csv atualizado e rodar de novo;
  - treina uma regressão linear simples (numpy, sem dependências externas) sobre a série
    mensal real para prever os próximos 6 meses;
  - usa o clima de 2025 (dados/clima_mensal_2025.csv) como padrão sazonal para os meses
    futuros, já que ainda não há observação climática para eles.

Limitação conhecida (ver README): não conseguimos automatizar a extração do SIH filtrado
por "causas externas / acidentes de transporte" no TabNet do DATASUS (a consulta certa é
Morbidade Hospitalar > Lista Morb CID-10 > "Acidentes de transporte", mas o tabcgi.exe
rejeita a submissão fora do navegador interativo — parece exigir o encoding ISO-8859-1
exato dos nomes de campo, que não reproduzimos de forma confiável).
Por isso "Leitos Ocupados" é uma estimativa baseada em feridos_graves (feridos graves em
acidentes de trânsito), não o número oficial de leitos do SIH. Ver README para o caminho
manual caso alguém quera buscar o número oficial depois.
"""
import pandas as pd
import numpy as np

MESES_PT = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
UF_NOME = {
    'AC':'Acre','AL':'Alagoas','AP':'Amapá','AM':'Amazonas','BA':'Bahia','CE':'Ceará',
    'DF':'Distrito Federal','ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MT':'Mato Grosso',
    'MS':'Mato Grosso do Sul','MG':'Minas Gerais','PA':'Pará','PB':'Paraíba','PR':'Paraná',
    'PE':'Pernambuco','PI':'Piauí','RJ':'Rio de Janeiro','RN':'Rio Grande do Norte',
    'RS':'Rio Grande do Sul','RO':'Rondônia','RR':'Roraima','SC':'Santa Catarina',
    'SP':'São Paulo','SE':'Sergipe','TO':'Tocantins'
}
DIA_MAP = {
    'segunda-feira':'Seg','terça-feira':'Ter','quarta-feira':'Qua','quinta-feira':'Qui',
    'sexta-feira':'Sex','sábado':'Sáb','domingo':'Dom',
}
ORDEM_DIA = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']

# ---------- carga ----------
d25 = pd.read_csv('datatran2025.csv', sep=';', encoding='latin1')
d25['data_inversa'] = pd.to_datetime(d25['data_inversa'])
d26 = pd.read_csv('datatran2026/datatran2026.csv', sep=';', encoding='latin1', low_memory=False)
d26['data_inversa'] = pd.to_datetime(d26['data_inversa'], format='mixed')

cols_comuns = [c for c in d25.columns if c in d26.columns]
df = pd.concat([d25[cols_comuns], d26[cols_comuns]], ignore_index=True)
df['ano'] = df['data_inversa'].dt.year
df['mes_num'] = df['data_inversa'].dt.month
df['hora'] = pd.to_datetime(df['horario'], format='%H:%M:%S').dt.hour
df['dia_norm'] = df['dia_semana'].str.lower().str.strip().map(DIA_MAP)
for col in ['mortos','feridos_leves','feridos_graves','feridos','pessoas','veiculos']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

total = len(df)
print(f'Total combinado: {total} acidentes')

# ---------- corte de meses incompletos (defasagem de processamento da PRF) ----------
# Os meses mais recentes do datatran costumam vir parcialmente preenchidos (os boletins
# de acidente continuam chegando por semanas/meses após o fato). Um mês cujo volume cai
# muito abaixo da tendência recente quase certamente não é uma queda real de acidentes —
# é o arquivo ainda sendo populado. Cortamos esses meses do fim da série antes de gerar
# qualquer KPI/gráfico/previsão, para não fabricar uma "queda" que é só atraso de dado.
contagem_mensal_bruta = df.groupby(['ano','mes_num']).size().reset_index(name='n').sort_values(['ano','mes_num'])
while len(contagem_mensal_bruta) > 3:
    ultimos3_media = contagem_mensal_bruta['n'].iloc[-4:-1].mean()
    ultimo_n = contagem_mensal_bruta['n'].iloc[-1]
    if ultimo_n < 0.6 * ultimos3_media:
        ano_corte, mes_corte = int(contagem_mensal_bruta.iloc[-1]['ano']), int(contagem_mensal_bruta.iloc[-1]['mes_num'])
        print(f'  AVISO: {MESES_PT[mes_corte]}/{ano_corte} tem so {int(ultimo_n)} registros '
              f'(media dos 3 meses anteriores: {ultimos3_media:.0f}) - parece incompleto, excluido da serie.')
        df = df[~((df['ano']==ano_corte) & (df['mes_num']==mes_corte))]
        contagem_mensal_bruta = contagem_mensal_bruta.iloc[:-1]
    else:
        break

total = len(df)
print(f'Total após corte de meses incompletos: {total} acidentes')

def mes_label(ano, mes):
    return f"{MESES_PT[mes]}/{str(ano)[2:]}"

# ---------- acidentes_mensal.csv (série mensal real completa) ----------
mensal = df.groupby(['ano','mes_num']).size().reset_index(name='acidentes').sort_values(['ano','mes_num'])
with open('../dados/acidentes_mensal.csv', 'w', encoding='utf-8') as f:
    f.write('mes,acidentes\n')
    for _, r in mensal.iterrows():
        f.write(f"{mes_label(int(r['ano']), int(r['mes_num']))},{int(r['acidentes'])}\n")

# ---------- acidentes_mensal_estado.csv (filtro de Estado no gráfico Evolução) ----------
meses_ordem = list(mensal[['ano','mes_num']].itertuples(index=False, name=None))
mensal_uf = df.groupby(['uf','ano','mes_num']).size().reset_index(name='acidentes')
mensal_uf_idx = mensal_uf.set_index(['uf','ano','mes_num'])['acidentes']
with open('../dados/acidentes_mensal_estado.csv', 'w', encoding='utf-8') as f:
    f.write('uf,mes,acidentes\n')
    for uf in sorted(df['uf'].unique()):
        for ano, mes in meses_ordem:
            n = mensal_uf_idx.get((uf, ano, mes), 0)
            f.write(f"{UF_NOME.get(uf, uf)},{mes_label(ano, mes)},{int(n)}\n")

# ---------- acidentes_estado.csv ----------
por_uf = df['uf'].value_counts()
with open('../dados/acidentes_estado.csv', 'w', encoding='utf-8') as f:
    f.write('uf,acidentes\n')
    for uf, n in por_uf.items():
        f.write(f"{UF_NOME.get(uf, uf)},{n}\n")

# ---------- recursos_estado.csv (aba Recursos) ----------
# Não há fonte pública de capacidade instalada (leitos/ambulâncias) por UF nos dados
# coletados (ver README) — aqui é só o lado da demanda, mesmos proxies do restante do
# dashboard (feridos_graves = leitos; feridos_leves+feridos_graves+mortos = atendimentos).
rec_uf = df.groupby('uf').agg(
    leitos_estim=('feridos_graves','sum'), obitos=('mortos','sum'),
    feridos_leves=('feridos_leves','sum')).reset_index()
rec_uf['atendimentos_estim'] = rec_uf['feridos_leves'] + rec_uf['leitos_estim'] + rec_uf['obitos']
rec_uf = rec_uf.sort_values('leitos_estim', ascending=False)
with open('../dados/recursos_estado.csv', 'w', encoding='utf-8') as f:
    f.write('uf,leitos_estim,atendimentos_estim,obitos\n')
    for _, r in rec_uf.iterrows():
        f.write(f"{UF_NOME.get(r['uf'], r['uf'])},{int(r['leitos_estim'])},{int(r['atendimentos_estim'])},{int(r['obitos'])}\n")

# ---------- tipos_acidente.csv ----------
tipos = df['tipo_acidente'].value_counts()
top5 = tipos.head(5)
outros = tipos.iloc[5:].sum()
with open('../dados/tipos_acidente.csv', 'w', encoding='utf-8') as f:
    f.write('tipo,percentual\n')
    for t, n in top5.items():
        f.write(f"{t},{round(n/total*100,1)}\n")
    if outros > 0:
        f.write(f"Outros,{round(outros/total*100,1)}\n")

# ---------- faixa_horaria.csv ----------
bins = [(0,3),(3,6),(6,9),(9,12),(12,15),(15,18),(18,21),(21,24)]
with open('../dados/faixa_horaria.csv', 'w', encoding='utf-8') as f:
    f.write('faixa,percentual\n')
    for a,b in bins:
        n = df[(df['hora']>=a) & (df['hora']<b)].shape[0]
        f.write(f"{a:02d}-{b:02d},{round(n/total*100,1)}\n")

# ---------- dia_semana.csv ----------
dia_counts = df['dia_norm'].value_counts()
with open('../dados/dia_semana.csv', 'w', encoding='utf-8') as f:
    f.write('dia,percentual\n')
    for dnome in ORDEM_DIA:
        n = dia_counts.get(dnome, 0)
        f.write(f"{dnome},{round(n/total*100,1)}\n")

# ---------- municipios.csv (Top 30 nacional — "Ver todos" mostra essa lista inteira) ----------
mun = df.groupby(['municipio','uf']).size().sort_values(ascending=False).head(30)
with open('../dados/municipios.csv', 'w', encoding='utf-8') as f:
    f.write('municipio,uf,acidentes\n')
    for (m, uf), n in mun.items():
        f.write(f"{m.title()},{uf},{n}\n")

# ---------- rodovias.csv (Top 20 nacional) ----------
br = df.dropna(subset=['br']).groupby('br').size().sort_values(ascending=False).head(20)
with open('../dados/rodovias.csv', 'w', encoding='utf-8') as f:
    f.write('rodovia,trecho,acidentes,percentual\n')
    for b, n in br.items():
        ufs = df[df['br']==b]['uf'].value_counts().head(3).index.tolist()
        trecho = 'Trechos em ' + '/'.join(ufs)
        f.write(f'BR-{int(b):03d},"{trecho}",{n},"{round(n/total*100,1)}%"\n')

# ---------- causas_acidente.csv (aba Análises) ----------
causas = df['causa_acidente'].dropna().value_counts()
top8 = causas.head(8)
outros_causas = causas.iloc[8:].sum()
with open('../dados/causas_acidente.csv', 'w', encoding='utf-8') as f:
    f.write('causa,percentual\n')
    for c, n in top8.items():
        f.write(f"{c},{round(n/total*100,1)}\n")
    if outros_causas > 0:
        f.write(f"Outras causas,{round(outros_causas/total*100,1)}\n")

# ---------- condicao_metereologica.csv (aba Análises) ----------
clima_cond = df['condicao_metereologica'].dropna().value_counts()
with open('../dados/condicao_metereologica.csv', 'w', encoding='utf-8') as f:
    f.write('condicao,percentual\n')
    for c, n in clima_cond.items():
        f.write(f"{c},{round(n/total*100,1)}\n")

# ---------- gravidade_acidente.csv (aba Análises) ----------
grav = df['classificacao_acidente'].dropna().value_counts()
with open('../dados/gravidade_acidente.csv', 'w', encoding='utf-8') as f:
    f.write('classificacao,percentual\n')
    for c, n in grav.items():
        f.write(f"{c},{round(n/total*100,1)}\n")

# ---------- mortos_feridos_mensal.csv (aba Análises) ----------
mf = df.groupby(['ano','mes_num']).agg(mortos=('mortos','sum'), feridos_graves=('feridos_graves','sum'),
                                        feridos_leves=('feridos_leves','sum')).reset_index().sort_values(['ano','mes_num'])
with open('../dados/mortos_feridos_mensal.csv', 'w', encoding='utf-8') as f:
    f.write('mes,mortos,feridos_graves,feridos_leves\n')
    for _, r in mf.iterrows():
        f.write(f"{mes_label(int(r['ano']), int(r['mes_num']))},{int(r['mortos'])},{int(r['feridos_graves'])},{int(r['feridos_leves'])}\n")

# ---------- kpis_analises.csv (aba Análises) ----------
taxa_letalidade = round(df['mortos'].sum() / total * 100, 2)
pct_fatais = round((df['classificacao_acidente']=='Com Vítimas Fatais').sum() / total * 100, 1)
media_pessoas = round(df['pessoas'].sum() / total, 1)
media_veiculos = round(df['veiculos'].sum() / total, 1)
with open('../dados/kpis_analises.csv', 'w', encoding='utf-8') as f:
    f.write('indicador,valor\n')
    f.write(f'Taxa de Letalidade,{taxa_letalidade}\n')
    f.write(f'Pct Acidentes Fatais,{pct_fatais}\n')
    f.write(f'Media Pessoas por Acidente,{media_pessoas}\n')
    f.write(f'Media Veiculos por Acidente,{media_veiculos}\n')

# ---------- KPIs: ano corrente vs ano anterior, mesmo recorte de meses (dinâmico) ----------
ano_atual = int(df['ano'].max())
ultimo_mes_atual = int(df[df['ano']==ano_atual]['mes_num'].max())
cur = df[(df['ano']==ano_atual) & (df['mes_num']<=ultimo_mes_atual)]
prev = df[(df['ano']==ano_atual-1) & (df['mes_num']<=ultimo_mes_atual)]
print(f'Recorte de comparação: Jan-{MESES_PT[ultimo_mes_atual]}/{ano_atual} vs Jan-{MESES_PT[ultimo_mes_atual]}/{ano_atual-1}')

def var_pct(c, p):
    if p == 0: return 0.0
    return round((c - p) / p * 100, 1)

acidentes_cur, acidentes_prev = len(cur), len(prev)
obitos_cur, obitos_prev = int(cur['mortos'].sum()), int(prev['mortos'].sum())
leitos_cur, leitos_prev = int(cur['feridos_graves'].sum()), int(prev['feridos_graves'].sum())
atend_cur = int(cur['feridos_leves'].sum() + cur['feridos_graves'].sum() + cur['mortos'].sum())
atend_prev = int(prev['feridos_leves'].sum() + prev['feridos_graves'].sum() + prev['mortos'].sum())
vitimas_cur = int((cur['classificacao_acidente'] != 'Sem Vítimas').sum())
vitimas_prev = int((prev['classificacao_acidente'] != 'Sem Vítimas').sum())

def trend(c, p):
    return 'up' if c >= p else 'down'

with open('../dados/kpis.csv', 'w', encoding='utf-8') as f:
    f.write('indicador,valor,variacao,tendencia\n')
    f.write(f'Acidentes,{acidentes_cur},"{abs(var_pct(acidentes_cur,acidentes_prev))}%",{trend(acidentes_cur,acidentes_prev)}\n')
    f.write(f'Leitos Ocupados,{leitos_cur},"{abs(var_pct(leitos_cur,leitos_prev))}%",{trend(leitos_cur,leitos_prev)}\n')
    f.write(f'Acidentes com Vítimas,{vitimas_cur},"{abs(var_pct(vitimas_cur,vitimas_prev))}%",{trend(vitimas_cur,vitimas_prev)}\n')
    f.write(f'Atendimentos,{atend_cur},"{abs(var_pct(atend_cur,atend_prev))}%",{trend(atend_cur,atend_prev)}\n')
    f.write(f'Óbitos,{obitos_cur},"{abs(var_pct(obitos_cur,obitos_prev))}%",{trend(obitos_cur,obitos_prev)}\n')

print(f'KPIs Jan-{MESES_PT[ultimo_mes_atual]}/{ano_atual} vs Jan-{MESES_PT[ultimo_mes_atual]}/{ano_atual-1}:')
print(f'  Acidentes: {acidentes_cur} vs {acidentes_prev} ({var_pct(acidentes_cur,acidentes_prev)}%)')
print(f'  Leitos (proxy feridos graves): {leitos_cur} vs {leitos_prev} ({var_pct(leitos_cur,leitos_prev)}%)')
print(f'  Acidentes c/ vítimas: {vitimas_cur} vs {vitimas_prev}')
print(f'  Atendimentos (proxy): {atend_cur} vs {atend_prev}')
print(f'  Óbitos: {obitos_cur} vs {obitos_prev}')

# ---------- Previsão: regressão linear múltipla (numpy, sem sklearn) ----------
# y = b0 + b1*t + b2*temperatura + b3*precipitação
# t = índice do mês (0..16), clima = clima_mensal_2025.csv casado por mês-do-ano
# (assume padrão sazonal 2025 se repete em 2026 — simplificação assumida e documentada)
clima = pd.read_csv('../dados/clima_mensal_2025.csv')
clima['mes_num'] = clima['mes'].str.extract(r'([A-Za-zç]+)/')[0].map(
    {v:k for k,v in MESES_PT.items()})
clima_by_month = clima.set_index('mes_num')[['temperatura_media_c','precipitacao_media_mm']]

serie = mensal.reset_index(drop=True).copy()
serie['t'] = np.arange(len(serie))
serie = serie.merge(clima_by_month, left_on='mes_num', right_index=True, how='left')

# variáveis-alvo mensais adicionais
for col, src in [('obitos','mortos'), ('leitos','feridos_graves'),
                  ('atendimentos', None)]:
    pass

extra = df.groupby(['ano','mes_num']).agg(
    obitos=('mortos','sum'), leitos=('feridos_graves','sum'),
    feridos_leves=('feridos_leves','sum')).reset_index()
serie = serie.merge(extra, on=['ano','mes_num'], how='left')
serie['atendimentos'] = serie['feridos_leves'] + serie['leitos'] + serie['obitos']

X = np.column_stack([
    np.ones(len(serie)), serie['t'].values,
    serie['temperatura_media_c'].values, serie['precipitacao_media_mm'].values,
])

def fit_predict(y_col, future_t, future_temp, future_precip):
    y = serie[y_col].values.astype(float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    Xf = np.column_stack([np.ones(len(future_t)), future_t, future_temp, future_precip])
    pred = Xf @ coef
    return np.maximum(pred, 0), coef

def proximos_n_meses(ano, mes, n):
    out = []
    for _ in range(n):
        mes += 1
        if mes > 12:
            mes = 1; ano += 1
        out.append((ano, mes))
    return out

ultimo_ano_serie, ultimo_mes_serie = int(serie.iloc[-1]['ano']), int(serie.iloc[-1]['mes_num'])
future_months = proximos_n_meses(ultimo_ano_serie, ultimo_mes_serie, 6)
print(f'Previsão para: {", ".join(mes_label(a,m) for a,m in future_months)}')
future_t = np.arange(len(serie), len(serie) + 6)
future_temp = np.array([clima_by_month.loc[m, 'temperatura_media_c'] for _, m in future_months])
future_precip = np.array([clima_by_month.loc[m, 'precipitacao_media_mm'] for _, m in future_months])

pred_acidentes, coef_acid = fit_predict('acidentes', future_t, future_temp, future_precip)
pred_leitos, _ = fit_predict('leitos', future_t, future_temp, future_precip)
pred_obitos, _ = fit_predict('obitos', future_t, future_temp, future_precip)
pred_atend, _ = fit_predict('atendimentos', future_t, future_temp, future_precip)

# previsao_mensal.csv: real (série completa) + previsto (6 meses futuros), série de acidentes
with open('../dados/previsao_mensal.csv', 'w', encoding='utf-8') as f:
    f.write('mes,real,previsto\n')
    for _, r in serie.iterrows():
        f.write(f"{mes_label(int(r['ano']), int(r['mes_num']))},{int(r['acidentes'])},\n")
    for (ano, m), prev_v in zip(future_months, pred_acidentes):
        f.write(f"{mes_label(ano, m)},,{int(round(prev_v))}\n")

# previsao_semestre.csv: leitos (proxy) previstos por mês, próximo semestre
with open('../dados/previsao_semestre.csv', 'w', encoding='utf-8') as f:
    f.write('mes,previsto\n')
    for (ano, m), prev_v in zip(future_months, pred_leitos):
        f.write(f"{mes_label(ano, m).lower()},{int(round(prev_v))}\n")

# kpis_previsao.csv: soma dos 6 meses previstos vs soma dos últimos 6 meses reais
ultimos6 = serie.tail(6)
def pct(fut_sum, real_sum):
    if real_sum == 0: return 0.0
    return round((fut_sum - real_sum) / real_sum * 100, 1)

leitos_fut_sum, leitos_real_sum = pred_leitos.sum(), ultimos6['leitos'].sum()
obitos_fut_sum, obitos_real_sum = pred_obitos.sum(), ultimos6['obitos'].sum()
atend_fut_sum, atend_real_sum = pred_atend.sum(), ultimos6['atendimentos'].sum()
acid_fut_sum, acid_real_sum = pred_acidentes.sum(), ultimos6['acidentes'].sum()

with open('../dados/kpis_previsao.csv', 'w', encoding='utf-8') as f:
    f.write('indicador,valor,variacao\n')
    f.write(f'Leitos,{int(round(leitos_fut_sum))},"{abs(pct(leitos_fut_sum,leitos_real_sum))}%"\n')
    f.write(f'Acidentes,{int(round(acid_fut_sum))},"{abs(pct(acid_fut_sum,acid_real_sum))}%"\n')
    f.write(f'Atendimentos,{int(round(atend_fut_sum))},"{abs(pct(atend_fut_sum,atend_real_sum))}%"\n')
    f.write(f'Óbitos,{int(round(obitos_fut_sum))},"{abs(pct(obitos_fut_sum,obitos_real_sum))}%"\n')

# comparacao_real_previsto.csv
with open('../dados/comparacao_real_previsto.csv', 'w', encoding='utf-8') as f:
    f.write('recurso,icone,real,previsto,variacao\n')
    f.write(f'Leitos Ocupados,🛏️,{int(leitos_real_sum)},{int(round(leitos_fut_sum))},"{pct(leitos_fut_sum,leitos_real_sum)}%"\n')
    f.write(f'Acidentes,🚗,{int(acid_real_sum)},{int(round(acid_fut_sum))},"{pct(acid_fut_sum,acid_real_sum)}%"\n')
    f.write(f'Atendimentos,🧑‍⚕️,{int(atend_real_sum)},{int(round(atend_fut_sum))},"{pct(atend_fut_sum,atend_real_sum)}%"\n')
    f.write(f'Óbitos,❤️,{int(obitos_real_sum)},{int(round(obitos_fut_sum))},"{pct(obitos_fut_sum,obitos_real_sum)}%"\n')

# fatores_impacto.csv: peso de cada variável no modelo de acidentes (coef padronizado)
std_t = serie['t'].std()
std_temp = serie['temperatura_media_c'].std()
std_precip = serie['precipitacao_media_mm'].std()
std_y = serie['acidentes'].std()
pesos = {
    'Tendência Temporal (mês)': abs(coef_acid[1] * std_t / std_y),
    'Temperatura Média': abs(coef_acid[2] * std_temp / std_y),
    'Precipitação Média': abs(coef_acid[3] * std_precip / std_y),
}
# adiciona concentração por tipo/horário/dia como sinal descritivo (não é coeficiente do
# modelo, mas ajuda a explicar a variação — mantido para contexto do usuário)
pesos['Tipo de Acidente (concentração)'] = tipos.iloc[0] / total
pesos['Horário (concentração faixa pico)'] = df.groupby(
    df['hora'].apply(lambda h: h//3)).size().max() / total
soma = sum(pesos.values())
pesos_norm = {k: v/soma for k, v in pesos.items()}
with open('../dados/fatores_impacto.csv', 'w', encoding='utf-8') as f:
    f.write('fator,importancia\n')
    for k, v in sorted(pesos_norm.items(), key=lambda kv: -kv[1]):
        f.write(f'{k},{round(v,3)}\n')

# ---------- acidentes_estado_tipo.csv (filtro de Tipo de Acidente por Estado) ----------
tipo_uf = df.groupby(['uf','tipo_acidente']).size().reset_index(name='acidentes')
with open('../dados/acidentes_estado_tipo.csv', 'w', encoding='utf-8') as f:
    f.write('uf,tipo,acidentes\n')
    for _, r in tipo_uf.iterrows():
        f.write(f"{UF_NOME.get(r['uf'], r['uf'])},{r['tipo_acidente']},{int(r['acidentes'])}\n")

# ---------- municipios_estado.csv (filtro de Município por Estado — Top 15 por UF) ----------
with open('../dados/municipios_estado.csv', 'w', encoding='utf-8') as f:
    f.write('uf,municipio,acidentes\n')
    for uf in sorted(df['uf'].unique()):
        top_mun = df[df['uf']==uf].groupby('municipio').size().sort_values(ascending=False).head(15)
        for m, n in top_mun.items():
            f.write(f"{UF_NOME.get(uf, uf)},{m.title()},{int(n)}\n")

# ---------- Previsão por Estado: mesma regressão linear, uma por UF ----------
# serie_mensal_estado.csv: histórico real de acidentes/leitos/atendimentos/óbitos por UF×mês
# previsao_mensal_estado.csv: os 6 meses seguintes previstos, mesmas 4 métricas
# kpis_previsao_estado.csv: soma dos 6 meses previstos vs últimos 6 meses reais, por UF
serie_uf_full = df.groupby(['uf','ano','mes_num']).agg(
    acidentes=('mortos','size'), obitos=('mortos','sum'),
    leitos_estim=('feridos_graves','sum'), feridos_leves=('feridos_leves','sum')).reset_index()
serie_uf_full['atendimentos_estim'] = serie_uf_full['feridos_leves'] + serie_uf_full['leitos_estim'] + serie_uf_full['obitos']

with open('../dados/serie_mensal_estado.csv', 'w', encoding='utf-8') as f, \
     open('../dados/previsao_mensal_estado.csv', 'w', encoding='utf-8') as fp, \
     open('../dados/kpis_previsao_estado.csv', 'w', encoding='utf-8') as fk:
    f.write('uf,mes,acidentes,leitos_estim,atendimentos_estim,obitos\n')
    fp.write('uf,mes,previsto_acidentes,previsto_leitos,previsto_atendimentos,previsto_obitos\n')
    fk.write('uf,acidentes_valor,acidentes_variacao,leitos_valor,leitos_variacao,atendimentos_valor,atendimentos_variacao,obitos_valor,obitos_variacao\n')
    for uf in sorted(df['uf'].unique()):
        s = serie_uf_full[serie_uf_full['uf']==uf].set_index(['ano','mes_num'])
        rows = []
        for ano, mes in meses_ordem:
            r = s.loc[(ano,mes)] if (ano,mes) in s.index else None
            vals = {'acidentes':0,'leitos_estim':0,'atendimentos_estim':0,'obitos':0} if r is None else \
                   {'acidentes':int(r['acidentes']),'leitos_estim':int(r['leitos_estim']),
                    'atendimentos_estim':int(r['atendimentos_estim']),'obitos':int(r['obitos'])}
            rows.append(vals)
            f.write(f"{UF_NOME.get(uf,uf)},{mes_label(ano,mes)},{vals['acidentes']},{vals['leitos_estim']},{vals['atendimentos_estim']},{vals['obitos']}\n")

        t_uf = np.arange(len(rows))
        Xuf = np.column_stack([np.ones(len(rows)), t_uf, serie['temperatura_media_c'].values, serie['precipitacao_media_mm'].values])
        Xuf_fut = np.column_stack([np.ones(6), future_t, future_temp, future_precip])

        def fit_uf(metric):
            y = np.array([r[metric] for r in rows], dtype=float)
            coef, *_ = np.linalg.lstsq(Xuf, y, rcond=None)
            return np.maximum(Xuf_fut @ coef, 0)

        pf_acid = fit_uf('acidentes'); pf_leitos = fit_uf('leitos_estim')
        pf_atend = fit_uf('atendimentos_estim'); pf_obitos = fit_uf('obitos')
        for i, (ano, mes) in enumerate(future_months):
            fp.write(f"{UF_NOME.get(uf,uf)},{mes_label(ano,mes)},{int(round(pf_acid[i]))},{int(round(pf_leitos[i]))},{int(round(pf_atend[i]))},{int(round(pf_obitos[i]))}\n")

        ultimos6_uf = rows[-6:]
        def real_sum_uf(metric): return sum(r[metric] for r in ultimos6_uf)
        def pct_uf(fut, real):
            return 0.0 if real == 0 else round((fut - real) / real * 100, 1)

        acid_r, acid_p = real_sum_uf('acidentes'), pf_acid.sum()
        leitos_r, leitos_p = real_sum_uf('leitos_estim'), pf_leitos.sum()
        atend_r, atend_p = real_sum_uf('atendimentos_estim'), pf_atend.sum()
        obitos_r, obitos_p = real_sum_uf('obitos'), pf_obitos.sum()
        fk.write(f"{UF_NOME.get(uf,uf)},{int(round(acid_p))},\"{pct_uf(acid_p,acid_r)}%\","
                 f"{int(round(leitos_p))},\"{pct_uf(leitos_p,leitos_r)}%\","
                 f"{int(round(atend_p))},\"{pct_uf(atend_p,atend_r)}%\","
                 f"{int(round(obitos_p))},\"{pct_uf(obitos_p,obitos_r)}%\"\n")

print('Previsão por estado gerada (27 UFs).')

print(f'\nArquivos gerados em ../dados/ ({len(serie)} meses reais {mes_label(int(serie.iloc[0]["ano"]),int(serie.iloc[0]["mes_num"]))}'
      f'-{mes_label(ultimo_ano_serie,ultimo_mes_serie)} + previsão {mes_label(*future_months[0])}-{mes_label(*future_months[-1])}).')
