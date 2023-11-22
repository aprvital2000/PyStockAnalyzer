import os
import os.path
import time
from datetime import date

import pandas as pd
import pandas_ta as ta

print_result = False
print_reco = True
write_to_file = True
print_debug = False
purge_files_after_days = 1
decision_truncate_days = 5

file_dir = os.getcwd() + '/data'
dest_csv_file_url = '{}/{}-enriched-{}.csv'
src_csv_file_url = '{}/{}-{}.csv'

pd.set_option("display.max_columns", None)  # show all columns


def analyze_symbols():
    symbols_df = pd.read_json('securities.json')
    symbols_df.sort_values(by=['ticker'], ascending=True, inplace=True)
    for symbol in symbols_df['ticker']:
        analyze_symbol(symbol)


def analyze_symbol(symbol):
    if print_debug: print('Analyzing Symbol: %s' % symbol)
    src_file_path = src_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
    file_exists = os.path.isfile(src_file_path)

    url = src_file_path
    df = pd.DataFrame()

    if not file_exists:
        df = df.ta.ticker(symbol, period="12mo", interval="1d")
        df.drop(['Dividends', 'Stock Splits'], inplace=True, axis=1)
        df.reset_index(inplace=True)
    else:
        df = pd.read_csv(url)
        if print_debug: print('Get data from URL: %s' % url)

    df.set_index('Date')
    rows = df.shape[0]
    if print_debug: print("Got nRecords: %d" % rows)

    if rows < decision_truncate_days:
        print('Error getting data from URL: %s' % url)
        return

    if not file_exists: df.to_csv(src_file_path, index=False)
    df.sort_index(ascending=True, inplace=True)

    df.ta.bbands(close='Close', length=20, std=2, signal_indicators=True, append=True)
    df['bb_reco'] = df.apply(lambda row: bb_reco(row), axis=1)

    df.ta.macd(close='Close', signal_indicators=True, append=True)
    macd_reco(df)
    df['macd_reco'] = df.apply(lambda row: macd_reco2(row), axis=1)

    df.ta.roc(close='Close', append=True)
    upward_signal = ta.cross_value(df['ROC_10'], 0, above=True)
    df['ROC_10_XU0'] = upward_signal
    downward_signal = ta.cross_value(df['ROC_10'], 0, above=False)
    df['ROC_10_XD0'] = downward_signal
    df['roc_reco'] = df.apply(lambda row: roc_reco(row), axis=1)

    df.ta.rsi(close='Close', signal_indicators=True, append=True)
    df['rsi_reco'] = df.apply(lambda row: rsi_reco(row), axis=1)

    df.ta.stoch(close='Close', signal_indicators=True, append=True)
    df['stoch_reco'] = df.apply(lambda row: stoch_reco(row), axis=1)

    df.ta.aroon(high='High', low='Low', append=True)
    df['aroon_reco'] = df.apply(lambda row: aroon_reco(row), axis=1)

    df.ta.adx(high='High', low='Low', close='Close', signal_indicators=True, append=True)
    df['adx_reco'] = df.apply(lambda row: adx_reco(row), axis=1)

    # df.ta.vwap(high='High', low='Low', close='Close', volume='Volume', append=True)
    # df['vwap_reco'] = df.apply(lambda row: vwap_reco(row), axis=1)

    df.ta.obv(close='Close', volume='Volume', append=True)
    df['obv_reco'] = df.apply(lambda row: obv_reco(row), axis=1)

    df.ta.cci(high='High', low='Low', close='Close', append=True)
    df['cci_reco'] = df.apply(lambda row: cci_reco(row), axis=1)

    df.ta.willr(high='High', low='Low', close='Close', append=True)
    df['willr_reco'] = df.apply(lambda row: willr_reco(row), axis=1)

    df.ta.supertrend(high='High', low='Low', close='Close', append=True)

    df.sort_index(ascending=False, inplace=True)
    df.dropna(subset=['MACDs_12_26_9'], inplace=True)

    if write_to_file:
        dest_file_path = dest_csv_file_url.format(file_dir, symbol, date.today().strftime('%d%m%y'))
        df.to_csv(dest_file_path, index=False)

    if print_result:
        # print(df.keys())
        print(df.head()[
                  ['macd_reco', 'roc_reco', 'aroon_reco', 'rsi_reco', 'adx_reco', 'stoch_reco', 'bb_reco', 'cci_reco',
                   'willr_reco', 'vwap_reco', 'obv_reco']])

    if print_reco:
        df2 = df.head(decision_truncate_days)
        buy_reco = 'Buy' in df2['macd_reco'].unique() and 'Buy' in df2['roc_reco'].unique()  # and 'Buy' in df2['vwap_reco'].unique()
        sell_reco = 'Sell' in df2['macd_reco'].unique() and 'Sell' in df2['roc_reco'].unique()  # and 'Sell' in df2['vwap_reco'].unique()

        if buy_reco: print(f"[BUY ] --> {symbol}")
        elif sell_reco: print(f"[SELL] --> {symbol}")
        else: print(f"[N/A ] --> {symbol}")

    return df


