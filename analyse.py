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
print_result = False

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250
rsi_rp = 14
bbands_rp = 20
stoch_rp_1 = 14
stoch_rp_2 = 3

output_size = 'full'  # default - compact 100 days data only
data_type = 'csv'  # default - json

csv_file_url = 'C:/Users/panumula/Downloads/data-analysis/{}-{}.csv'
api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'


def analyzeSymbol(symbol):
    print("analyzeSymbol --> %s" % symbol)
    file_path = csv_file_url.format(symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(file_path)

    url = file_path
    if not file_exists:
        url = api_url.format(api_key, symbol, output_size, data_type)
    print("Get data from URL --> %s" % url)

    df = pd.read_csv(url)
    print("Got nRecords ==  %d" % df.size)

    if df.size < 5:
        print("Error getting data from URL --> %s" % url)

    print(df.head(5))
    df = df.truncate(after=data_truncate_days)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if not file_exists:
        df.to_csv(file_path)

    typicalPrice(df)
    macd(df)
    doubleEMA(df)
    relativeStrengthIndicator(df)
    bollingerBand(df)
    stochasticOscillator(df)
    volumeWeightedAvgPrice(df)

    if print_result:
        print(df.to_string())

    if plot_chart:
        plotCharts(df, symbol)


def analyzeSymbols():
    for symbol in symbols:
        analyzeSymbol(symbol)

# Implement ADX, OBV, CCI, AROON

# TP
def typicalPrice(df):
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    return df

# STOCH
def stochasticOscillator(df):
    low_min = df['low'].rolling(window=stoch_rp_1).min().shift(-stoch_rp_1+1)
    high_max = df['high'].rolling(window=stoch_rp_1).max().shift(-stoch_rp_1+1)
    k_fast = 100 * (df['close'] - low_min)/(high_max - low_min)
    k_fast.ffill(inplace=True)
    d_fast = k_fast.rolling(window=stoch_rp_2).mean().shift(-stoch_rp_2+1)
    k_slow = d_fast
    d_slow = k_slow.rolling(window=stoch_rp_2).mean().shift(-stoch_rp_2+1)
    df['k_slow'] = k_slow
    df['k_fast'] = k_fast
    return df

# VWAP
def volumeWeightedAvgPrice(df):
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

# RSI
def relativeStrengthIndicator(df):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(rsi_rp).mean().shift(-rsi_rp + 1)
    avg_loss = loss.rolling(rsi_rp).mean().shift(-rsi_rp + 1)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Logic To Be Verified
    df['rsi_reco'] = 'None'
    df.loc[rsi < 30, 'rsi_reco'] = 'Sell'
    df.loc[rsi > 70, 'rsi_reco'] = 'Buy'
    df['rsi'] = rsi
    return df

# MACD
def macd(df):
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()

    df['macd'] = macd
    df['macd_signal'] = macd_signal

    # Logic To Be Verified
    df['macd_reco'] = 'Buy'
    df.loc[macd < macd_signal, 'macd_reco'] = 'Sell'
    return df

# DEMA
def doubleEMA(df):
    ema20 = df['close'].ewm(span=20).mean()
    eema20 = ema20.ewm(span=20).mean()
    dema20 = 2 * ema20 - eema20

    ema50 = df['close'].ewm(span=50).mean()
    eema50 = ema50.ewm(span=50).mean()
    dema50 = 2 * ema50 - eema50
    df['dema20'] = dema20
    df['dema50'] = dema50

    # Logic To Be Verified
    df['dema_reco'] = 'Buy'
    df.loc[dema20 < dema50, 'dema_reco'] = 'Sell'
    return df

# BBANDS
def bollingerBand(df):
    b_ma = df['tp'].rolling(bbands_rp).mean().shift(-bbands_rp + 1)
    sigma = df['tp'].rolling(bbands_rp).std().shift(-bbands_rp + 1)

    bu = b_ma + 2 * sigma
    bl = b_ma - 2 * sigma

    df['b_reco'] = 'None'
    df.loc[bu > df['close'], 'b_reco'] = 'Sell'
    df.loc[bl > df['close'], 'b_reco'] = 'Buy'

    df['bu'] = bu
    df['bl'] = bl
    return df


def plotCharts(df, symbol):
    fig, ax = plt.subplots(nrows=6, ncols=1, sharex=True, figsize=(18, 8))

    ax[0].plot(df['timestamp'], df['macd'], label='macd', color='#ff000080', linestyle='solid')
    ax[0].plot(df['timestamp'], df['macd_signal'], label='macd_signal', color='#0000ff80', linestyle='-.')
    ax[0].set_ylabel('MACD')
    ax[0].grid(True, linestyle='-.')
    ax[0].legend()

    ax[1].plot(df['timestamp'], df['dema20'], label='dema20', color='#ff000080', linestyle='solid')
    ax[1].plot(df['timestamp'], df['dema50'], label='dema50', color='#0000ff80', linestyle='-.')
    ax[1].set_ylabel('DEMA')
    ax[1].grid(True, linestyle='-.')
    ax[1].legend()

    ax[2].fill_between(df['timestamp'], df['rsi'], label='rsi', color='lightsteelblue', linestyle='solid')
    ax[2].axhline(y=30, color='#00ff0080', label='30%', linestyle='dotted', lw=1)
    ax[2].axhline(y=50, color='#0000ff80', label='50%', linestyle='dotted', lw=1)
    ax[2].axhline(y=70, color='#ff000080', label='70%', linestyle='dotted', lw=1)
    ax[2].set_ylabel('RSI')
    ax[2].grid(True, linestyle='-.')
    ax[2].legend()

    ax[3].plot(df['timestamp'], df['close'], label='closing price', color='#0000ff80', linestyle='solid')
    ax[3].plot(df['timestamp'], df['bu'], label='bollinger upper', color='#ff000080', linestyle='dotted')
    ax[3].plot(df['timestamp'], df['bl'], label='bollinger lower', color='#00ff0080', linestyle='dotted')
    ax[3].set_ylabel('BOLLINGER')
    ax[3].grid(True, linestyle='-.')
    ax[3].legend()

    ax[4].plot(df['timestamp'], df['k_fast'], label='k_fast', color='#ff000080', linestyle='solid')
    ax[4].plot(df['timestamp'], df['k_slow'], label='k_slow', color='#0000ff80', linestyle='-.')
    ax[4].set_ylabel('STOCH')
    ax[4].grid(True, linestyle='-.')
    ax[4].legend()

    ax[5].plot(df['timestamp'], df['close'], label='closing price', color='#0000ff80', linestyle='-.')
    ax[5].plot(df['timestamp'], df['vwap'], label='vwap', color='#ff000080', linestyle='solid')
    ax[5].set_ylabel('VWAP')
    ax[5].grid(True, linestyle='-.')
    ax[5].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()


analyzeSymbol(symbols[0])
