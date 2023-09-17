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
print_result = True
write_to_file = True

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
    df.ta.bbands(close='close', length=20, std=2, signal_indicators=True, append=True)
    df.ta.macd(close='close', signal_indicators=True, append=True)

    df.ta.dema(close='close', length=20, append=True)
    df.ta.dema(close='close', length=50, append=True)
    xsignal = ta.cross(df['DEMA_20'], df['DEMA_50'])
    df['DEMA_20_50_XA'] = xsignal
    xsignal = ta.cross(df['DEMA_50'], df['DEMA_20'])
    df['DEMA_20_50_XB'] = xsignal

    df.ta.rsi(close='close', signal_indicators=True, append=True)

    df.ta.stoch(close='close', signal_indicators=True, append=True)
    xsignal = ta.cross(df['STOCHk_14_3_3'], df['STOCHd_14_3_3'])
    df['STOCHk_14_3_3_XA'] = xsignal
    xsignal = ta.cross(df['STOCHd_14_3_3'], df['STOCHk_14_3_3'])
    df['STOCHk_14_3_3_XB'] = xsignal

    df.ta.vwap(high='high', low='low', close='close', volume='volume', append=True)
    # xsignal = ta.signals(df['VWAP_D'], df['close'])
    # df['VWAP_D_XA'] = xsignal
    # xsignal = ta.cross(df['close'], df['VWAP_D'])
    # df['VWAP_D_XB'] = xsignal

    df.ta.adx(high='high', low='low', close='close', signal_indicators=True, append=True)
    df.ta.obv(close='close', volume='volume', append=True)

    macdReco(df)
    rsiReco(df)
    adxReco(df)
    bbReco(df)
    demaReco(df)
    stochReco(df)

    df.sort_index(ascending=False, inplace=True)
    df.dropna(subset=['MACDs_12_26_9'], inplace=True)

    if(write_to_file):
        dest_file_path = dest_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
        df.to_csv(dest_file_path, index=False)

    if print_result:
        print(df.keys())
        # print(df.to_string())

    if plot_chart:
        plotCharts(df, symbol)

def analyzeSymbols():
    for symbol in symbols:
        analyzeSymbol(symbol)

# TODO - Implement CCI, AROON

def macdReco(df):
    # Logic To Be Verified
    df['macd_reco'] = 'No Action'
    df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['MACD_12_26_9'] < 0), 'macd_reco'] = 'Buy'
    df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['MACD_12_26_9'] > 0), 'macd_reco'] = 'Sell'
    return df

def rsiReco(df):
    # Logic To Be Verified
    df['rsi_reco'] = 'No Action'
    df.loc[df['RSI_14'] <= 50, 'rsi_reco'] = 'Sell'
    df.loc[df['RSI_14'] > 50, 'rsi_reco'] = 'Buy'

def adxReco(df):
    # Logic To Be Verified
    df['adx_reco'] = 'Action'
    df.loc[df['ADX_14'] < 25, 'adx_reco'] = 'NA'

def bbReco(df):
    # Logic To Be Verified
    df['bb_reco'] = 'No Action'
    df.loc[df['BBP_20_2.0'] >= 1, 'bb_reco'] = 'Buy'
    df.loc[df['BBP_20_2.0'] <= 0, 'bb_reco'] = 'Sell'

def demaReco(df):
    # Logic To Be Verified
    df['dema_reco'] = 'No Action'
    df.loc[df['DEMA_20_50_XA'] == 1, 'dema_reco'] = 'Buy'
    df.loc[df['DEMA_20_50_XB'] == 1, 'dema_reco'] = 'Sell'

def stochReco(df):
    # Logic To Be Verified
    df['stoch_reco'] = 'No Action'
    df.loc[df['STOCHk_14_3_3_XA'] == 1, 'stoch_reco'] = 'Buy'
    df.loc[df['STOCHk_14_3_3_XB'] == 1, 'stoch_reco'] = 'Sell'

