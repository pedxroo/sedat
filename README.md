## Publicação (GitHub + Vercel) e modo admin

Os botões que atualizam os dados exibidos — **"Selecionar pasta de dados"**,
**"↻ Recarregar de /dados"** e os ícones **⟳** de cada aba — ficam **ocultos para
qualquer visitante público**. Eles só aparecem depois de entrar no **modo admin**,
pelo link discreto **"Modo admin"** no rodapé da barra lateral.

A senha do modo admin **não fica no código do site**. Ela é conferida por uma função
serverless (`api/admin-login.js`) contra a variável de ambiente `ADMIN_PASSWORD`
cadastrada no projeto da Vercel. Para configurar:

1. Suba o repositório no GitHub e importe-o na Vercel.
2. No projeto da Vercel, vá em **Settings → Environment Variables** e crie
   `ADMIN_PASSWORD` com a senha desejada (marque Production e Preview).
3. Faça um novo deploy (ou "Redeploy") para a variável entrar em vigor.
4. No site publicado, clique em **"Modo admin"** no rodapé da barra lateral e
   digite a senha — os botões de atualização aparecem e ficam lembrados nesse
   navegador (para sair, clique em "Sair do modo admin").

Como esse login roda numa função serverless, ele **não funciona** ao abrir o
`index.html` localmente ou pelo `iniciar_dashboard.bat` (servidor estático simples,
sem `/api`) — nesses casos os botões continuam ocultos por padrão, o que não é um
problema já que quem roda localmente já tem acesso direto aos arquivos em `dados/`.

# SEDAT-SUS — Dashboard Inteligente de Trânsito e Saúde

Dashboard estático em HTML/CSS/JS baseado no protótipo do Sprint 1 (grupo Dummys / FIAP).
Os dados são carregados de arquivos **CSV ou XLSX** dentro da pasta `dados/` — não é
necessário editar o HTML para atualizar os números.

As bibliotecas JS (Chart.js, PapaParse, SheetJS) ficam vendorizadas em `lib/` em vez de
carregadas de CDN, para o dashboard funcionar mesmo sem internet (inclusive no modo
`file://`, opção B abaixo).

## Como atualizar os dados

1. Exporte um relatório de um dos sites públicos (veja lista abaixo) em **CSV ou XLSX**.
2. Renomeie/organize o arquivo para bater com um dos nomes esperados na pasta `dados/`
   (veja a tabela de schemas abaixo — o nome do arquivo importa, o cabeçalho das colunas também).
3. Salve o arquivo dentro da pasta `dados/`, substituindo o modelo existente.
4. Abra o dashboard de uma destas duas formas:
   - **Opção A (recomendada): clique duas vezes em `iniciar_dashboard.bat`.**
     Isso sobe um servidor local e abre o navegador — os arquivos de `dados/` são
     carregados automaticamente toda vez que a página é aberta ou recarregada (F5).
   - **Opção B: abra `index.html` direto (duplo clique).**
     Nesse modo o navegador bloqueia a leitura automática da pasta (restrição de
     segurança do `file://`). Use o botão **"Selecionar pasta de dados"** no menu
     lateral do dashboard e escolha a pasta `dados/` manualmente — os arquivos são
     lidos na hora, sem precisar de servidor.

Se um arquivo não existir ou tiver nome/colunas diferentes do esperado, o dashboard
simplesmente ignora aquele gráfico e mantém o dado de exemplo — nunca quebra a página.

## Onde encontrar os dados reais (fontes públicas oficiais)

Estas são as mesmas fontes citadas na proposta do projeto (slide "Fontes de Dados"):

