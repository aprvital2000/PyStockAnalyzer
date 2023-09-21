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

# MANAMANAT
symbols = ['MSFT', 'AAPL', 'NFLX', 'AMZN', 'META', 'ADBE', 'NVDA', 'GOOGL', 'TLSA']
data_truncate_days = 250

output_size = 'full'  # default - compact 100 days data only
data_type = 'csv'  # default - json

file_dir = '/tmp/data'
dest_csv_file_url = '{}/{}-enriched-{}.csv'
src_csv_file_url = '{}/{}-{}.csv'

api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'

pd.set_option("display.max_columns", None)  # show all columns


def analyze_symbol(symbol):
    print('Analyzing Symbol: %s' % symbol)
    src_file_path = src_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(src_file_path)

    url = src_file_path
    if not file_exists:
        url = api_url.format(api_key, symbol, output_size, data_type)
    print('Get data from URL: %s' % url)

    df = pd.read_csv(url)
    rows = df.shape[0]
    print("Got nRecords: %d" % rows)

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
    df['iMACDs_12_26_9'] = ta.sma(df['MACD_12_26_9'])
    df['iMACDh_12_26_9'] = df['MACD_12_26_9'] - df['iMACDs_12_26_9']
    df.ta.roc(close='close', append=True)

    df.ta.macd(close='close', fast=5, slow=3, signal=1, signal_indicators=True, append=True)

    df.ta.stc(close='close', append=True)
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

    df.ta.aroon(high='high', low='low', append=True)
    usignal = ta.cross_value(df['AROONOSC_14'], 0, above=True)
    dsignal = ta.cross_value(df['AROONOSC_14'], 0, above=False)
    df['AROONOSC_14_X0'] = usignal
    df['AROONOSC_14_0X'] = dsignal

    df.ta.cci(high='high', low='low', close='close', append=True)
    df.ta.willr(high='high', low='low', close='close', append=True)

    macd_reco(df)
    impulse_macd_reco(df)
    aroon_reco(df)
    rsi_reco(df)
    adx_reco(df)
    bb_reco(df)
    stoch_reco(df)
    cci_reco(df)
    willr_reco(df)

    df.sort_index(ascending=False, inplace=True)
    df.dropna(subset=['MACDs_12_26_9'], inplace=True)

    if write_to_file:
        dest_file_path = dest_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
        df.to_csv(dest_file_path, index=False)

    if print_result:
        print(df.keys())
        # print(df.to_string())

    if plot_chart:
        plot_charts(df, symbol)


def analyze_symbols():
    for symbol in symbols:
        analyze_symbol(symbol)


# TODO - Implement CCI, AROON

def macd_reco(df):
    # Logic To Be Verified
    # When the MACD crosses down MACDs above 0, indicates downtrend
    # When the MACD crosses up MACDs below 0, indicates uptrend
    df['macd_reco'] = 'No Action'
    df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['MACD_12_26_9'] < 0), 'macd_reco'] = 'Buy'
    df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['MACD_12_26_9'] > 0), 'macd_reco'] = 'Sell'
    return df


def impulse_macd_reco(df):
    # Logic To Be Verified
    # When the MACD crosses down MACDs above 0, indicates downtrend
    # When the MACD crosses up MACDs below 0, indicates uptrend
    df['imacd_reco'] = 'No Action'
    # df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['iMACDh_12_26_9'] > 0) & (df['ROC_10'] > 0), 'imacd_reco'] = 'Buy'
    # df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['iMACDh_12_26_9'] < 0) & (df['ROC_10'] < 0), 'imacd_reco'] = 'Sell'
    df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['MACDh_12_26_9'] > 0) & (df['ROC_10'] > 0), 'imacd_reco'] = 'Buy'
    df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['MACDh_12_26_9'] < 0) & (df['ROC_10'] < 0), 'imacd_reco'] = 'Sell'
    return df


def rsi_reco(df):
    # Logic To Be Verified
    # RSI <= 30, Indicates Over sold, potential reversal / bounce - Buy
    # RSI >= 70, Indicates Over bought, potential reversal / pull back - Sell
    df['rsi_reco'] = 'No Action'
    df.loc[df['RSI_14'] <= 30, 'rsi_reco'] = 'Sell'
    df.loc[df['RSI_14'] >= 70, 'rsi_reco'] = 'Buy'


