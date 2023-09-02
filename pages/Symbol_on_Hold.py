import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px
from datetime import datetime
import matplotlib.pyplot as plt

st.title("Best and Worst Criptos")
st.markdown("##")


db = boto3.resource('dynamodb', region_name = 'us-east-1' )
tables = list(db.tables.all())

table_name = db.Table(name='app_bi')
response  = table_name.scan()
response = response['Items']

@st.cache_data
def load_df(response):
    data = []
    for count, each in enumerate(response):

        data_dict = {}

        symbol = each['symbol']
        each = json.loads(each['item'])
        quantity_to_sell = each["quantity_to_sell"]
        price = each['price'][-1]
        method = each["method"]
        money_spent = each["money_spent"]
        
        
        data_dict['symbol'] = symbol
        data_dict['quantity'] = float(quantity_to_sell)
        data_dict['current_price'] = float(price)
        data_dict['method'] = method
        time = each['time'][0].split(' ')[0]+' '+each['time'][0].split(' ')[2]
        data_dict['date_bougth'] = pd.to_datetime(time,  yearfirst=True)
        data_dict['money_spent'] = float(money_spent)

        now = datetime.now()
        data_dict['date'] = now.strftime("%Y-%m-%d %H:%M:%S")
        data_dict['time_hold'] = round((pd.to_datetime(data_dict['date']) - pd.to_datetime(data_dict['date_bougth']))/ np.timedelta64(1, 'h'), 2)
        data.append(data_dict)
        

    df = pd.DataFrame(data)
    
    return df


# def total(df):
#     df['date'] = pd.to_datetime(df['date_sold'])
#     df['dates'] = df['date'].dt.strftime('%Y-%m-%d')
#     df['Day_of_week'] = df['date'].dt.day_name()
#     df['hour'] = df['date'].dt.strftime('%H')
#     return df

data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex.")


best20 = px.bar(data, x="symbol", y="time_hold", 
                pattern_shape="quantity", 
                pattern_shape_sequence=['/', '\\', 'x', '-', '|', '+', '.'],
                title="<b>Tiempo Hold per Symbol</b>",
                color_discrete_sequence=["#CC6600"] * len(data['symbol']),
                template="plotly_dark",
                )


best20.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)

best20.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
best20.update_yaxes(showticklabels=True)






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