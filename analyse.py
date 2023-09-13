import pandas as pd
import matplotlib.pyplot as plt
import os.path
import numpy as np
from datetime import date

plt.style.use('default')

# Vital
api_key = 'RUUKVAG9C6D2ECAL'

# Vishnu
# api_key = 'EE45PHWQN0W27PS1'

plot_chart = True 
print_result = False
write_to_file = True

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250
rsi_rp = 14
bbands_rp = 20
stoch_rp_1 = 14
stoch_rp_2 = 3
adx_rp = 14

output_size = 'full' # default - compact 100 days data only
data_type = 'csv' # default - json

file_dir = 'C:/Users/panumula/Downloads/data-analysis'
dest_csv_file_url = '{}/{}-enriched-{}.csv'
src_csv_file_url = '{}/{}-{}.csv'

api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'

def analyzeSymbol(symbol):
    print('Analyzing Symbol: %s' % symbol)
    src_file_path = src_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(src_file_path)

    url = src_file_path
    if not file_exists:
        url = api_url.format(api_key, symbol, output_size, data_type)
    print('Get data from URL: %s' % url)

    df = pd.read_csv(url)
    print('Got nRecords: %d' % df.size)

    if df.size < 5:
        print('Error getting data from URL: %s' % url)
        return

    print(df.head(5))
    df = df.truncate(after=data_truncate_days)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if not file_exists:
        df.to_csv(src_file_path, index=False)

    typicalPrice(df)
    macd(df)
    dema(df)
    rsi(df)
    bollingerBand(df)
    stoch(df)
    vwap(df)
    adx(df)
    obv(df)

    if(write_to_file):
        dest_file_path = dest_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
        df.to_csv(dest_file_path, index=False)

    if print_result:
        print(df.to_string())

    if plot_chart:
        plotCharts(df, symbol)

def analyzeSymbols():
    for symbol in symbols:
        analyzeSymbol(symbol)

# TODO - Implement CCI, AROON

# TP
def typicalPrice(df):
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    return df

# STOCH
def stoch(df):
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
def vwap(df):
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df

# RSI
def rsi(df):
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
def dema(df):
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

# ADX
def adx(df):
    high = df['high']
    low = df['low']
    close = df['close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
    atr = tr.rolling(adx_rp).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha = 1/adx_rp).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha = 1/adx_rp).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = ((dx.shift(1) * (adx_rp - 1)) + dx) / adx_rp
    adx_smooth = adx.ewm(alpha = 1/adx_rp).mean()

    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    df['adx_smooth'] = adx_smooth
    df['adx_reco'] = 'None'
    df.loc[(adx_smooth > 25) & (plus_di < minus_di), 'adx_reco'] = 'Sell'
    df.loc[(adx_smooth > 25) & (plus_di > minus_di), 'adx_reco'] = 'Buy'
    
    return df

# OBV
def obv(df):
    df['obv'] = np.where(df['close'] > df['close'].shift(1), df['volume'], np.where(df['close'] < df['close'].shift(1), -df['volume'], 0)).cumsum()
    return df

# Plot Charts
def plotCharts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=2, sharex=True, figsize=(18, 8))

    ax[0, 0].plot(df['timestamp'], df['macd'], label='macd', color='#ff000080', linestyle='solid')
    ax[0, 0].plot(df['timestamp'], df['macd_signal'], label='macd_signal', color='#0000ff80', linestyle='-.')
    ax[0, 0].set_ylabel('MACD')
    ax[0, 0].grid(True, linestyle='-.')
    ax[0, 0].legend()

    ax[1, 0].fill_between(df['timestamp'], df['rsi'], label='rsi', color='lightsteelblue', linestyle='solid')
    ax[1, 0].axhline(y=30, color='#00ff0080', label='30%', linestyle='dotted', lw=1)
    ax[1, 0].axhline(y=50, color='#0000ff80', label='50%', linestyle='dotted', lw=1)
    ax[1, 0].axhline(y=70, color='#ff000080', label='70%', linestyle='dotted', lw=1)
    ax[1, 0].set_ylabel('RSI')
    ax[1, 0].grid(True, linestyle='-.')
    ax[1, 0].legend()

    ax[2, 0].plot(df['timestamp'], df['k_fast'], label='k_fast', color='#ff000080', linestyle='solid')
    ax[2, 0].plot(df['timestamp'], df['k_slow'], label='k_slow', color='#0000ff80', linestyle='-.')
    ax[2, 0].set_ylabel('STOCH')
    ax[2, 0].grid(True, linestyle='-.')
    ax[2, 0].legend()

    ax[3, 0].plot(df['timestamp'], df['dema20'], label='dema20', color='#ff000080', linestyle='solid')
    ax[3, 0].plot(df['timestamp'], df['dema50'], label='dema50', color='#0000ff80', linestyle='-.')
    ax[3, 0].set_ylabel('DEMA')
    ax[3, 0].grid(True, linestyle='-.')
    ax[3, 0].legend()

    ax[0, 1].plot(df['timestamp'], df['close'], label='closing price', color='#0000ff80', linestyle='solid')
    ax[0, 1].plot(df['timestamp'], df['bu'], label='bollinger upper', color='#ff000080', linestyle='dotted')
    ax[0, 1].plot(df['timestamp'], df['bl'], label='bollinger lower', color='#00ff0080', linestyle='dotted')
    ax[0, 1].set_ylabel('BOLLINGER')
    ax[0, 1].grid(True, linestyle='-.')
    ax[0, 1].legend()

    ax[1, 1].plot(df['timestamp'], df['close'], label='closing price', color='#0000ff80', linestyle='-.')
    ax[1, 1].plot(df['timestamp'], df['vwap'], label='vwap', color='#ff000080', linestyle='solid')
    ax[1, 1].set_ylabel('VWAP')
    ax[1, 1].grid(True, linestyle='-.')
    ax[1, 1].legend()

    ax[2, 1].plot(df['timestamp'], df['obv'], label='obv', color='#ff000080', linestyle='solid')
    ax[2, 1].plot(df['timestamp'], df['volume'], label='volume', color='#00ff0080', linestyle='solid')
    ax[2, 1].set_ylabel('OBV')
    ax[2, 1].grid(True, linestyle='-.')
    ax[2, 1].legend()

    ax[3, 1].plot(df['timestamp'], df['adx_smooth'], label='adx_smooth', color='#0000ff80', linestyle='solid')
    ax[3, 1].plot(df['timestamp'], df['plus_di'], label='+di', color='#ff000080', linestyle='dotted')
    ax[3, 1].plot(df['timestamp'], df['minus_di'], label='-di', color='#00ff0080', linestyle='dotted')
    ax[3, 1].axhline(y=25, color='#00000080', label='25', linestyle='dotted', lw=1)
    ax[3, 1].set_ylabel('ADX')
    ax[3, 1].grid(True, linestyle='-.')
    ax[3, 1].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()

analyzeSymbol(symbols[0])
