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
        data.append(data_dict)

    df = pd.DataFrame(data)
    df['profit'] = df['sold'] - df['bougth']

    return df


data_load_state = st.text('Loading data...')
profit = load_df(response)
data_load_state.text("Done! Alex.")
st.markdown("""---""")
# profit = total(data)
loosing = profit[profit['profit'] < 0]
profit = profit[profit['profit'] > 0]


profit['profit'] = profit['profit'].apply(lambda x: round(x, 2))
loosing['profit'] = loosing['profit'].apply(lambda x: round(x, 2)*-1)

profit['method'] = profit['method'].apply(lambda x: 'CATEGORICAL' if x == 'deep_learning_forecast' else 'RNN')
loosing['method'] = loosing['method'].apply(lambda x: 'CATEGORICAL' if x == 'deep_learning_forecast' else 'RNN')

count_df = pd.DataFrame(profit['symbol'].value_counts())
count_df_loosing = pd.DataFrame(loosing['symbol'].value_counts())

count_df = count_df.reset_index()
count_df.columns = ['symbols', 'counts']

count_df_loosing = count_df_loosing.reset_index()
count_df_loosing.columns = ['symbols', 'counts']

greater_occurence = int(count_df['counts'][0])
n3 = (greater_occurence / 3)  # dividing between number of 3 to get top 3

greater_occurence_loosing = int(count_df_loosing['counts'][0])
n3_loosing = (greater_occurence_loosing/ 3)  # dividing between number of 3 to get top 3



def count_values(x, val, df):
    a = int(df.loc[df['symbols'] == x, 'counts'].iloc[0])
    val = round(val)
    if a > 2 * val:
        return f'TOP1>{2*val}'
    elif a < val:
        return f'TOP3<{val}'
    else:
        return f'{val}>TOP2<{2*val}'


profit['category'] = profit['symbol'].apply(lambda x: count_values(x, n3, count_df))
loosing['category'] = loosing['symbol'].apply(lambda x: count_values(x, n3_loosing, count_df_loosing))



best20 = px.treemap(profit[profit['profit'] != 0], path=[px.Constant('Profit'), 'category', 'method', 'symbol'],
                    values='profit', color='symbol',
                    hover_data=['profit'],
                    # color_continuous_midpoint=np.average(profit['profit'], weights=profit['profit']),
                    color_continuous_scale='RdBu',
                    title="<b>Profit By Times</b>",
                    )

best20.update_traces(marker=dict(cornerradius=5))
best20.update_coloraxes(colorbar={'orientation': 'h', 'thickness': 20, 'y': -0.2})


best20_l = px.treemap(loosing[loosing['profit'] != 0], path=[px.Constant('Loosing'), 'category', 'method', 'symbol'],
                    values='profit', color='symbol',
                    hover_data=['profit'],
                    # color_continuous_midpoint=np.average(profit['profit'], weights=profit['profit']),
                    color_continuous_scale='RdBu',
                    title="<b>Loosing By times</b>",
                    )

best20_l.update_traces(marker=dict(cornerradius=5))
best20_l.update_coloraxes(colorbar={'orientation': 'h', 'thickness': 20, 'y': -0.2})




st.plotly_chart(best20, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(best20_l, use_container_width=True)
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