def macd_reco2(row):
    # Logic To Be Verified
    # When the MACD crosses down MACDs above 0, indicates downtrend
    # When the MACD crosses up MACDs below 0, indicates uptrend
    if (row['MACDh_12_26_9_XA_0'] == 1) & (row['MACD_12_26_9'] < 0): return 'Buy'
    elif (row['MACDh_12_26_9_XB_0'] == 1) & (row['MACD_12_26_9'] > 0): return 'Sell'
    return None


def aroon_reco(row):
    return 'Buy' if row['AROONOSC_14'] >= 0 else 'Sell'


def roc_reco(row):
    if row['ROC_10_XU0'] == 1: return 'Buy'
    elif row['ROC_10_XD0'] == 1: return 'Sell'
    return None


def rsi_reco(row):
    if row['RSI_14'] >= 70: return 'Buy'
    elif row['RSI_14'] <= 30: return 'Sell'
    return None


def adx_reco(row):
    # Logic To Be Verified
    # ADX > 25 - Strong trend (But, No Direction)
    # When the +DMI is above the -DMI, prices are moving up
    # When the -DMI is above the +DMI, prices are moving down
    if (row['ADX_14'] > 25) & (row['DMP_14'] > row['DMN_14']): return 'Buy'
    elif (row['ADX_14'] > 25) & (row['DMP_14'] < row['DMN_14']): return 'Sell'
    return None


def macd_reco(df):
    # Logic To Be Verified
    # When the MACD crosses down MACDs above 0, indicates downtrend
    # When the MACD crosses up MACDs below 0, indicates uptrend
    df['macd_buy_reco'] = None
    df['macd_sell_reco'] = None
    df.loc[(df['MACDh_12_26_9_XA_0'] == 1) & (df['MACD_12_26_9'] < 0), 'macd_buy_reco'] = df['Close']
    df.loc[(df['MACDh_12_26_9_XB_0'] == 1) & (df['MACD_12_26_9'] > 0), 'macd_sell_reco'] = df['Close']
    return df


def stoch_reco(row):
    # Logic To Be Verified
    # %K <= 20, Indicates Over sold, potential reversal / bounce - Buy
    # %K >= 80, Indicates Over bought, potential reversal / pull back - Sell
    # When %K crosses above %D from below, indicates uptrend
    # When %K crosses below %D from above, indicates downtrend
    if (row['STOCHk_14_3_3'] <= 20) & (row['STOCHd_14_3_3'] <= 20) & (row['STOCHk_14_3_3'] >= row['STOCHd_14_3_3']): return 'Buy'
    elif (row['STOCHk_14_3_3'] >= 80) & (row['STOCHd_14_3_3'] >= 80) & (row['STOCHk_14_3_3'] <= row['STOCHd_14_3_3']): return 'Sell'
    return None


def bb_reco(row):
    if row['Close'] <= row['BBL_20_2.0']: return 'Buy'
    elif row['Close'] >= row['BBU_20_2.0']: return 'Sell'
    return None


def cci_reco(row):
    if row['CCI_14_0.015'] <= -100: return 'Buy'
    elif row['CCI_14_0.015'] >= 100: return 'Sell'
    return None


def willr_reco(row):
    if row['WILLR_14'] <= -80: return 'Buy'
    elif row['WILLR_14'] >= -20: return 'Sell'
    return None


def vwap_reco(row):
    if row['Close'] >= row['VWAP_D']: return 'Buy'
    elif row['Close'] < row['VWAP_D']: return 'Sell'
    return None


def obv_reco(row):
    if print_debug: print("Got row in OBV : %d" % row)
    return None


def cleanup_files():
    print(f" Deleting the older files in folder : {file_dir}")
    list_of_files = os.listdir(file_dir)
    for i in list_of_files:
        file_location = os.path.join(file_dir, i)
        file_time = os.stat(file_location).st_mtime
        if (i.endswith('.csv')) & (file_time < time.time() - 86400 * purge_files_after_days):
            print(f" Delete : {i}")
            os.remove(file_location)
    print(f" Completed deleting the older files in folder : {file_dir}")
