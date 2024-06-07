import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px
import random
import time
import matplotlib.pyplot as plt

st.title("From Cripto symbols to Hours")
st.markdown("##")

db = boto3.resource('dynamodb', region_name='us-east-1')
# tables = list(db.tables.all())
table_name = db.Table(name='app_bi_sell')
response = table_name.scan()
data = response['Items']

while 'LastEvaluatedKey' in response:
    response = table_name.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    data.extend(response['Items'])

response = data


@st.cache_data
def load_df(response):
    data = []
    for count, each in enumerate(response):
        data_dict = {}

        symbol = each['symbol']
        date = symbol.split('_')
        date_sold = datetime.datetime.utcfromtimestamp(float(date[-1])).strftime('%Y-%m-%d %H:%M:%S')
        each_sell = json.loads(each['item_sell'])
        each_bougth = json.loads(each['item_bougth'])

        data_dict['symbol'] = date[0]
        data_dict['sold'] = float(each_sell["cummulativeQuoteQty"])
        data_dict['method'] = each_bougth["method"]
        data_dict['date_sold'] = date_sold
        data_dict['bougth'] = float(each_bougth["money_spent"])

        data_dict['date_bougth'] = pd.Timestamp(f'20{each_bougth["time"][0]}').strftime('%Y-%m-%d %H:%M:%S')
        data.append(data_dict)

    df = pd.DataFrame(data)
    df['profit'] = df['sold'] - df['bougth']
    df['time_hold'] = pd.to_datetime(df['date_sold']) - pd.to_datetime(df['date_bougth'])
    df['time_hold'] = round(df['time_hold'].dt.seconds / 60, 2)
    df['profit_'] = df['profit'].apply(lambda x: 0 if x > 0 else 1)
    return df


def total(df):
    df['date'] = pd.to_datetime(df['date_sold'])
    df['dates'] = df['date'].dt.strftime('%Y-%m-%d')
    df['Sold'] = df['date'].dt.day_name()
    df['hour_sold'] = df['date'].dt.strftime('%H')
    return df


def total_bougth(df):
    df['date_bougth'] = pd.to_datetime(df['date_bougth'])
    df['dates_bougth'] = df['date_bougth'].dt.strftime('%Y-%m-%d')
    df['Bought'] = df['date_bougth'].dt.day_name()
    df['hour_bougth'] = df['date_bougth'].dt.strftime('%H')
    return df


def close(df):
    date_quant = df.groupby(['symbol', 'method', 'profit_', 'Bought', 'hour_bougth', 'Sold', 'hour_sold'])[
        'profit'].agg('count').reset_index()
    return date_quant


def Profit(df):
    date_quant = df.groupby(['symbol'])['profit'].agg('sum').reset_index()
    date_quant = date_quant.sort_values("profit", ascending=False).reset_index(drop=True)
    return date_quant


data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex.")

df = total(data)

df = total(data)
df = total_bougth(df)
datas = close(df)
profit = Profit(df)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")
symbol = st.sidebar.multiselect(
    "Select the Symbol:",
    options=df["symbol"].unique(),
    default=df["symbol"].unique()[0:30]
)

df_selection = datas.query(
    "symbol == @symbol"
)

# st.markdown("""---""")


# # SALES BY PRODUCT LINE [BAR CHART]
df_selection['Profit'] = df_selection['profit_'].apply(lambda x: 'Profit' if x == 0 else 'Loosing')
df_selection['method'] = df_selection['method'].apply(lambda x: 'CATEG' if x == 'deep_learning_forecast' else 'RNN')
sales_by_product_line = (
    df_selection
)

fig = px.parallel_categories(
    df_selection,
    dimensions=['symbol', 'Bought', 'hour_bougth', 'method', 'Sold', 'hour_sold', 'Profit'],
    color="profit_",
    # color_continuous_scale=px.colors.sequential.Inferno,
    template="plotly_dark",
    labels={'symbol': 'Cripto', 'method': 'Method', 'hour_sold': 'HS',
            'hour_bougth': 'HB', 'profit_': 'Profit'})

fig.update_coloraxes(colorbar={'orientation': 'h', 'thickness': 20, 'y': -0.2})
fig.update_layout(
    width=1000,
    height=800,
)
st.markdown("""---""")

st.plotly_chart(fig, use_container_width=True)
st.markdown("""---""")

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
