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

st.title("Closed Choices by Date")
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
    df['month'] = df['date'].dt.strftime('%Y-%m')
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    return df

def close(df):
    date_quant = df.groupby(['month','date', 'profit_', 'method'])['symbol'].agg('count').reset_index()
    return date_quant

data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex.")

df = total(data)
datas = close(df)

sortedMoth = sorted([datetime.datetime.strptime(item, '%Y-%m') for item in df['month'].unique()])
sortedMonth = [item.strftime('%Y-%m') for item in sortedMoth]




# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")
month = st.sidebar.multiselect(
    "Select the Moth:",
    options=sortedMonth,
    default=sortedMonth[-6:]
)

df_selection = datas.query(
    "month == @month"
)

sortedDates = sorted([datetime.datetime.strptime(item, '%Y-%m-%d') for item in df_selection["date"].unique()])
sortedDates = [item.strftime('%Y-%m-%d') for item in sortedDates]

date = st.sidebar.multiselect(
    "Select the Date:",
    options=sortedDates,
    default=sortedDates[-6:]
)

df_dates = df_selection.query(
    "date == @date"
)




profit = st.sidebar.multiselect(
    "Select the Profit:",
    options=df_dates["profit_"].unique(),
    default=df_dates["profit_"].unique(),
)

df_profit = df_dates.query(
    "profit_ == @profit"
)



method = st.sidebar.multiselect(
    "Select the Method:",
    options=df_profit["method"].unique(),
    default=df_profit["method"].unique(),
)


df_method = df_profit.query(
    "method == @method"
)


df_selection = datas.query(
    "date == @date & profit_ ==@profit"
)

df_selection_method = df.query(
    "date == @date & profit_ ==@profit & method ==@method"
)
# ---- MAINPAGE ----
symbol_df = df.query(
    "date == @date & profit_ ==@profit"
)


st.markdown("""---""")


# SALES BY PRODUCT LINE [BAR CHART]
df_selection['Profit'] = df_selection['profit_'].apply(lambda x: 'Profit' if x == 0 else 'Loosing')
df_selection['Quantity'] = df_selection['symbol']
sales_by_product_line = (
    df_selection.groupby(['date', 'Profit'])['Quantity'].agg('sum').reset_index()
)

df_selection_method['method'] = df_selection_method['method'].apply(lambda x: 'Forecast' if x == 'deep_learning_forecast' else 'Binance')

profit_df_selection_method = (
    df_selection_method.groupby(['date', 'method'])['profit'].agg('sum').reset_index()
)
profit_df_selection_method_quantity = df_selection_method.groupby(['date', 'method'])['symbol'].agg('count').reset_index()
profit_df_selection_method_quantity['Quantity'] = profit_df_selection_method_quantity['symbol']
profit_df_selection_method_quantity = (
    profit_df_selection_method_quantity
)

fig_product_sales = px.bar(
    sales_by_product_line,
    x='Quantity',
    color="Profit",
    y=sales_by_product_line.date,
    orientation="h",
    title="<b>Quantity by Date</b>",
    # color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
    template="plotly_dark",
)
fig_product_sales.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    # xaxis=(dict(showgrid=True)),
    # yaxis=(dict(showgrid=True))
)

# SALES BY HOUR [BAR CHART]
fig_hourly_sales = px.bar(
    profit_df_selection_method,
    y=profit_df_selection_method.date,
    x="profit",
    color = 'method',
    orientation="h",
    title="<b>Profit by Method</b>",
    # color_discrete_sequence=["#0083B8"] * len(profit_df_selection_method),
    template="plotly_dark",
)
fig_hourly_sales.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)

fig_hourly_sales_quantity = px.bar(
    profit_df_selection_method_quantity,
    y=profit_df_selection_method_quantity.date,
    x="Quantity",
    color = 'method',
    orientation="h",
    title="<b>Quantity by Method</b>",
    # color_discrete_sequence=["#0083B8"] * len(profit_df_selection_method),
    template="plotly_dark",
)
fig_hourly_sales_quantity.update_layout(
    xaxis=dict(tickmode="linear"),
    # plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)
symbol_df =  ( symbol_df.groupby(['symbol'])['profit'].agg('sum').reset_index())


symbol = px.bar(
    symbol_df,
    y='symbol',
    x="profit",
    # color = 'method',
    orientation="h",
    title="<b>Profit by Symbol</b>",
    # color_discrete_sequence=["#0083B8"] * len(profit_df_selection_method),
    template="plotly_dark",
)
symbol.update_layout(
    xaxis=dict(tickmode="linear"),
    # plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=True))
)




st.plotly_chart(fig_product_sales, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(fig_hourly_sales, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(fig_hourly_sales_quantity, use_container_width=True)
st.markdown("""---""")
st.plotly_chart(symbol, use_container_width=True)
st.markdown("""---""")
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