# Plot Charts
def plotCharts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=2, sharex=True, figsize=(18, 8))

    ax[0, 0].plot(df['timestamp'], df['MACD_12_26_9'], label='MACD', color='#ff000080', linestyle='solid')
    ax[0, 0].plot(df['timestamp'], df['MACDs_12_26_9'], label='MACDs', color='#0000ff80', linestyle='solid')
    ax[0, 0].set_ylabel('MACD')
    ax[0, 0].grid(True, linestyle='-.')
    ax[0, 0].legend()

    ax[1, 0].fill_between(df['timestamp'], df['RSI_14'], label='RSI', color='lightsteelblue', linestyle='solid')
    ax[1, 0].axhline(y=30, color='#00ff0080', label='30%', linestyle='dotted', lw=1)
    ax[1, 0].axhline(y=50, color='#0000ff80', label='50%', linestyle='dotted', lw=1)
    ax[1, 0].axhline(y=70, color='#ff000080', label='70%', linestyle='dotted', lw=1)
    ax[1, 0].set_ylabel('RSI')
    ax[1, 0].grid(True, linestyle='-.')
    ax[1, 0].legend()

    ax[2, 0].plot(df['timestamp'], df['ADX_14'], label='ADX', color='#0000ff80', linestyle='solid')
    ax[2, 0].plot(df['timestamp'], df['DMP_14'], label='+di', color='#ff000080', linestyle='dotted')
    ax[2, 0].plot(df['timestamp'], df['DMN_14'], label='-di', color='#00ff0080', linestyle='dotted')
    ax[2, 0].axhline(y=25, color='#00000080', label='25', linestyle='dotted', lw=1)
    ax[2, 0].set_ylabel('ADX')
    ax[2, 0].grid(True, linestyle='-.')
    ax[2, 0].legend()

    ax[3, 0].plot(df['timestamp'], df['DEMA_20'], label='DEMA_20', color='#ff000080', linestyle='solid')
    ax[3, 0].plot(df['timestamp'], df['DEMA_50'], label='DEMA_50', color='#0000ff80', linestyle='-.')
    ax[3, 0].set_ylabel('DEMA')
    ax[3, 0].grid(True, linestyle='-.')
    ax[3, 0].legend()

    ax[0, 1].plot(df['timestamp'], df['close'], label='CLOSE', color='#00000080', linestyle='solid')
    ax[0, 1].plot(df['timestamp'], df['BBL_20_2.0'], label='BBL_20_2.0', color='#ff000080', linestyle='solid')
    ax[0, 1].plot(df['timestamp'], df['BBM_20_2.0'], label='BBM_20_2.0', color='#00ff0080', linestyle='solid')
    ax[0, 1].plot(df['timestamp'], df['BBU_20_2.0'], label='BBU_20_2.0', color='#0000ff80', linestyle='solid')
    ax[0, 1].set_ylabel('BOLLINGER')
    ax[0, 1].grid(True, linestyle='-.')
    ax[0, 1].legend()

    ax[1, 1].plot(df['timestamp'], df['close'], label='CLOSE', color='#0000ff80', linestyle='-.')
    ax[1, 1].plot(df['timestamp'], df['VWAP_D'], label='VWAP', color='#ff000080', linestyle='solid')
    ax[1, 1].set_ylabel('VWAP')
    ax[1, 1].grid(True, linestyle='-.')
    ax[1, 1].legend()

    ax[2, 1].plot(df['timestamp'], df['OBV'], label='OBV', color='#ff000080', linestyle='solid')
    ax[2, 1].plot(df['timestamp'], df['volume'], label='volume', color='#00ff0080', linestyle='solid')
    ax[2, 1].set_ylabel('OBV')
    ax[2, 1].grid(True, linestyle='-.')
    ax[2, 1].legend()

    ax[3, 1].plot(df['timestamp'], df['STOCHk_14_3_3'], label='k', color='#ff000080', linestyle='solid')
    ax[3, 1].plot(df['timestamp'], df['STOCHd_14_3_3'], label='d', color='#0000ff80', linestyle='-.')
    ax[3, 1].set_ylabel('STOCH')
    ax[3, 1].grid(True, linestyle='-.')
    ax[3, 1].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()

analyzeSymbol(symbols[0])
