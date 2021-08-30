import pandas as pd 
import numpy as np 

from tqdm import tqdm

def get_daily_strangle(options, ETF, dev=0.04):
    
    
    # helper function
    def helper(date, daily):
        pos = []
        spot = ETF.loc[date, 'close']
        expires = daily['exp_date'].unique()
        for exp_date in expires:
            df = daily[daily['exp_date'] == exp_date].reset_index(drop=True)
            
            call_strike = df.loc[np.argmin(abs(df['strike'] - spot * (1+dev))), 'strike']
            put_strike = df.loc[np.argmin(abs(df['strike'] - spot * (1-dev))), 'strike']

            call = df[(df['type'] == 'CALL') & (df['strike'] == call_strike)].to_dict(orient='records')
            put = df[(df['type'] == 'PUT') & (df['strike'] == put_strike)].to_dict(orient='records')

            pos += call + put

        return pos

    security_selected = []
    for date in tqdm(options['trade_date'].unique()):
        daily = options[options['trade_date'] == date].reset_index(drop=True)
        security_selected += helper(date=date, daily=daily)
        
    return pd.DataFrame(security_selected)
