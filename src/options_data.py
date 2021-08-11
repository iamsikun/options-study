import os 
import scipy.io

import pandas as pd 
import numpy as np 

from datetime import datetime

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
    options_book.insert(0, 'asof', [date.replace('/', '-') for i in range(options_book.shape[0])])
    options_book.insert(options_book.shape[1], 'time_to_exp', pd.to_datetime(options_book['exp_date']) - pd.to_datetime(options_book['asof']))
    
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