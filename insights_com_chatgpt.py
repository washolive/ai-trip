"""
Insights sobre dados de custeio administrativo da administração pública
federal usando dashboard Streamlit, gráficos Plotly e ChatGPT.
As despesas constituem a base para a prestação de serviços públicos e
compreendem gastos correntes relativos a apoio administrativo,
energia elétrica, água, telefone, locação de imóveis, entre outros.

Requisitos:
    - python 3.7.1+
    - openai 0.27.0+
    - Variável OPENAI_API_KEY (API Key do ChatGPT) setada no ambiente.

Para executar:
    > streamlit run insights_com_chatgpt.py

Referência: https://youtu.be/6dsUQfsovCw
"""

import os
import locale
from urllib.request import urlopen, quote
from zipfile import ZipFile
from io import BytesIO
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import openai

locale.setlocale(locale.LC_ALL, 'pt_BR')

openai.api_key = os.environ.get("OPENAI_API_KEY")

REPO_URL = "https://repositorio.dados.gov.br/seges/raio-x/"
FILE_PREFIX = "raiox-2021"
CSV_FILE = "custeio-administrativo.csv"

df_list = []
for ref in range(12):
    file_name = f"{FILE_PREFIX}-{(ref + 1):02d}.zip"
    file_url = REPO_URL + quote(file_name) # file_name
    url = urlopen(file_url)
    file = ZipFile(BytesIO(url.read()))
    df = pd.read_csv(file.open(CSV_FILE))
    df_list.append(df)

df = pd.concat(df_list, axis=0, ignore_index=True)

df["ano_mes_referencia"] = df["ano_mes_referencia"].apply(str)
df = df[["ano_mes_referencia", "orgao_superior_nome", "orgao_superior_sigla",
         "orgao_nome", "orgao_sigla", "nome_item",
         "nome_natureza_despesa_detalhada", "valor"]]
df.rename({"nome_item": "item_despesa",
           "nome_natureza_despesa_detalhada": "natureza_despesa"},
           axis=1, inplace=True)

# Dashboard

st.title("Custeio Administrativo")
st.markdown("""Despesas necessárias para o funcionamento da administração
            pública federal.""")

# Filtros

SELECT_ALL = "<Todos>"

orgao_sup_list = pd.unique(df["orgao_superior_nome"]).tolist()
orgao_sup_list.append(SELECT_ALL)
filtro1 = st.selectbox("Órgão Superior", sorted(orgao_sup_list))
if filtro1 != SELECT_ALL:
    df = df[df["orgao_superior_nome"] == filtro1]

orgao_list = pd.unique(df["orgao_nome"]).tolist()
orgao_list.append(SELECT_ALL)
filtro2 = st.selectbox("Órgão", sorted(orgao_list))
if filtro2 != SELECT_ALL:
    df = df[df["orgao_nome"] == filtro2]

item_desp_list = pd.unique(df["item_despesa"]).tolist()
item_desp_list.append(SELECT_ALL)
filtro3 = st.selectbox("Item de despesa", sorted(item_desp_list))
if filtro3 != SELECT_ALL:
    df = df[df["item_despesa"] == filtro3]

# Indicadores e gráficos

ind1, ind2 = st.columns(2)
valor = locale.currency(df["valor"].min(), grouping=True)
ind1.metric(label="Mínimo", value=valor)
valor = locale.currency(df["valor"].max(), grouping=True)
ind2.metric(label="Máximo", value=valor)

ind3, ind4 = st.columns(2)
valor = locale.currency(df["valor"].mean(), grouping=True)
ind3.metric(label="Média", value=valor)
valor = locale.currency(df["valor"].sum(), grouping=True)
ind4.metric(label="Soma", value=valor)

st.markdown("### Série temporal")
fig = px.bar(data_frame=df, y="valor", x="ano_mes_referencia")
fig.update_layout(xaxis_type='category')
st.write(fig)

st.markdown("### Dados detalhados")
st.dataframe(df)

# Insights

st.markdown("### Insights do ChatGPT")

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user",
            "content": f"""O dataset a seguir contém dados do
            custeio administrativo da administração pública federal.
            Me informe 10 insights sobre este dataset: {df}"""
        },
    ]
)
st.markdown(completion.choices[0].message.content)

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        # {"role": "assistant",
        # "content": "Você é o responsável pela gestão pública do governo"},
        {"role": "user",
        "content": f"""Me explique o porquê dos valores negativos.
        Quais depesas possuem mais valores negativos neste dataset? {df}"""
        },
]
)
st.markdown(completion.choices[0].message.content)
