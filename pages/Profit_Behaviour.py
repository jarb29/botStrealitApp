import streamlit as st
import pandas as pd
import seaborn as sns
import boto3
import json
import datetime

import matplotlib.pyplot as plt

st.title('Profit Behaviour per each time that the symbol is choose.')





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
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

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
st.markdown("""---""")

df = total(data)

 
# Create a Seaborn correlation plot

sns.set_style("dark")


colsInt = df['symbol'].unique()
total_n = len(colsInt)
fig, axes = plt.subplots(round(len(colsInt)/3),3,figsize=(15, 60))
for i in range(len(colsInt)-1):
    plt.subplot(round(total_n/3),3,i+1)
    new_df = df[df['symbol'] == colsInt[i]]
    if len(new_df) > 1:
        chart = sns.histplot(new_df, hue='profit_',x='profit',
                             bins=40,kde=True,palette="flare");
        
        plt.gca().set_title(colsInt[i])
    
fig.tight_layout()
 
# Display the plot in Streamlit
st.pyplot(chart.get_figure())
st.markdown("""---""")