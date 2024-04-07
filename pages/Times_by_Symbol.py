import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px

import matplotlib.pyplot as plt

st.title("Best and Worst Criptos")
st.markdown("##")


db = boto3.resource('dynamodb', region_name = 'us-east-1' )

table_name = db.Table(name='app_bi_sell')
response  = table_name.scan()
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
    df['profit_'] = df['profit'].apply(lambda x: 0 if x > 0 else 1)
    return df



def Profit(df):
    date_quant = df.groupby(['symbol'])['profit'].agg('count').reset_index()
    date_quant = date_quant.sort_values("profit", ascending=False).reset_index(drop=True)
    return date_quant
    



data_load_state = st.text('Loading data...')
data = load_df(response)
positive = data[data['profit_'] == 0]
negative = data[data['profit_'] == 1]


data_load_state.text("Done! Alex.")



profit = Profit(positive)
st.markdown("""---""")

# SALES BY HOUR [BAR CHART]
profit_50 = profit[0:50]
profit_50_names = profit_50['symbol'].unique()

negative_50 = negative[negative['symbol'].isin(profit_50_names)]
negative_50 = Profit(negative_50)
# print(negative_50 , 'negative_50_names')

symbol = px.bar(
    profit[0:50],
    x='symbol',
    y="profit",
    color = "profit",
    # orientation="h",
    title="<b>Times by Symbol</b>",
    # color_discrete_sequence=["#0083B8"] * len(profit),
    template="plotly_dark",
)
symbol.update_layout(
    xaxis=dict(tickmode="linear"),
    # plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)

negative = px.bar(
    negative_50,
    x='symbol',
    y="profit",
    color = "profit",
    # orientation="h",
    title="<b>Times Negatives Symbol</b>",
    # color_discrete_sequence=["#0083B8"] * len(profit),
    template="plotly_dark",
)
negative.update_layout(
    xaxis=dict(tickmode="linear"),
    # plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)





st.plotly_chart(symbol, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(negative, use_container_width=True)
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