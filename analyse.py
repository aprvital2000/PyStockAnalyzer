import pandas as pd
import matplotlib.pyplot as plt
import os.path
from pathlib import Path
from datetime import date

plt.style.use('default')
pd.options.display.max_rows = 100

# Vital
api_key = 'RUUKVAG9C6D2ECAL'

# Vishnu
# api_key = 'EE45PHWQN0W27PS1'

plot_chart = False
print_result = True

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250
rsi_rolling_period = 10

output_size = 'full' #default - compact 100 days data only
data_type = 'csv' #default - json

def analyzeSymbol(symbol):
    print("analyzeSymbol --> %s" %symbol)
    file_path = getFilePath(symbol)
    file_exists = os.path.isfile(file_path)

    url = file_path
    if not file_exists:
        url = getApiUrl(symbol)
    print("Get data from URL --> %s" %url)

    df = pd.read_csv(url)
    print("Got nRecords ==  %d" %df.size)
    if df.size < 5:
        print("Error getting data from URL --> %s" %url)

    print(df.head(5))
    df = df.truncate(after=data_truncate_days)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if not file_exists:
        df.to_csv(file_path)

    close = df['close']
    ### Calculate Exponential Moving Averages (EMA)
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    macdSig = macd.ewm(span=9).mean()
    delta = macdSig - macd
    df['macd'] = macd
    df['macd_sig'] = macdSig

    df['reco'] = 'Buy'
    df.loc[delta > 0, 'reco'] = 'Sell'
    
    if print_result:
        print(df.to_string())

    if plot_chart:
        df.plot(x='timestamp', y=['macd', 'macd_sig'], figsize=(18,9), style='-o', grid=True)
        plt.xlabel('Date')
        plt.ylabel('Technical Indicator')
        plt.title(symbol)
        plt.show()

def analyzeSymbols():
    for symbol in symbols:
        analyzeSymbol(symbol)

def getFilePath(symbol):
    file_path = '/Users/aprvital/Documents/Code/PyStockAnalysis/{}-{}.csv'
    return file_path.format(symbol, date.today().strftime('%d%m%y'))

def getApiUrl(symbol):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'
    return url.format(api_key, symbol, output_size, data_type)

analyzeSymbols()
