import pandas as pd 
import numpy as np 

def get_daily_strangle(date, options_book, ETF, dev=0.04):
    pos = []
    expires = options_book['exp_date'].unique()
    
    spot = ETF.loc[date, 'close']
    
    for exp_date in expires:
        df = options_book[options_book['exp_date'] == exp_date].reset_index(drop=True)
    
        call_strike = df.loc[np.argmin(abs(df['strike'] - spot * (1+dev))), 'strike']
        put_strike = df.loc[np.argmin(abs(df['strike'] - spot * (1-dev))), 'strike']

        call = df[(df['type'] == 'CALL') & (df['strike'] == call_strike)].to_dict(orient='records')
        put = df[(df['type'] == 'PUT') & (df['strike'] == put_strike)].to_dict(orient='records')

        pos += call + put
    
    return pos