def adx_reco(df):
    # Logic To Be Verified
    # ADX > 25 - Strong trend (But, No Direction)
    # When the +DMI is above the -DMI, prices are moving up
    # When the -DMI is above the +DMI, prices are moving down
    df['adx_reco'] = 'No Action'
    df.loc[(df['ADX_14'] > 25) & (df['DMP_14'] > df['DMN_14']), 'adx_reco'] = 'Buy'
    df.loc[(df['ADX_14'] > 25) & (df['DMN_14'] > df['DMP_14']), 'adx_reco'] = 'Sell'


def bb_reco(df):
    # Logic To Be Verified
    # When the close is above the BBU, Sell
    # When the close is below the BBL, Buy
    # What is BBP?
    df['bb_reco'] = 'No Action'
    df.loc[df['close'] <= df['BBL_20_2.0'], 'bb_reco'] = 'Sell'
    df.loc[df['close'] >= df['BBU_20_2.0'], 'bb_reco'] = 'Buy'


def stoch_reco(df):
    # Logic To Be Verified
    # %K <= 20, Indicates Over sold, potential reversal / bounce - Buy
    # %K >= 80, Indicates Over bought, potential reversal / pull back - Sell
    # When %K crosses above %D from below, indicates uptrend
    # When %K crosses below %D from above, indicates downtrend
    df['stoch_reco'] = 'No Action'
    df.loc[(df['STOCHk_14_3_3'] <= 20) | (df['STOCHk_14_3_3_XA'] == 1), 'stoch_reco'] = 'Buy'
    df.loc[(df['STOCHk_14_3_3'] >= 80) | (df['STOCHk_14_3_3_XB'] == 1), 'stoch_reco'] = 'Sell'


def aroon_reco(df):
    # Logic To Be Verified - AROONOSC_14
    # AROONU_14 crossing above AROOND_14 can be a signal to buy
    # AROOND_14 crossing below AROONU_14 may be a signal to sell.
    df['aroon_reco'] = 'No Action'
    df.loc[df['AROONOSC_14_X0'] == 1, 'aroon_reco'] = 'Buy'
    df.loc[df['AROONOSC_14_0X'] == 1, 'aroon_reco'] = 'Sell'


def cci_reco(df):
    # Logic To Be Verified - CCI_14_0.015
    # CCI_14_0.015 < -100 can be over sold a signal to buy
    # CCI_14_0.015 > 100 can be over bought a signal to sell
    df['cci_reco'] = 'No Action'
    df.loc[df['CCI_14_0.015'] <= -100, 'cci_reco'] = 'Buy'
    df.loc[df['CCI_14_0.015'] >= 100, 'cci_reco'] = 'Sell'


def willr_reco(df):
    # Logic To Be Verified - WILLR_14
    # WILLR_14 < -80 can be over sold a signal to buy
    # WILLR_14 > -20 can be over bought a signal to sell
    df['willr_reco'] = 'No Action'
    df.loc[df['WILLR_14'] <= -80, 'willr_reco'] = 'Buy'
    df.loc[df['WILLR_14'] >= -20, 'willr_reco'] = 'Sell'


