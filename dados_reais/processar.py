# -*- coding: utf-8 -*-
import pandas as pd
import unicodedata

df = pd.read_csv('datatran2026/datatran2026.csv', sep=';', encoding='latin1')

def fix(s):
    # conserta mojibake comum de latin1 mal decodificado (ã, ç, etc. já vêm ok em latin1 real)
    return s

UF_NOME = {
    'AC':'Acre','AL':'Alagoas','AP':'Amapá','AM':'Amazonas','BA':'Bahia','CE':'Ceará',
    'DF':'Distrito Federal','ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MT':'Mato Grosso',
    'MS':'Mato Grosso do Sul','MG':'Minas Gerais','PA':'Pará','PB':'Paraíba','PR':'Paraná',
    'PE':'Pernambuco','PI':'Piauí','RJ':'Rio de Janeiro','RN':'Rio Grande do Norte',
    'RS':'Rio Grande do Sul','RO':'Rondônia','RR':'Roraima','SC':'Santa Catarina',
    'SP':'São Paulo','SE':'Sergipe','TO':'Tocantins'
}

df['data_inversa'] = pd.to_datetime(df['data_inversa'], format='%d/%m/%Y')
df['mes_num'] = df['data_inversa'].dt.month

MESES_PT = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}

total = len(df)
print('Total de acidentes (2026, jan-mai):', total)
print('Total de obitos:', df['mortos'].sum())

# ---------- acidentes_mensal.csv ----------
por_mes = df.groupby('mes_num').size().reindex(range(1,13), fill_value=0)
with open('../dados/acidentes_mensal.csv', 'w', encoding='utf-8') as f:
    f.write('mes,acidentes\n')
    for m in range(1,13):
        if por_mes[m] > 0 or m <= df['mes_num'].max():
            f.write(f"{MESES_PT[m]}/26,{int(por_mes[m])}\n")

# ---------- acidentes_estado.csv ----------
por_uf = df['uf'].value_counts()
with open('../dados/acidentes_estado.csv', 'w', encoding='utf-8') as f:
    f.write('uf,acidentes\n')
    for uf, n in por_uf.items():
        f.write(f"{UF_NOME.get(uf, uf)},{n}\n")

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
df['hora'] = pd.to_datetime(df['horario'], format='%H:%M:%S').dt.hour
bins = [(0,3),(3,6),(6,9),(9,12),(12,15),(15,18),(18,21),(21,24)]
with open('../dados/faixa_horaria.csv', 'w', encoding='utf-8') as f:
    f.write('faixa,percentual\n')
    for a,b in bins:
        n = df[(df['hora']>=a) & (df['hora']<b)].shape[0]
        f.write(f"{a:02d}-{b:02d},{round(n/total*100,1)}\n")

# ---------- dia_semana.csv ----------
DIA_MAP = {
    'segunda-feira':'Seg','terça-feira':'Ter','quarta-feira':'Qua','quinta-feira':'Qui',
    'sexta-feira':'Sex','sábado':'Sáb','domingo':'Dom',
    'segunda':'Seg','terca':'Ter','quarta':'Qua','quinta':'Qui','sexta':'Sex','sabado':'Sáb'
}
ordem = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']
dia_norm = df['dia_semana'].str.lower().str.strip().map(lambda x: DIA_MAP.get(x, x[:3].capitalize()))
dia_counts = dia_norm.value_counts()
with open('../dados/dia_semana.csv', 'w', encoding='utf-8') as f:
    f.write('dia,percentual\n')
    for d in ordem:
        n = dia_counts.get(d, 0)
        f.write(f"{d},{round(n/total*100,1)}\n")

# ---------- municipios.csv ----------
mun = df.groupby(['municipio','uf']).size().sort_values(ascending=False).head(10)
with open('../dados/municipios.csv', 'w', encoding='utf-8') as f:
    f.write('municipio,uf,acidentes\n')
    for (m, uf), n in mun.items():
        f.write(f"{m.title()},{uf},{n}\n")

# ---------- rodovias.csv ----------
br = df.groupby('br').size().sort_values(ascending=False).head(10)
with open('../dados/rodovias.csv', 'w', encoding='utf-8') as f:
    f.write('rodovia,trecho,acidentes,percentual\n')
    for b, n in br.items():
        ufs = df[df['br']==b]['uf'].value_counts().head(3).index.tolist()
        trecho = 'Trechos em ' + '/'.join(ufs)
        f.write(f'BR-{int(b):03d},"{trecho}",{n},"{round(n/total*100,1)}%"\n')

print('Arquivos gerados em dados/.')
