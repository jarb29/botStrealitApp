import streamlit as st
import pandas as pd
import numpy as np
import boto3
import json
import datetime
import plotly.express as px

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
date = st.sidebar.multiselect(
    "Select the Date:",
    options=df["date"].unique(),
    default=df["date"].unique()
)

profit = st.sidebar.multiselect(
    "Select the Customer Type:",
    options=df["profit_"].unique(),
    default=df["profit_"].unique(),
)



df_selection = df.query(
    "date == @date & profit_ ==@profit"
)

# ---- MAINPAGE ----


# TOP KPI's
total_sales = round(df_selection["profit"].sum(), 2)
average_earning = round(df_selection['profit'][df['profit_'] == 0].mean(), 1)
average_loosing = round(df_selection['profit'][df['profit_'] == 1].mean(), 1)
length_average_earning = len(df_selection['profit'][df['profit_'] == 0])
length_average_loosing = len(df_selection['profit'][df['profit_'] == 1])

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.subheader("Total Earning:")
    st.subheader(f"US $ {total_sales:,}")

with middle_column:
    st.subheader("Average Earning:")
    st.subheader(f"{average_earning}")
    st.subheader("# Rigth choices:")
    st.subheader(f"Total {length_average_earning}")
with right_column:
    st.subheader("Average Loosing:")
    st.subheader(f"US $ {average_loosing }")
    st.subheader("# Wrong choices:")
    st.subheader(f"Total {length_average_loosing}")

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
    title="<b>Sales by date</b>",
    color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
    template="plotly_white",
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
    title="<b>Sales by Symbol</b>",
    color_discrete_sequence=["#0083B8"] * len(sales_by_hour),
    template="plotly_white",
)
fig_hourly_sales.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
)
st.plotly_chart(fig_product_sales, use_container_width=True)
st.plotly_chart(fig_hourly_sales, use_container_width=True)

# left_column, right_column = st.columns(2)
# left_column.plotly_chart(fig_hourly_sales, use_container_width=True)
# right_column.plotly_chart(fig_product_sales, use_container_width=True)


# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)