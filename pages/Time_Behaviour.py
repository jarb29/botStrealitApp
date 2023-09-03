import streamlit as st
import pandas as pd
import seaborn as sns
import boto3
import json
import datetime
import plotly.express as px
st.title('Time Profit or Loosing Behaviour Plot')





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
    df = df.groupby(['symbol', 'date'])['profit'].agg('sum').reset_index()
    return df

# def total(df):
#     df['date'] = pd.to_datetime(df['date_sold'])
#     df['dates'] = df['date'].dt.strftime('%Y-%m-%d')
#     df['Day_of_week'] = df['date'].dt.day_name()
#     df['hour'] = df['date'].dt.strftime('%H')
#     return df





data_load_state = st.text('Loading data...')
data = load_df(response)
data_load_state.text("Done! Alex")
st.markdown("""---""")

df = total(data)

def sum_profit(symbol_list, df):
    final = pd.DataFrame()
    for each in symbol_list:
        new_df = pd.DataFrame()
        new_df = df[df['symbol'] == each].reset_index()
        for ind in range(len(new_df)):
            if ind == 0:
                new_df.loc[ind, 'sum_profit']  = new_df.loc[ind, "profit"]
            else:
                 new_df.loc[ind, 'sum_profit'] = round(new_df.loc[ind, "profit"] + new_df.loc[ind-1, 'sum_profit'], 2)
                 
        final = pd.concat([new_df, final], ignore_index=True)
        new_df = []
    return final


def dates_profit(symbol_list, df):
    sortedDates = sorted([datetime.datetime.strptime(item, '%Y-%m-%d') for item in df["date"].unique()])
    sortedDates = [item.strftime('%Y-%m-%d') for item in sortedDates]
    sortedDates  =  list(pd.date_range(sortedDates[0],sortedDates[-1],freq='d').strftime("%Y-%m-%d"))
    final = pd.DataFrame()
    for each in symbol_list:
        new_df = pd.DataFrame()
        new_dfII = pd.DataFrame()
        new_df = df[df['symbol'] == each].reset_index()
        df2=new_df.loc[new_df['date'] == new_df['date'].values.tolist()[0]]
        df2['date'] = sortedDates[0]
        new_dfII = pd.concat([new_dfII, df2], ignore_index = True)
                    
                    

        if len(new_df)> 1:
            for ind in range(len(new_df)):
                if ind + 1 < len(new_df):
                    date_ini_idx = sortedDates.index(new_df.loc[ind, 'date'])
                    date_twi_idx = sortedDates.index(new_df.loc[ind+1, 'date'])
                    if (date_twi_idx - date_ini_idx) >= 1:
                        date_num  = date_twi_idx - date_ini_idx
                
                        for each in range(date_num):   
                            df2=new_df.loc[new_df['date'] == new_df.loc[ind, 'date']]
                            df2['date'] = sortedDates[int(date_ini_idx+each)]
                            new_dfII = pd.concat([new_dfII, df2], ignore_index = True)
                    else:
                        df2=new_df.loc[new_df['date'] == new_df.loc[ind, 'date']]
                        new_dfII = pd.concat([new_dfII, df2], ignore_index = True)

                
                else:
                    new_df  = new_df.sort_values("date")
                    date_ini_idx  = sortedDates.index(new_df['date'].values.tolist()[-1])
                    date_twi_idx = len(sortedDates)
                    date_num  = date_twi_idx - date_ini_idx
                    if date_num >= 1:
                        for each in range(date_num):
                            df2=new_df.loc[new_df['date'] == new_df['date'].values.tolist()[-1]]
                            df2['date'] = sortedDates[int(date_ini_idx+each)]
                            new_dfII = pd.concat([new_dfII, df2], ignore_index = True)
                    final = pd.concat([new_dfII, final], ignore_index=True)
        else:
            date_ini_idx  = sortedDates.index(new_df['date'].values.tolist()[-1])
            date_twi_idx = len(sortedDates)
            final_date = new_df['date'].values.tolist()[-1]
            date_num  = date_twi_idx - date_ini_idx
            if date_num >= 1:
                final_date_df=new_df.loc[new_df['date'] == final_date]
                for each in range(date_num):
                    final_date_df['date'] = sortedDates[int(date_ini_idx+each)]
                    new_dfII = pd.concat([new_dfII, final_date_df], ignore_index = True)   

        final = pd.concat([new_dfII, final], ignore_index=True)
       
    return final

symbol_list = df['symbol'].unique()

    
df = sum_profit(symbol_list, df)
print(df)

df['sum_profit'] = df['sum_profit'].apply(lambda x: round(x,2) if x > 0 else 0.01)
df['category'] = df['symbol'].apply(lambda x: 'BUSD' if x[-4:] == 'BUSD' else 'USDT')
df = dates_profit(symbol_list, df)


sortedDates = sorted([datetime.datetime.strptime(item, '%Y-%m-%d') for item in df["date"].unique()])
sortedDates = [item.strftime('%Y-%m-%d') for item in sortedDates]

dates =  list(pd.date_range(sortedDates[0],sortedDates[-1],freq='d').strftime("%Y-%m-%d"))



df = df.drop(['level_0',  'index'], axis=1)

df = df.drop_duplicates()
df  = df.sort_values("date").reset_index()
df = df.drop(['index'], axis=1).copy()
# print(df[df['date'] == '2023-08-14'])

max_profit = max(df['sum_profit'].values.tolist()) + 0.5

best20 = px.scatter(df, x="symbol", y="sum_profit", 
                    animation_frame="date", animation_group="symbol",
                    size="sum_profit", color="symbol", 
                    hover_name="symbol", facet_col="category",
                    size_max=15, range_y=[0,max_profit],
                    title="<b>Symbol Behaviour By Time</b>",
                    template="plotly_dark")

best20.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(154, 167, 199, 0.09)",
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