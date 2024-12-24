
import pandas as pd
import numpy as np
import statsmodels.api as sm
from joblib import Parallel, delayed
from tqdm import tqdm

def calculate_residual_volatility(data, lookback_period=60, n_jobs=-1):
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['PERMNO', 'date']).reset_index(drop=True)
    data['RET'] = pd.to_numeric(data['RET'], errors='coerce')
    data['rf'] = pd.to_numeric(data['rf'], errors='coerce')
    data['mktrf'] = pd.to_numeric(data['mktrf'], errors='coerce')
    data['RET_excess'] = data['RET'] - data['rf']

    def compute_stock_residual_volatility(stock_data):
        stock_data = stock_data.set_index('date').sort_index()
        X = sm.add_constant(stock_data['mktrf'])
        rolling_resid_std = stock_data['RET_excess'].rolling(window=lookback_period, min_periods=lookback_period).apply(
            lambda y: np.std(sm.OLS(y, X.loc[y.index]).fit().resid) if len(y.dropna()) == lookback_period else np.nan,
            raw=False
        )
        return pd.DataFrame({'date': stock_data.index, 'PERMNO': stock_data['PERMNO'].iloc[0], 'residual_vol': rolling_resid_std})

    results = Parallel(n_jobs=n_jobs)(delayed(compute_stock_residual_volatility)(group) for _, group in tqdm(data.groupby('PERMNO')))
    residual_vol = pd.concat(results).dropna(subset=['residual_vol']).reset_index(drop=True)
    return residual_vol