| Fonte | O que baixar | Onde |
|---|---|---|
| **DATASUS / TabNet — SIH** | Internações hospitalares (proxy de leitos ocupados), por causas externas / acidentes de transporte | tabnet.datasus.gov.br → "Assistência à Saúde" → SIH |
| **DATASUS / TabNet — SIM** | Óbitos por acidentes de trânsito (mortalidade) | tabnet.datasus.gov.br → "Estatísticas Vitais" → SIM |
| **PRF — Dados Abertos** | Acidentes registrados em rodovias federais, por BR/trecho/tipo/horário/dia da semana | gov.br/prf → "Acesso à Informação" → "Dados Abertos" (arquivos anuais em CSV) |
| **SENATRAN/DENATRAN** | Frota de veículos por UF/município | gov.br/transportes → "Frota de Veículos" |
| **IBGE / SIDRA** | População por UF/município (para taxas per capita) | sidra.ibge.gov.br |
| **INMET** | Dados climáticos históricos (variável usada no modelo preditivo) | portal.inmet.gov.br/dadoshistoricos |
| **Portal Brasileiro de Dados Abertos** | Bases agregadas de SAMU/saúde/trânsito de vários órgãos | dados.gov.br |

Esses portais normalmente exportam em CSV ou permitem baixar planilhas em Excel — em
ambos os casos o dashboard consegue ler.

## Atualizando com os dados mais recentes da PRF

A PRF atualiza o arquivo do ano corrente mensalmente em
gov.br/prf → "Acesso à Informação" → "Dados Abertos" → seção **BAT: Boletim de
Acidente de Trânsito** → "Documento CSV de Acidentes {ano} (Agrupados por ocorrência)".
Para atualizar:

1. Baixe o zip do ano corrente nessa página e extraia o `.csv`.
2. Substitua `dados_reais/datatran2026/datatran2026.csv` (ajuste o nome da pasta se já
   estiver em outro ano) pelo arquivo novo.
3. Rode `python processar_completo.py` dentro de `dados_reais/` de novo.

O script detecta sozinho os meses mais recentes e corta automaticamente qualquer mês
cujo volume caia abaixo de 60% da média dos 3 meses anteriores — isso é sinal de que o
mês ainda está sendo preenchido pela PRF (os boletins de acidente continuam chegando
por semanas depois do fato), não uma queda real. Sem esse corte, um mês parcial (às
vezes com menos de 5% do volume normal) entraria nos KPIs e no modelo de previsão como
se fosse uma queda real de acidentes — o script avisa no terminal qual mês cortou e por
quê. Essa lógica atualiza sozinha o footer "Dados atualizados até..." do dashboard e o
rótulo de período no topo — nada precisa ser editado manualmente no `index.html`.

## Arquivos esperados em `dados/`

