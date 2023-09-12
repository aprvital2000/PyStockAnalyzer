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

plot_chart = True
print_result = True

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250
rsi_rolling_period = 14
bollinger_rolling_period = 20

output_size = 'full' #default - compact 100 days data only
data_type = 'csv' #default - json

csv_file_url = 'C:/Users/panumula/Downloads/data-analysis/{}-{}.csv'
api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'

def analyzeSymbol(symbol):
    print("analyzeSymbol --> %s" %symbol)
    file_path = csv_file_url.format(symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(file_path)

    url = file_path
    if not file_exists:
        url = api_url.format(api_key, symbol, output_size, data_type)
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
    macd, macd_signal = getMacd(close)
    df['macd'] = macd
    df['macd_signal'] = macd_signal

    # Logic To Be Verified
    df['macd_reco'] = 'Buy'
    df.loc[macd < macd_signal, 'macd_reco'] = 'Sell'
    
    ### Calculate DEMA (Double EMA)
    dema20, dema50 = getDema(close)
    df['dema20'] = dema20
    df['dema50'] = dema50

    # Logic To Be Verified
    df['dema_reco'] = 'Buy'
    df.loc[dema20 < dema50, 'dema_reco'] = 'Sell'

    ### Calculate RSI
    rsi = getRsi(close)
    df['rsi'] = rsi
    # Logic To Be Verified
    df['rsi_reco'] = 'None'
    df.loc[rsi < 30, 'rsi_reco'] = 'Sell'
    df.loc[rsi > 70, 'rsi_reco'] = 'Buy'

    bu, bl = getBollingerBand(df)
    df['bu'] = bu
    df['bl'] = bl
    df['b_reco'] = 'None'
    df.loc[bu > close, 'b_reco'] = 'Sell'
    df.loc[bl > close, 'b_reco'] = 'Buy'

    if print_result:
        print(df.to_string())

    if plot_chart:
        plotCharts(df, symbol)

def analyzeSymbols():
    for symbol in symbols:
        analyzeSymbol(symbol)

def getRsi(close):
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(rsi_rolling_period).mean().shift(-rsi_rolling_period + 1)
    avg_loss = loss.rolling(rsi_rolling_period).mean().shift(-rsi_rolling_period + 1)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def getMacd(close):
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()
    return macd, macd_signal

def getDema(close):
    ema20 = close.ewm(span=20).mean()
    eema20 = ema20.ewm(span=20).mean()
    dema20 = 2 * ema20 - eema20

    ema50 = close.ewm(span=50).mean()
    eema50 = ema20.ewm(span=50).mean()
    dema50 = 2 * ema50 - eema50
    return dema20, dema50

def getBollingerBand(df):
    #typical price
    tp = (df['high'] + df['low'] + df['close']) / 3
    b_ma = tp.rolling(bollinger_rolling_period).mean().shift(-bollinger_rolling_period + 1)
    sigma = tp.rolling(bollinger_rolling_period).std().shift(-bollinger_rolling_period + 1)
    
    bu = b_ma + 2 * sigma
    bl = b_ma - 2 * sigma
    return bu, bl

def plotCharts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(18, 8))
    
    ax[0].plot(df['timestamp'], df['macd'], label='macd', color='r', linestyle='solid')
    ax[0].plot(df['timestamp'], df['macd_signal'], label='macd_signal', color='b', linestyle='-.')
    ax[0].set_ylabel('MACD')
    ax[0].grid(True, linestyle='-.')
    ax[0].legend()

    ax[1].plot(df['timestamp'], df['dema20'], label='dema20', color='r', linestyle='solid')
    ax[1].plot(df['timestamp'], df['dema50'], label='dema50', color='b', linestyle='-.')
    ax[1].set_ylabel('DEMA')
    ax[1].grid(True, linestyle='-.')
    ax[1].legend()

    ax[2].plot(df['timestamp'], df['rsi'], label='rsi', color='b', linestyle='solid')
    ax[2].axhline(y=30, color='g', label='30%', linestyle='dotted', lw=2)
    ax[2].axhline(y=70, color='r', label='70%', linestyle='dotted', lw=2)
    ax[2].set_ylabel('RSI')
    ax[2].grid(True, linestyle='-.')
    ax[2].legend()

    ax[3].plot(df['timestamp'], df['close'], label='closing price', color='b', linestyle='solid')
    ax[3].plot(df['timestamp'], df['bu'], label='bollinger upper', color='r', linestyle='-.')
    ax[3].plot(df['timestamp'], df['bl'], label='bollinger lower', color='g', linestyle='-.')
    ax[3].set_ylabel('BOLLINGER')
    ax[3].grid(True, linestyle='-.')
    ax[3].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    fig.supxlabel('Date')
    fig.tight_layout()

    plt.xticks(rotation=45)
    plt.show()

analyzeSymbol(symbols[0])
