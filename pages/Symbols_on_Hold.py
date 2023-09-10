import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import time
import datetime
import plotly.express as px
from datetime import datetime

st.title("Symbols That Hasn't Been Sold")
st.markdown("##")


db = boto3.resource('dynamodb', region_name = 'us-east-1' )
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


        
        data.append(data_dict)
    df = pd.DataFrame(data)
    
    return df

with st.status("Downloading data...", expanded=True) as status:
    st.write("Searching for data...")
    data = load_df(response)
    time.sleep(2)
    st.write("Found URL.")
    time.sleep(1)
    st.write("Downloading data...")
    time.sleep(1)
    status.update(label="Download complete!", state="complete", expanded=False)
st.button('Rerun')




now = datetime.now()
t1  = pd.to_datetime(now.strftime("%Y-%m-%d %H:%M:%S"))
    

data['time_hold'] = data['date_bougth'].apply(lambda x: (t1-x).total_seconds()/60)  
        
st.markdown("""---""")
if len(data) >0:
    best20 = px.bar(data, y="symbol", x="time_hold", 
                    pattern_shape="quantity", 
                    color = 'time_hold',
                    pattern_shape_sequence=['/', '\\', 'x', '-', '|', '+', '.'],
                    title="<b>Time on Hold per Symbol in minutes</b>",
                    template="plotly_dark",
                    )


    best20.update_layout(
        xaxis=(dict(showgrid=True)),
        yaxis=(dict(showgrid=True)),
    )
    best20.update_coloraxes(colorbar={'orientation':'h', 'thickness':20, 'y': -1.0})

    best20.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    best20.update_yaxes(showticklabels=True)

    st.plotly_chart(best20, use_container_width=True)
else:
    st.write("There is none symbols on HOLD...")
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