| Arquivo | Usado em | Colunas (cabeçalho exato) |
|---|---|---|
| `acidentes_mensal.csv` | Overview → Evolução dos Acidentes | `mes, acidentes` |
| `acidentes_estado.csv` | Overview + Geográfico → Ranking/Mapa por Estado | `uf, acidentes` |
| `tipos_acidente.csv` | Overview → Tipos de Acidente (donut) | `tipo, percentual` |
| `faixa_horaria.csv` | Overview + Geográfico → Faixa Horária | `faixa, percentual` |
| `dia_semana.csv` | Geográfico → Acidentes por Dia da Semana | `dia, percentual` |
| `municipios.csv` | Geográfico → Top Municípios | `municipio, uf, acidentes` |
| `rodovias.csv` | Geográfico → Distribuição por Rodovia | `rodovia, trecho, acidentes, percentual` |
| `previsao_mensal.csv` | Previsões → Real vs Previsto (linha) | `mes, real, previsto` (deixe vazio o que não se aplica) |
| `previsao_semestre.csv` | Previsões → Previsão por Mês (barras) | `mes, previsto` |
| `fatores_impacto.csv` | Previsões → Fatores que mais impactam | `fator, importancia` (0 a 1) |
| `kpis.csv` | Overview → cartões de indicadores | `indicador, valor, variacao, tendencia` (`tendencia` = `up` ou `down`; indicadores esperados: `Acidentes`, `Leitos Ocupados`, `Acidentes com Vítimas`, `Atendimentos`, `Óbitos`) |
| `kpis_previsao.csv` | Previsões → cartões de indicadores previstos | `indicador, valor, variacao` (indicadores esperados: `Leitos`, `Acidentes`, `Atendimentos`, `Óbitos`) |
| `comparacao_real_previsto.csv` | Previsões → tabela comparativa | `recurso, icone, real, previsto, variacao` |
| `clima_mensal_2025.csv` | Previsões → gráfico de Clima (fator do modelo) | `mes, temperatura_media_c, precipitacao_media_mm` |
| `populacao_uf.csv` | Geográfico → coluna "/100k hab." no ranking | `uf, populacao, ano` |
| `causas_acidente.csv` | Análises → Principais Causas | `causa, percentual` |
| `condicao_metereologica.csv` | Análises → Condição Meteorológica | `condicao, percentual` |
| `gravidade_acidente.csv` | Análises → Gravidade dos Acidentes (donut) | `classificacao, percentual` |
| `mortos_feridos_mensal.csv` | Análises → Evolução de Mortos e Feridos Graves | `mes, mortos, feridos_graves, feridos_leves` |
| `kpis_analises.csv` | Análises → cartões de indicadores | `indicador, valor` (indicadores esperados: `Taxa de Letalidade`, `Pct Acidentes Fatais`, `Media Pessoas por Acidente`, `Media Veiculos por Acidente`) |
| `recursos_estado.csv` | Recursos → ranking e gráfico por estado | `uf, leitos_estim, atendimentos_estim, obitos` |
| `acidentes_mensal_estado.csv` | Overview → filtro de Estado no gráfico Evolução | `uf, mes, acidentes` |
| `acidentes_estado_tipo.csv` | Geográfico → filtro de Tipo de Acidente | `uf, tipo, acidentes` |
| `municipios_estado.csv` | Geográfico → filtro de Município em cascata (Top 15 por UF) | `uf, municipio, acidentes` |
| `serie_mensal_estado.csv` | Previsões → filtro de Estado (histórico real por UF) | `uf, mes, acidentes, leitos_estim, atendimentos_estim, obitos` |
| `previsao_mensal_estado.csv` | Previsões → filtro de Estado (previsão por UF, 6 meses) | `uf, mes, previsto_acidentes, previsto_leitos, previsto_atendimentos, previsto_obitos` |
| `kpis_previsao_estado.csv` | Previsões → filtro de Estado (KPIs por UF) | `uf, acidentes_valor, acidentes_variacao, leitos_valor, leitos_variacao, atendimentos_valor, atendimentos_variacao, obitos_valor, obitos_variacao` |

Números podem usar tanto `1234.5` quanto `1.234,5` (formato brasileiro) — o dashboard
converte automaticamente. Percentuais podem ser escritos como `45.6` ou `45,6%`.

## Pipeline de dados reais (`dados_reais/processar_completo.py`)

Os CSVs em `dados/` hoje são gerados a partir de dados reais da PRF (`datatran2025.csv` +
`dados_reais/datatran2026/datatran2026.csv`) por `dados_reais/processar_completo.py`.
Para regenerar tudo depois de baixar um novo mês de dados da PRF:

```bash
cd dados_reais
python processar_completo.py
```

O script:
- combina os dois arquivos da PRF numa série mensal real (o número de meses cresce a
  cada atualização — ver "Atualizando com os dados mais recentes" acima);
- corta automaticamente do fim da série qualquer mês com volume muito abaixo da
  tendência recente (< 60% da média dos 3 meses anteriores), porque isso normalmente é
  o boletim de acidente ainda sendo preenchido pela PRF, não uma queda real;
- calcula os KPIs do Overview comparando o ano corrente com o anterior, no mesmo
  recorte de meses (ex.: Jan-Jun/2026 vs Jan-Jun/2025 — esse recorte se ajusta sozinho
  ao mês mais recente disponível; não é mais "vs. 2023" fixo como no protótipo
  original);
