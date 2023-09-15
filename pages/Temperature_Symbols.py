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


        # data_dict['date_bougth'] = pd.Timestamp(f'20{each_bougth["time"][0]}').strftime('%Y-%m-%d %H:%M:%S')
        data.append(data_dict)

    df = pd.DataFrame(data)
    df['profit'] = df['sold'] - df['bougth']
    # df['time_hold'] = pd.to_datetime(df['date_sold']) - pd.to_datetime(df['date_bougth'])
    # df['time_hold'] = round(df['time_hold'].dt.seconds / 60, 2)
    # df['profit_'] = df['profit'].apply(lambda x: 0 if x > 0 else 1)
    
    return df


# def total(df):
#     df['date'] = pd.to_datetime(df['date_sold'])
#     df['dates'] = df['date'].dt.strftime('%Y-%m-%d')
#     df['Day_of_week'] = df['date'].dt.day_name()
#     df['hour'] = df['date'].dt.strftime('%H')
#     return df

data_load_state = st.text('Loading data...')
profit = load_df(response)
data_load_state.text("Done! Alex.")
st.markdown("""---""")
# profit = total(data)

profit['profit'] = profit['profit'].apply(lambda x: round(x,2) if x >= 0 else 0.001)
profit['category'] = profit['symbol'].apply(lambda x: 'BUSD' if x[-4:] == 'BUSD' else 'USDT')
profit['method'] = profit['method'].apply(lambda x: 'Series' if x == 'deep_learning_forecast' else 'RNN')

# print(profit[profit['symbol'] == 'ALGOBUSD'])
# money = sum(profit[profit['symbol'] == 'ALGOBUSD']['sum_profit'])
best20 = px.treemap(profit, path=[px.Constant('category'), 'category', 'method', 'symbol'],
                    values='profit', color='profit', 
                    hover_data=['profit'],
                    color_continuous_midpoint=np.average(profit['profit'], weights=profit['profit']),
                    color_continuous_scale='RdBu'           
                    )

# best20.update_layout(
#     xaxis=dict(tickmode="linear"),
#     plot_bgcolor="rgba(154, 167, 199, 0.09)",
#     yaxis=(dict(showgrid=True))
# )
best20.update_traces(marker=dict(cornerradius=5))
best20.update_coloraxes(colorbar={'orientation':'h', 'thickness':20, 'y': -0.2})

# best20.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
# best20.update_yaxes(showticklabels=True)






st.plotly_chart(best20, use_container_width=True)
st.markdown("""---""")
# st.plotly_chart(worst20, use_container_width=True)



# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# function to conect to s3
