import os
import json
import warnings
import pandas as pd 
import numpy as np 


def prepare_sample_data(price_direc: str, portfolio_direc: str) -> dict:
    return read_sample_data(price_direc=price_direc, portfolio_direc=portfolio_direc)


def read_wrds_options_data(ticker, directory, col_renames=None):
    """
    Reads in and cleans csv file for each path in paths,
    where each element of paths is a path leading to a 
    csv in the WRDS format for options data.

    Args:
        paths (list): list of paths to WRDS options data to read/clean
        col_replacements (None, optional): Description

    Returns:
        pandas dataframe: cleaned dataframes concatenated 

    """
    full = pd.DataFrame()
    files = os.listdir(directory)
    valid_files = [file for file in files if ((os.path.splitext(file)[1] == '.txt') and (ticker in file))]
    paths = [directory + '/' + file for file in valid_files]
    
    print('valid files: ', valid_files)
    for path in paths:
        df = pd.read_csv(path, delimiter=' ')
        full = pd.concat([full, df])
    # print(full.columns)
    full.date = pd.to_datetime(full.date, format="%Y-%m-%d")
    full.exdate = pd.to_datetime(full.exdate, format="%Y-%m-%d")
    full.last_date = pd.to_datetime(full.last_date, format="%Y-%m-%d")

    full['ticker'] = full.symbol.str.split().str[0]

    if col_renames is None: 
        col_renames = {"contract_size": "contractSize",
                       "impl_volatility": "vol",
                       "best_bid": "bid",
                       "best_offer": "ask",
                       "cp_flag": "type",
                       "open_interest": "oi",
                       "strike_price": "strike",
                       "symbol": "full_ticker",
                       "ticker": "symbol"
                       }

    full.rename(col_renames, axis='columns', inplace=True)
    full['type'].replace({"C": "CALL", "P": "PUT"}, inplace=True)
    full['px_mid'] = (full.ask + full.bid)/2
    full.drop(['root', 'suffix', 'expiry_indicator'], axis=1, inplace=True)

    # print(full)

    return full


def read_alternative_options_data(ticker, directory, verbose=1):
    """Reads in the options data whose text files
    are specified in datapaths.

    Data format is specific to the set found in the 
    github samples.

    Args:
        datapaths (list): paths to text files

    Returns:
        DataFrame: concatenated dataframe containing
        all data from files in datapaths. 
    """
    all_dfs = []
    files = os.listdir(directory + ticker)
    valid_files = [file for file in files if os.path.splitext(file)[1] == '.txt']

    paths = [directory + ticker + '/' + file for file in valid_files if not file.startswith('.')]
    if verbose > 0:
        print('paths: ', paths)
    for path in paths:
        try:
            f = open(path)
            lines = f.readlines(1)[0]
            dic = json.loads(lines)
        except IndexError:
            warnings.warn("%s is empty. Skipping..." % path) 
            continue
        except json.decoder.JSONDecodeError:
            raise ValueError("Something wrong with file %s" % path) 
        # get the date from the filename
        date = path.split('.txt')[0][-6:]
        date = pd.to_datetime(date, format="%y%m%d")

        # top level variables:
        code = dic['code']
        exchange = dic['exchange']
        lastTradeDate = dic['lastTradeDate']
        lastTradePrice = dic['lastTradePrice']
        df_lst = []

        # handle elements in dic['data']
        for i in range(len(dic['data'])):
            row = dic['data'][i]
            try:
                calls = pd.json_normalize(row['options']['CALL'])
            except KeyError:
                calls = pd.DataFrame()

            try: 
                puts = pd.json_normalize(row['options']['PUT'])

            except KeyError:
                puts = pd.DataFrame() 
            df = pd.concat([calls, puts])
            df_lst.append(df)

        pathdf = pd.concat(df_lst) 
        pathdf['date'] = date 
        pathdf['code'] = code
        pathdf['exchange'] = exchange
        pathdf['lastTradeDate'] = lastTradeDate 
        pathdf['lastTradePrice'] = lastTradePrice 
        all_dfs.append(pathdf)

    full = pd.concat(all_dfs).reset_index(drop=True)

    # standardizing names across dataframes 
    names = {"contractName": "symbol",
             "impliedVolatility": "vol",
             "openInterest": "oi", 
             "theoretical": "px_mid",
             "expirationDate": "exdate"}

    full.rename(names, axis='columns', inplace=True)
    full.exdate = pd.to_datetime(full.exdate)
    full.lastTradeDate = pd.to_datetime(full.lastTradeDate)

    # replace full symbol with ticker. 
    full.symbol = full.symbol.str[:4]

    return full


def read_sample_data(price_direc: str, portfolio_direc: str) -> dict:
    # historical data
    daily_price = pd.read_csv(os.path.join(price_direc), parse_dates=['datetime'])
    daily_price.set_index('datetime', inplace=True)

    # portfolio information
    trade_info = pd.read_csv(os.path.join(portfolio_direc), parse_dates=['trade_date'])
    
    return {
        'price': daily_price, 
        'portfolio': trade_info
    }

