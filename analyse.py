import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('default')
pd.options.display.max_rows = 100

api_key = 'RUUKVAG9C6D2ECAL'
plot_chart = False
print_result = False

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250
rsi_rolling_period = 10

output_size = 'full' #default - compact 100 days data only
data_type = 'csv' #default - json

def analyzeSymbol(symbol):
    print("analyzeSymbol == " + symbol)
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'
    url = url.format(api_key, symbol, output_size, data_type)
    print("URL --> %s" % url)

    df = pd.read_csv(url)
    print("Got nRecords ==  %d" % df.size)
    print(df.head(5))
    df = df.truncate(after=data_truncate_days)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(df.head(10))

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

analyzeSymbols()