- treina uma regressão linear múltipla (`numpy.linalg.lstsq`, sem dependências de ML)
  sobre a série real (variáveis: tendência temporal, temperatura média, precipitação
  média) para prever os 6 meses seguintes. O clima dos meses futuros assume o mesmo
  padrão sazonal observado em `clima_mensal_2025.csv`.
- `dados_reais/processar.py` (script antigo, só processava `datatran2026` e não gerava
  KPIs/previsões reais) foi mantido no repositório por enquanto, mas está obsoleto —
  use `processar_completo.py`.

### Metodologia dos indicadores (e uma limitação conhecida)

- **Leitos Ocupados (estim.)**: não é o número oficial de leitos do SIH/SUS. É uma
  estimativa baseada na soma de `feridos_graves` (feridos graves em acidentes de
  trânsito) reportados pela PRF — feridos graves são o proxy mais direto de demanda por
  internação que temos nos dados abertos disponíveis.
- **Acidentes com Vítimas** (substituiu "Ambulâncias Ativas" do protótipo original):
  contagem de acidentes classificados pela PRF como "Com Vítimas Feridas" ou "Com
  Vítimas Fatais". Não existe fonte pública de frota de ambulâncias ativas nos dados
  coletados — o card antigo mostrava um número de exemplo fixo, então foi substituído
  por uma métrica real.
- **Por que não usamos o SIH filtrado por causa (acidentes de transporte)?** O SIH/SUS
  do DATASUS tem um relatório específico para isso — TabNet → "Morbidade Hospitalar do
  SUS por local de internação" → filtro **Lista Morb CID-10 = "Acidentes de
  transporte"** (é diferente do relatório "Procedimentos hospitalares" usado
  originalmente em `dados_reais/sih_uf_2025.txt`/`sih_uf_2026.txt`, que traz o total de
  internações por **todas as causas**, não só trânsito — foi esse mismatch que causava o
  valor absurdo de ~6 milhões no KPI "Leitos Ocupados" antes desta correção). Tentamos
  automatizar essa consulta filtrada e o formulário (`tabcgi.exe`) rejeita a submissão
  fora do navegador interativo (parece exigir o encoding ISO-8859-1 exato dos nomes de
  campo do formulário, que não conseguimos reproduzir de forma confiável via
  requisição HTTP direta). Quem quiser esse número oficial no futuro:
  1. Acesse `tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/niuf.def`;
  2. Em "Linha", selecione "Unidade da Federação";
  3. Em "Seleções disponíveis" → "Lista Morb CID-10", clique `[+]`, busque
     "acidentes de transporte" e selecione o item (deixa "Todas as categorias"
     desmarcado);
  4. Em "Períodos disponíveis", selecione os meses desejados;
  5. Clique "Mostra" e exporte como "Colunas separadas por ';'".
- **Fatores que mais impactam a demanda**: pesos derivados dos coeficientes
  padronizados da regressão linear (tendência, temperatura, precipitação) + duas
  medidas descritivas de concentração (tipo de acidente e faixa horária mais frequentes)
  — não é um modelo de árvore/feature-importance de verdade, é só uma leitura direta dos
  coeficientes ajustados.

## Observações

