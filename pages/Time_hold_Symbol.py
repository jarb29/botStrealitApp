import streamlit as st
import pandas as pd
import seaborn as sns
import boto3
import json
import datetime

import matplotlib.pyplot as plt

st.title('Time Hold per Symbol')





db = boto3.resource('dynamodb', region_name = 'us-east-1' )
# tables = list(db.tables.all())
table_name = db.Table(name='app_bi_sell')
response  = table_name.scan()
response = response['Items']



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
data_load_state.text("Done! Alex")


df = total(data)
df['category'] = df['symbol'].apply(lambda x: 'BUSD' if x[-4:] == 'BUSD' else 'USDT')


#  USDT and binance
USDT_and_binace  = df[(df['method'] == 'deep_learning_binance') & (df['category']=='USDT')] 

#  USDT and series
USDT_and_series  = df[(df['method'] == 'deep_learning_forecast') & (df['category']=='USDT')] 




sns.set_style("dark")
st.markdown("""---""")
st.text("USDT and RNN")
chart2 = sns.catplot(data=USDT_and_binace, x="time_hold", y="symbol", kind="violin", color=".9", inner=None, height=8, aspect=1)
chart2 = sns.swarmplot(data=USDT_and_binace, x="time_hold", y="symbol", orient="h", size=1)
# Display the plot in Streamlit
st.pyplot(chart2.get_figure())




st.markdown("""---""")
st.text("USDT and CATEGORICAL")
chart3 = sns.catplot(data=USDT_and_series, x="time_hold", y="symbol", kind="violin", color=".9", inner=None, height=15, aspect=0.5)
chart3 = sns.swarmplot(data=USDT_and_series, x="time_hold", y="symbol", orient="h", size=1)
# Display the plot in Streamlit
st.pyplot(chart3.get_figure())
st.markdown("""---""")