# Plot Charts
def plot_charts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(18, 8))

    ax[0].plot(df['timestamp'], df['close'], label='CLOSE', color='#0000ff80', linestyle='solid')
    ax[0].set_ylabel('CLOSE')
    ax[0].grid(True, linestyle='-.')
    ax[0].legend()

    ax[1].plot(df['timestamp'], df['MACD_12_26_9'], label='MACD', color='#ff000080', linestyle='solid')
    ax[1].plot(df['timestamp'], df['MACDs_12_26_9'], label='MACDs', color='#0000ff80', linestyle='solid')
    ax[1].axhline(y=0, color='#00ff0080', label='0', linestyle='solid', lw=1)
    ax[1].set_ylabel('MACD_12_26_9')
    ax[1].grid(True, linestyle='-.')
    ax[1].legend()

    ax[2].plot(df['timestamp'], df['AROONOSC_14'], label='AROONOSC_14', color='#0000ff80', linestyle='solid')
    ax[2].axhline(y=0, color='#ff000080', label='0', linestyle='solid', lw=1)
    ax[2].set_ylabel('AROON')
    ax[2].grid(True, linestyle='-.')
    ax[2].legend()

    ax[3].plot(df['timestamp'], df['ROC_10'], label='ROC_10', color='#0000ff80', linestyle='solid')
    ax[3].axhline(y=0, color='#00ff0080', label='0', linestyle='solid', lw=1)
    ax[3].set_ylabel('ROC')
    ax[3].grid(True, linestyle='-.')
    ax[3].legend()

    # ax[3].plot(df['timestamp'], df['STC_10_12_26_0.5'], label='STC_10_12_26_0.5', color='#ff000080', linestyle='solid')
    # ax[3].plot(df['timestamp'], df['STCmacd_10_12_26_0.5'], label='STCmacd_10_12_26_0.5', color='#0000ff80', linestyle='solid')
    # ax[3].plot(df['timestamp'], df['STCstoch_10_12_26_0.5'], label='STCstoch_10_12_26_0.5', color='#00ff0080', linestyle='solid')
    # ax[3].axhline(y=0, color='#00000080', label='0', linestyle='solid', lw=1)
    # ax[3].axhline(y=25, color='#00000080', label='<25 - oversold', linestyle='solid', lw=1)
    # ax[3].axhline(y=75, color='#00000080', label='>75 - overbought', linestyle='solid', lw=1)
    # ax[3].set_ylabel('STC')
    # ax[3].grid(True, linestyle='-.')
    # ax[3].legend()

    # ax[3].fill_between(df['timestamp'], df['RSI_14'], label='RSI', color='lightsteelblue', linestyle='solid')
    # ax[3].axhline(y=30, color='#00ff0080', label='30%', linestyle='dotted', lw=1)
    # ax[3].axhline(y=50, color='#0000ff80', label='50%', linestyle='dotted', lw=1)
    # ax[3].axhline(y=70, color='#ff000080', label='70%', linestyle='dotted', lw=1)
    # ax[3].set_ylabel('RSI')
    # ax[3].grid(True, linestyle='-.')
    # ax[3].legend()

    # ax[4].plot(df['timestamp'], df['DMP_14'], label='+di', color='#ff000080', linestyle='solid')
    # ax[4].plot(df['timestamp'], df['ADX_14'], label='ADX', color='#00ff0080', linestyle='solid')
    # ax[4].plot(df['timestamp'], df['DMN_14'], label='-di', color='#0000ff80', linestyle='solid')
    # ax[4].axhline(y=25, color='#00000080', label='25', linestyle='dotted', lw=1)
    # ax[4].set_ylabel('ADX')
    # ax[4].grid(True, linestyle='-.')
    # ax[4].legend()

    # ax[5].plot(df['timestamp'], df['STOCHk_14_3_3'], label='k', color='#ff000080', linestyle='solid')
    # ax[5].plot(df['timestamp'], df['STOCHd_14_3_3'], label='d', color='#0000ff80', linestyle='solid')
    # ax[5].set_ylabel('STOCH')
    # ax[5].grid(True, linestyle='-.')
    # ax[5].legend()

    # ax[6].plot(df['timestamp'], df['close'], label='CLOSE', color='#00ff0080', linestyle='solid')
    # ax[6].plot(df['timestamp'], df['BBL_20_2.0'], label='BBL_20_2.0', color='#ff000080', linestyle='solid')
    # ax[6].plot(df['timestamp'], df['BBU_20_2.0'], label='BBU_20_2.0', color='#0000ff80', linestyle='solid')
    # ax[6].set_ylabel('BOLLINGER')
    # ax[6].grid(True, linestyle='-.')
    # ax[6].legend()

    # ax[8].plot(df['timestamp'], df['CCI_14_0.015'], label='CCI_14_0.015', color='#0000ff80', linestyle='solid')
    # ax[8].axhline(y=0, color='#ff000080', label='0', linestyle='solid', lw=1)
    # ax[8].set_ylabel('CCI')
    # ax[8].grid(True, linestyle='-.')
    # ax[8].legend()

    # ax[9].plot(df['timestamp'], df['WILLR_14'], label='WILLR_14', color='#0000ff80', linestyle='solid')
    # ax[9].axhline(y=-20, color='#ff000080', label='0', linestyle='solid', lw=1)
    # ax[9].axhline(y=-80, color='#ff000080', label='0', linestyle='solid', lw=1)
    # ax[9].set_ylabel('WILLR')
    # ax[9].grid(True, linestyle='-.')
    # ax[9].legend()

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()


analyze_symbol(symbols[0])
