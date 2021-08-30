import os 
import scipy.io

import pandas as pd 
import numpy as np 

from datetime import datetime


def prepare_options_price_data_from_op510050(filepath=None, raw1=None, raw2=None, save=False, save_filepath=''):
    """
    If filepath is provided, read the data directly from filepath. 
    If filepath is not provided, construct options data using Op510050_1 and Op510050_2
    """
    if filepath is not None:
        options = pd.read_csv(filepath)
        options['datetime'] = pd.to_datetime(options['datetime'])
        options.set_index('datetime', inplace=True)
        options['sec_code'] = options['sec_code'].astype(str)
        
        return options
    
    if (raw1 is None) or (raw2 is None):
        raise Exception('')
      
    file_list1 = [filename for filename in os.listdir(raw1) if True ^ filename.startswith('.')]
    file_list2 = [filename for filename in os.listdir(raw2) if True ^ filename.startswith('.')]
    
    def process_options_minute_level_data(data: pd.DataFrame, code: str) -> pd.DataFrame:
        columns_to_drop = ['datetime_nano']

        # datetime processing 
        data['datetime'] = pd.to_datetime(data['datetime'])

        # rename columns
        data.rename(columns={
            col: col.split('.')[-1] 
            for col in data.columns[1:]
        }, inplace=True)


        data.drop(columns_to_drop, axis=1, inplace=True)

        # add code 
        data.insert(0, 'code', code)

        return data
    
    data_list = [
        process_options_minute_level_data(pd.read_csv(os.path.join(folder1, filename)), filename.split('.')[1][:-4])
        for filename in file_list1
    ]

    data_list += [
        process_options_minute_level_data(pd.read_csv(os.path.join(folder2, filename)), filename.split('.')[1][:-4])
        for filename in file_list2
    ]
    
    options = pd.concat(data_list, axis=0)

    options.set_index('datetime', inplace=True)
    options.sort_index(inplace=True)
    
    options.rename(columns={'code': 'sec_code'}, inplace=True)
    options['sec_code'] = options['sec_code'].astype(str)
    
    if save:
        options.to_csv(save_filepath)
        
    return options


def resample_options_data(data, freq='1D'):
    resample_obj = data.groupby('sec_code').resample(freq)
    
    open_ = resample_obj.open.first()
    high_ = resample_obj.high.max()
    low_ = resample_obj.low.min()
    close_ = resample_obj.close.last()
    volume_ = resample_obj.volume.sum()
    open_oi_ = resample_obj.open_oi.sum()
    close_oi_ = resample_obj.close_oi.sum()

    resampled_data = pd.concat([open_, high_, low_, close_, volume_, open_oi_, close_oi_], axis=1).reset_index()

    # fillna, TODO
    resampled_data.fillna(method='ffill', inplace=True)
    
    # reset index
    resampled_data.set_index('datetime', inplace=True)
    
    return resampled_data


def read_options_data(direc) -> dict:
    mat = scipy.io.loadmat(direc)

    C = mat['Contract'].flatten()[0][0]
    ETF = mat['Contract'].flatten()[0][1]
    IH = mat['Contract'].flatten()[0][2]

    dates = [C[idx][0][0] for idx in range(C.shape[0])]

    # complete options data
    full = get_full_options_data(C, dates)

    # ETF
    ETF = pd.DataFrame(
        ETF, 
        index=pd.to_datetime(np.array(dates)), 
        columns=['open', 'high', 'low', 'close', 'adj_close']
    )

    return {
        'options': full, 
        'ETF': ETF, 
        'IH': IH
    }


def get_full_options_data(arr: np.array, dates: list):
    book_list = [get_daily_options_book(arr[idx], dates[idx]) for idx in range(len(dates))]
    
    options_book = pd.concat(book_list, axis=0)

    options_book['code'] = options_book['code'].str.slice(0, -3)
    
    return options_book


def get_daily_options_book(arr: np.array, date: str) -> pd.DataFrame:
    book_idx_list = [5, 6, 9, 10, 13, 14, 17, 18]

    # helper functions
    def helper_tabular_option(arr):
        new_arr = np.empty(arr.shape, dtype='object')
        for ridx in range(arr.shape[0]):
            for cidx in range(arr.shape[1]):
                new_arr[ridx, cidx] = arr[ridx][cidx].flatten()[0]
        return new_arr
    
    df_list = []
    for idx in book_idx_list:
        df_list += [pd.DataFrame(helper_tabular_option(arr[idx]), columns=['code', 'name', 'strike', 'date', 'exp_date'])]
    
    options_book = pd.concat(df_list, axis=0)
    options_book['exp_date'] = [str(date).replace('/', '-') for date in options_book['exp_date']]
    options_book['date'] = [str(date).replace('/', '-') for date in options_book['date']]
    options_book.insert(0, 'trade_date', [date.replace('/', '-') for i in range(options_book.shape[0])])
    options_book.insert(options_book.shape[1], 'time_to_exp', pd.to_datetime(options_book['exp_date']) - pd.to_datetime(options_book['trade_date']))
    
    # clean 
    options_book.drop_duplicates(inplace=True)
    
    # 
    type_list = [None] * options_book.shape[0]
    for idx, item in enumerate(options_book['name']):
        if item[5] == '购':
            type_list[idx] = 'CALL'
        else:
            type_list[idx] = 'PUT'
    options_book.insert(3, 'type', type_list)
    
    return options_book