- O "mapa do Brasil" (Overview e Geográfico) usa o contorno real de cada Estado — mapa
  de [MapSVG](https://mapsvg.com/maps/brazil) via
  [@svg-maps/brazil](https://github.com/VictorCazanave/svg-maps), licença Creative
  Commons Attribution 4.0 (CC BY 4.0), colorido por Estado (coroplético) conforme o
  filtro ativo. Não há traçado de rodovias federais nos dados coletados, por isso essa
  camada continua desabilitada.
- Todas as abas estão funcionais agora:
  - **Análises**: causas do acidente, gravidade, condição meteorológica, evolução
    mensal de óbitos/feridos graves — dados reais.
  - **Recursos**: leitos/atendimentos estimados por estado, ranking e per capita —
    mostra só o lado da demanda (não há fonte pública de capacidade instalada/CNES
    nos dados coletados; isso está avisado na própria aba).
  - **Select IA**: cartões de insight gerados a partir dos dados carregados +
    caixa de pergunta com um motor de regras simples (busca por palavras-chave sobre
    os dados, sem chamada de API nem modelo de linguagem — isso está avisado na
    própria aba, para não passar a impressão de IA generativa real).
  - **Exportação**: botão por dataset para baixar o CSV exatamente como está
    carregado no momento (usa `Papa.unparse`, tudo client-side) e um botão de
    relatório resumido que abre a caixa de impressão do navegador (pode salvar como
    PDF por ali).
### O que funciona e o que é decorativo (levantamento completo)

Funcionais:
- Filtro de Estado no gráfico "Evolução dos Acidentes" (Overview) — usa
  `acidentes_mensal_estado.csv`.
- Filtro de Estado, Tipo de Acidente (17 tipos reais) e Município (em cascata: a lista
  de municípios muda conforme o Estado escolhido) no ranking/tabelas da aba Geográfico
  — usam `acidentes_estado_tipo.csv` e `municipios_estado.csv`.
- Filtro de Estado na aba Previsões — treina uma regressão linear própria por UF (mesma
  metodologia do modelo nacional, só que ajustada nos dados daquele estado) e atualiza
  os 4 KPIs, o gráfico Real vs. Previsto, o gráfico do semestre e a tabela de
  comparação. Usa `serie_mensal_estado.csv`, `previsao_mensal_estado.csv` e
  `kpis_previsao_estado.csv`.
- "Ver todos os estados" (Overview e Geográfico) — expande de Top 10 para os 27.
- "Ver mais municípios (30)" e "Ver mais rodovias (20)" — as bases nacionais de
  município/rodovia foram ampliadas de Top 10 para Top 30/20.
- Camada do mapa (Densidade de Acidentes / Óbitos) e Tipo de Mapa (Calor / Pontos) na
  aba Geográfico, e o zoom (+/−) do mapa.
- Botões ⟳ de recarregar dados em Geográfico, Previsões, Análises e Recursos.
- "Ver mais insights no Select IA →" e "📄 Gerar relatório completo" — navegam para as
  abas correspondentes.
- Botão de ajuda ("?") no Overview.
- Tudo na aba Select IA e na aba Exportação (ver seções acima).

Corrigido nesta rodada: o card "Previsão de Leitos Ocupados" (Overview→Previsões)
estava com o título errado — o gráfico sempre mostrou a série de **acidentes**
(real vs. previsto), não de leitos (isso já era coberto pelo card ao lado,
"Previsão por Mês — Próximo Semestre (Leitos)"). Renomeado para "Previsão de
Acidentes", que é o que ele de fato mostra.

Intencionalmente decorativos/desabilitados (com tooltip explicando o motivo ao passar
o mouse, para não parecer quebrado) — não há dado nenhum que suporte essas opções,
nem com reestruturação:
- Camadas "Leitos Disponíveis" e "Unidades de Saúde" no mapa — sem fonte pública
  correspondente nos dados coletados (exigiria CNES; ver "Metodologia dos indicadores"
  acima).
- Camada "Rodovias Federais" no mapa — o mapa é esquemático (bolhas por estado), não
  tem como sobrepor o traçado real de uma rodovia.
- "Ver detalhes" (Tipos de Acidente) / "Ver mais análises" (Faixa Horária) / "Ver
  previsão detalhada por recurso" — esses três não tinham view de detalhe nenhuma
  desenhada no protótipo original; deixados desabilitados em vez de simulados.
- Painel "🔍 Filtros" (Overview) e o sino de notificações — não implementados.
