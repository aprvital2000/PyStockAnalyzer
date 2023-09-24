import os
import os.path
import time
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta

plt.style.use('default')

# Vital
api_key = 'RUUKVAG9C6D2ECAL'

# Vishnu
# api_key = 'EE45PHWQN0W27PS1'

plot_chart = False
print_result = False
write_to_file = True
purge_files_after_days = 1

data_truncate_days = 300

output_size = 'full'  # default - compact 100 days data only
data_type = 'csv'  # default - json

file_dir = os.getcwd()
dest_csv_file_url = '{}/{}-enriched-{}.csv'
src_csv_file_url = '{}/{}-{}.csv'

api_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&apikey={}&symbol={}&outputsize={}&datatype={}'

pd.set_option("display.max_columns", None)  # show all columns


def analyze_symbols():
    symbols_df = pd.read_json('securities.json')
    symbols_df.sort_values(by=['ticker'], ascending=True, inplace=True)
    for symbol in symbols_df['ticker']:
        analyze_symbol(symbol)
        time.sleep(10)


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

    df.ta.bbands(close='close', length=20, std=2, signal_indicators=True, append=True)
    df.ta.macd(close='close', signal_indicators=True, append=True)
    df.ta.roc(close='close', append=True)
    df.ta.rsi(close='close', signal_indicators=True, append=True)
    df.ta.stc(close='close', append=True)

    df.ta.stoch(close='close', signal_indicators=True, append=True)
    xsignal = ta.cross(df['STOCHk_14_3_3'], df['STOCHd_14_3_3'])
    df['STOCHk_14_3_3_XA'] = xsignal
    xsignal = ta.cross(df['STOCHd_14_3_3'], df['STOCHk_14_3_3'])
    df['STOCHk_14_3_3_XB'] = xsignal

    df.ta.vwap(high='high', low='low', close='close', volume='volume', append=True)
    df.ta.adx(high='high', low='low', close='close', signal_indicators=True, append=True)
    df.ta.obv(close='close', volume='volume', append=True)
    df.ta.cci(high='high', low='low', close='close', append=True)
    df.ta.willr(high='high', low='low', close='close', append=True)
    df.ta.aroon(high='high', low='low', append=True)

    macd_reco(df)
    adx_reco(df)
    stoch_reco(df)

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

    return df


def macd_reco(df):
    # Logic To Be Verified
    # When the MACD crosses down MACDs above 0, indicates downtrend
    # When the MACD crosses up MACDs below 0, indicates uptrend
    df['macd_buy_reco'] = None
    df['macd_sell_reco'] = None
    df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['MACD_12_26_9'] < 0), 'macd_buy_reco'] = df['close']
    df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['MACD_12_26_9'] > 0), 'macd_sell_reco'] = df['close']
    return df


def adx_reco(df):
    # Logic To Be Verified
    # ADX > 25 - Strong trend (But, No Direction)
    # When the +DMI is above the -DMI, prices are moving up
    # When the -DMI is above the +DMI, prices are moving down
    df['adx_reco'] = 'No Action'
    df.loc[(df['ADX_14'] > 25) & (df['DMP_14'] > df['DMN_14']), 'adx_reco'] = 'Buy'
    df.loc[(df['ADX_14'] > 25) & (df['DMN_14'] > df['DMP_14']), 'adx_reco'] = 'Sell'


def stoch_reco(df):
    # Logic To Be Verified
    # %K <= 20, Indicates Over sold, potential reversal / bounce - Buy
    # %K >= 80, Indicates Over bought, potential reversal / pull back - Sell
    # When %K crosses above %D from below, indicates uptrend
    # When %K crosses below %D from above, indicates downtrend
    df['stoch_reco'] = 'No Action'
    df.loc[(df['STOCHk_14_3_3'] <= 20) | (df['STOCHk_14_3_3_XA'] == 1), 'stoch_reco'] = 'Buy'
    df.loc[(df['STOCHk_14_3_3'] >= 80) | (df['STOCHk_14_3_3_XB'] == 1), 'stoch_reco'] = 'Sell'


# Plot Charts
def plot_charts(df, symbol):
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(18, 8))

    # ax[3].plot(df['timestamp'], df['STC_10_12_26_0.5'], label='STC_10_12_26_0.5', color='#ff000080', linestyle='solid')
    # ax[3].plot(df['timestamp'], df['STCmacd_10_12_26_0.5'], label='STCmacd_10_12_26_0.5', color='#0000ff80', linestyle='solid')
    # ax[3].plot(df['timestamp'], df['STCstoch_10_12_26_0.5'], label='STCstoch_10_12_26_0.5', color='#00ff0080', linestyle='solid')
    # ax[3].axhline(y=0, color='#00000080', label='0', linestyle='solid', lw=1)
    # ax[3].axhline(y=25, color='#00000080', label='<25 - oversold', linestyle='solid', lw=1)
    # ax[3].axhline(y=75, color='#00000080', label='>75 - overbought', linestyle='solid', lw=1)
    # ax[3].set_ylabel('STC')
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

    fig.subplots_adjust(hspace=0)
    fig.suptitle(symbol)
    # fig.supxlabel('Date')
    fig.tight_layout()

    # plt.xticks(rotation=45)
    plt.show()


def cleanup_files():
    # get a list of files present in the given folder
    list_of_files = os.listdir()
    # loop over all the files
    for i in list_of_files:
        # get the location of the file
        file_location = os.path.join(os.getcwd(), i)
        # file_time is the time when the file is modified
        file_time = os.stat(file_location).st_mtime

        # if a file is modified before N days then delete it
        if (i.endswith('.csv')) & (file_time < time.time() - 86400 * purge_files_after_days):
            print(f" Delete : {i}")
            os.remove(file_location)
