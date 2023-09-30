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
        data.append(data_dict)

    df = pd.DataFrame(data)
    df['profit'] = df['sold'] - df['bougth']
    
    return df



data_load_state = st.text('Loading data...')
profit = load_df(response)
data_load_state.text("Done! Alex.")
st.markdown("""---""")
# profit = total(data)

profit['profit'] = profit['profit'].apply(lambda x: round(x,2) if x > 0 else 0.001)
profit['category'] = profit['symbol'].apply(lambda x: 'BUSD' if x[-4:] == 'BUSD' else 'USDT')
profit['method'] = profit['method'].apply(lambda x: 'CATEGORICAL' if x == 'deep_learning_forecast' else 'RNN')

best20 = px.treemap(profit[profit['profit']!=0], path=['category', 'method', 'symbol'],
                    values='profit', color='profit', 
                    hover_data=['profit'],
                    color_continuous_midpoint=np.average(profit['profit'], weights=profit['profit']),
                    color_continuous_scale='RdBu'           
                    )

best20.update_traces(marker=dict(cornerradius=5))
best20.update_coloraxes(colorbar={'orientation':'h', 'thickness':20, 'y': -0.2})




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
