import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px

import numpy as np

import matplotlib.pyplot as plt

st.title("Sunburst Profit")
st.markdown("##")


db = boto3.resource('dynamodb', region_name = 'us-east-1' )
# tables = list(db.tables.all())
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
    df['time_hold'] = pd.to_datetime(df['date_sold']) - pd.to_datetime(df['date_bougth'])
    df['time_hold'] = round(df['time_hold'].dt.seconds / 60, 2)
    df['profit_'] = df['profit'].apply(lambda x: 0 if x > 0 else 1)
    return df


def total(df):
    df['date'] = pd.to_datetime(df['date_sold'])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    return df


data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex.")

df = total(data)


df_sunburst = df.groupby(['method', 'symbol'])['profit'].agg('sum').reset_index()
df_sunburst['method'] = df_sunburst['method'].apply(lambda x: 'CATEG' if x == 'deep_learning_forecast' else 'RNN')
df_sunburst['profit_'] = df_sunburst['profit'].apply(lambda x: 'Profit' if x > 0 else 'Loosing')
df_sunburst['profit'] = df_sunburst['profit'].apply(lambda x: round(x, 2))

df_sunburstII = df.groupby(['method', 'profit_'])['profit'].agg('sum').reset_index()
df_sunburstII['profit_'] = df_sunburstII['profit'].apply(lambda x: 'Profit' if x > 0 else 'Loosing')
df_sunburstII['total_profit'] = df_sunburstII['profit'].apply(lambda x: round(x, 2))
df_sunburstII = df_sunburstII.drop(['profit'], axis=1)
df_sunburstII['method'] = df_sunburstII['method'].apply(lambda x: 'CATEG' if x == 'deep_learning_forecast' else 'RNN')
df_sunburst = df_sunburst.merge(df_sunburstII, left_on=['method', 'profit_'], right_on=['method', 'profit_'])

df_sunburst['profit_'] = df_sunburst.apply(lambda x: f'{x.profit_}: {x.total_profit}$', axis=1)

fig = px.sunburst(df_sunburst, path=['method', 'profit_', 'symbol', 'profit'], color = 'profit',
                  hover_data=['profit'],
                #   color_continuous_scale=["red", "orange", 'yellow', "blue"],
                  template="plotly_white",
                  title="<b>Profit Sum by Method</b>",
                  color_continuous_scale=px.colors.sequential.RdBu,
                #   color_continuous_midpoint=np.average(df['profit'], weights=df['profit'])
                 
                 )
fig.update_coloraxes(colorbar={'orientation':'h', 'thickness':10, 'y': -0.3})
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