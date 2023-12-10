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
    df['time_hold'] = pd.to_datetime(df['date_sold']) - pd.to_datetime(df['date_bougth'])
    df['time_hold'] = round(df['time_hold'].dt.seconds / 60, 2)
    df['profit_'] = df['profit'].apply(lambda x: 0 if x > 0 else 1)
    return df


def total(df):
    df['date'] = pd.to_datetime(df['date_sold'])
    df['dates'] = df['date'].dt.strftime('%Y-%m-%d')
    df['Day_of_week'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.strftime('%H')
    return df


def Profit(df):
    date_quant = df.groupby(['symbol'])['profit'].agg('sum').reset_index()
    # date_quant = date_quant.sort_values("profit", ascending=False).reset_index(drop=True)
    return date_quant
    



data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex.")

df = total(data)


profit = Profit(df)
# print(profit, "the profit")
st.markdown("""---""")
left_column, middle_column = st.columns(2)
positive = profit[profit['profit'] >= 0]
negative = profit[profit['profit'] < 0]

earning = round(positive['profit'].sum(), 2)
loosing = round(negative['profit'].sum(), 2)

with left_column:
    # st.text('___'*10)
    st.subheader("Total Earning:")
    st.subheader(f"Total: {earning}")
    
    
with middle_column:
    # st.text('___'*10)
    st.subheader("Total Loosing:")
    st.subheader(f"{loosing}")

    
    
    
st.markdown("""---""")


# SALES BY HOUR [BAR CHART]

best20 = px.pie(positive, 
                          values='profit',
                          names='symbol', 
                          title='Profitable symbols')

val = negative['profit']*-1
negative.loc[:, ('profit')] = val
# negative['profit'] = val
worst20 = px.pie(negative, 
                          values='profit',
                          names='symbol', 
                          title='Loosing Symbols')


st.plotly_chart(best20, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(worst20, use_container_width=True)
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