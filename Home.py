import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px
import datetime
pd.set_option('mode.chained_assignment', None)
import matplotlib.pyplot as plt

st.title(":bar_chart: Alex Bot Dashboard.")
st.markdown("##")


db = boto3.resource('dynamodb', region_name = 'us-east-1' )
tables = list(db.tables.all())
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
data_load_state.text("Done! Alex.")

df = total(data)



# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")



sortedDates = sorted([datetime.datetime.strptime(item, '%Y-%m-%d') for item in df["date"].unique()])
sortedDates = [item.strftime('%Y-%m-%d') for item in sortedDates]


date = st.sidebar.multiselect(
    "Select the Date:",
    options=df["date"].unique(),
    default=sortedDates[-6:]
)

profit = st.sidebar.multiselect(
    "Select the Profit:",
    options=df["profit_"].unique(),
    default=df["profit_"].unique(),
)



df_selection = df.query(
    "date == @date & profit_ ==@profit"
)

# ---- MAINPAGE ----


# TOP KPI's\
total_sales = round(df["profit"].sum(), 2)
date_sales = round(df_selection["profit"].sum(), 2)
average_earning = round(df['profit'][df['profit_'] == 0].mean(), 1)
average_loosing = round(df['profit'][df['profit_'] == 1].mean(), 1)
date_average_earning = round(df_selection['profit'][df['profit_'] == 0].mean(), 1)
date_average_loosing = round(df_selection['profit'][df['profit_'] == 1].mean(), 1)
length_average_earning = len(df['profit'][df['profit_'] == 0])
length_average_loosing = len(df['profit'][df['profit_'] == 1])
date_length_average_earning = len(df_selection['profit'][df['profit_'] == 0])
date_length_average_loosing = len(df_selection['profit'][df['profit_'] == 1])
total_symbol = len(df['symbol'].unique())
date_symbol = len(df_selection['symbol'].unique())

left_column, middle_column = st.columns(2)
with left_column:
    st.text('___'*10)
    st.subheader("Total Earning:")
    st.subheader(f"US $ {total_sales:,}")
    st.text('___'*10)
    st.subheader("Total Average Earning:")
    st.subheader(f"{average_earning}")
    st.text('___'*10)
    st.subheader("Total Rigth choices:")
    st.subheader(f"Total: {length_average_earning}")

    st.text('___'*10)
    st.subheader("Total Wrong choices:")
    st.subheader(f"Total: {length_average_loosing}")
    st.text('___'*10)
    st.subheader("Total Average Loosing:")
    st.subheader(f"US $ {average_loosing }")
    st.text('___'*10)
    st.subheader("Total Symbols Trade:")
    st.subheader(f"Total: {total_symbol}")
    
    



with middle_column:
    st.text('___'*10)
    st.subheader("Date Earning:")
    st.subheader(f"US $ {date_sales:,}")
    st.text('___'*10)
    st.subheader("Date average Earning:")
    st.subheader(f"{date_average_earning}")
    st.text('___'*10)
    st.subheader("# Date Rigth choices:")
    st.subheader(f"Total: {date_length_average_earning}")

    st.text('___'*10)
    st.subheader("# Date Wrong choices:")
    st.subheader(f"Total: {date_length_average_loosing}")
    st.text('___'*10)
    st.subheader("Date Average Loosing:")
    st.subheader(f"US $ {date_average_loosing }")
    st.text('___'*10)
    st.subheader("Date Symbols Trade:")
    st.subheader(f"Total: {date_symbol}")

st.markdown("""---""")


# SALES BY PRODUCT LINE [BAR CHART]
sales_by_product_line = (
    df_selection.groupby(by=["date"]).sum()[["profit"]].sort_values(by="date")
)
fig_product_sales = px.bar(
    sales_by_product_line,
    x="profit",
    y=sales_by_product_line.index,
    orientation="h",
    title="<b>Profit by Date</b>",
    color_discrete_sequence=["#0063B8"] * len(sales_by_product_line),
    template="plotly_dark",
)
fig_product_sales.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False))
)

# SALES BY HOUR [BAR CHART]
sales_by_hour = df_selection.groupby(by=["symbol"]).sum()[["profit"]]
fig_hourly_sales = px.bar(
    sales_by_hour,
    y=sales_by_hour.index,
    x="profit",
    orientation="h",
    title="<b>Profit by Symbol</b>",
    color_discrete_sequence=["#CC6600"] * len(sales_by_hour),
    template="plotly_dark",
)
fig_hourly_sales.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
)
st.plotly_chart(fig_product_sales, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(fig_hourly_sales, use_container_width=True)
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


# To run the model
# source .venv/bin/activate
# streamlit run Home.py