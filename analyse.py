import pandas as pd
import matplotlib.pyplot as plt
import pandas_ta as ta
import os.path

from datetime import date

# https://github.com/twopirllc/pandas-ta
plt.style.use('default')

# Vital
api_key = 'RUUKVAG9C6D2ECAL'

# Vishnu
# api_key = 'EE45PHWQN0W27PS1'

plot_chart = True 
print_result = False
write_to_file = False

# MANAMANA
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250

output_size = 'full' # default - compact 100 days data only
data_type = 'csv' # default - json

file_dir = '/Users/aprvital/Documents/Code/PyStockAnalysis'
dest_csv_file_url = '{}/{}-enriched-{}.csv'
src_csv_file_url = '{}/{}-{}.csv'

api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'

pd.set_option("display.max_columns", None)  # show all columns

def analyzeSymbol(symbol):
    print('Analyzing Symbol: %s' % symbol)
    src_file_path = src_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(src_file_path)

    url = src_file_path
    if not file_exists:
        url = api_url.format(api_key, symbol, output_size, data_type)
    print('Get data from URL: %s' % url)

    df = pd.read_csv(url)
    rows = df.shape[0]
    print("Got nRecords: %d" %rows)

    if rows < 5:
        print('Error getting data from URL: %s' % url)
        return

    df = df.truncate(after=data_truncate_days)
    if not file_exists:
        df.to_csv(src_file_path, index=False)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index(pd.DatetimeIndex(df["timestamp"]), inplace=True)
    df.sort_index(ascending=True, inplace=True)

    # pd.DataFrame: lower, mid, upper, bandwidth, and percent columns.
    typicalPrice(df)
    df.ta.bbands(close='close', length=20, std=2, append=True)
    df.ta.macd(close='close', signal_indicators=True,append=True)
    df.ta.dema(close='close', length=20, append=True)
    df.ta.dema(close='close', length=50, append=True)
    df.ta.rsi(close='close', append=True)
    df.ta.stoch(close='close', append=True)
    df.ta.vwap(high='high', low='low', close='close', volume='volume', append=True)
    df.ta.adx(high='high', low='low', close='close', append=True)
    df.ta.obv(close='close', volume='volume', append=True)
    df.rename(columns={"BBL_20_2.0": "bbl", "BBM_20_2.0": "bbm", "BBU_20_2.0": "bbu", "BBB_20_2.0":"bbb", "BBP_20_2.0":"bbp", 
                       "MACD_12_26_9":"macd", "MACDh_12_26_9":"macdh", "MACDs_12_26_9":"macds", "RSI_14":"rsi", "OBV": "obv",
                       "STOCHk_14_3_3":"stochk", "STOCHd_14_3_3":"stochd", "ADX_14":"adx", "DMP_14":"dmp", "DMN_14":"dmn", "DEMA_20":"dema20", "DEMA_50":"dema50", "VWAP_D":"vwap"}, inplace = True)

    macdReco(df)
    rsiReco(df)
    adxReco(df)

    df.sort_index(ascending=False, inplace=True)
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

def macdReco(df):
    # Logic To Be Verified
    df['macd_reco'] = 'NA'
    df.loc[df['MACDh_12_26_9_XA_0'] == 1, 'macd_reco'] = 'Buy'
    df.loc[df['MACDh_12_26_9_XB_0'] == 1, 'macd_reco'] = 'Sell'
    return df

def rsiReco(df):
    # Logic To Be Verified
    df['rsi_reco'] = 'NA'
    df.loc[df['rsi'] < 30, 'rsi_reco'] = 'Sell'
    df.loc[df['rsi'] > 70, 'rsi_reco'] = 'Buy'

def adxReco(df):
    # Logic To Be Verified
    df['adx_reco'] = 'A'
    df.loc[df['adx'] < 25, 'adx_reco'] = 'NA'

# Plot Charts
def plotCharts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=2, sharex=True, figsize=(18, 8))

    ax[0, 0].plot(df['timestamp'], df['macd'], label='macd', color='#ff000080', linestyle='solid')
    # ax[0, 0].plot(df['timestamp'], df['macdh'], label='macdh', color='#00000080', linestyle='solid')
    ax[0, 0].plot(df['timestamp'], df['macds'], label='macds', color='#0000ff80', linestyle='solid')
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

    ax[2, 0].plot(df['timestamp'], df['adx'], label='adx', color='#0000ff80', linestyle='solid')
    ax[2, 0].plot(df['timestamp'], df['dmp'], label='+di', color='#ff000080', linestyle='dotted')
    ax[2, 0].plot(df['timestamp'], df['dmn'], label='-di', color='#00ff0080', linestyle='dotted')
    ax[2, 0].axhline(y=25, color='#00000080', label='25', linestyle='dotted', lw=1)
    ax[2, 0].set_ylabel('ADX')
    ax[2, 0].grid(True, linestyle='-.')
    ax[2, 0].legend()

    ax[3, 0].plot(df['timestamp'], df['dema20'], label='dema20', color='#ff000080', linestyle='solid')
    ax[3, 0].plot(df['timestamp'], df['dema50'], label='dema50', color='#0000ff80', linestyle='-.')
    ax[3, 0].set_ylabel('DEMA')
    ax[3, 0].grid(True, linestyle='-.')
    ax[3, 0].legend()

    ax[0, 1].plot(df['timestamp'], df['close'], label='closing price', color='#0000ff80', linestyle='solid')
    ax[0, 1].plot(df['timestamp'], df['bbu'], label='bbu', color='#ff000080', linestyle='dotted')
    ax[0, 1].plot(df['timestamp'], df['bbl'], label='bbl', color='#00ff0080', linestyle='dotted')
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

    ax[3, 1].plot(df['timestamp'], df['stochk'], label='k', color='#ff000080', linestyle='solid')
    ax[3, 1].plot(df['timestamp'], df['stochd'], label='d', color='#0000ff80', linestyle='-.')
    ax[3, 1].set_ylabel('STOCH')
    ax[3, 1].grid(True, linestyle='-.')
    ax[3, 1].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()

analyzeSymbol(symbols[1])
