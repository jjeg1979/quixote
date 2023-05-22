from collections import Counter
from typing import Tuple, Any

import numpy as np
import pandas as pd
import datetime as dt

from sklearn.linear_model import LinearRegression


def calculate_pf(df: pd.DataFrame, pips_mode=True) -> float:
    column = 'Pips' if pips_mode else 'Profit'
    profit = df[df[column] > 0][column].sum()
    loss = -df[df[column] < 0][column].sum()
    return profit / loss if loss > 0 else np.inf()


def drawdown(df: pd.DataFrame, pips_mode=True) -> pd.Series:
    column = 'Pips' if pips_mode else 'Profit'
    return df[column].cumsum() - df[column].cumsum().cummax()


def stagnation_period(df: pd.DataFrame, mode_pips=True) -> list:        
    dd = drawdown(df, mode_pips).to_list()
    stagnation = [df['Close Time'].iloc[dd.index(d)] for d in dd if d != 0]

    durations = pd.Series(stagnation).diff().to_list()

    # Need to remove first value (NaT)
    return durations[1:]


def dd2(df: pd.DataFrame, pips_mode=True) -> np.array:
    df = df['Pips'] if pips_mode is True else df['Profit']
    d, dd_actual = [], 0

    for p in df:
        dd_actual -= p
        if p < 0:
            dd_actual = 0
        d.append(dd_actual)

    return np.array(d)


def esp(df: pd.DataFrame, pips_mode=True) -> float:
    return df['Pips'].mean() if pips_mode is True else df['Profit'].mean()


def exposures(df: pd.DataFrame) -> list:
    exp = []
    for index, op in df.iterrows():
        open_time = op['Open Time']
        close_time = op['Close Time']
        ops = df[(df['Open Time'] >= open_time) & (df['Close Time'] <= close_time)]
        exp.append(ops.shape[0])
    return exp


def get_strikes(df: pd.DataFrame, pips_mode=True) -> dict:
    """
    This method returns a Counter object where the positive and negative
    strikes are shown.
    """
    
    column = 'Pips' if pips_mode else 'Profit'
    df['Strike Type'] = np.where(df[column] > 0, 1, -1)
    strikes = {1: [], -1: []}
    counter = 0
    for idx in range(1, df.shape[0]):
        if df['Strike Type'].iloc[idx] == df['Strike Type'].iloc[idx - 1]:
            counter += 1
        else:
            if df['Strike Type'].iloc[idx - 1] == 1:
                # Changed from winning strike to losing strike
                strikes[1].append(counter)
            elif df['Strike Type'].iloc[idx - 1] == -1:
                # Changed from losing strike to winning strike
                strikes[-1].append(counter)
            counter = 1
    return {1: Counter(strikes[1]), -1: Counter(strikes[-1])}


def get_max_losing_strike(strikes: dict) -> int:
    return max(strikes[-1].keys())


def get_max_winning_strike(strikes: dict) -> int:
    return max(strikes[1].keys())


def get_avg_losing_strike(strikes: dict) -> float:
    pairs = zip(strikes[-1].keys(), strikes[1].values())
    average = sum(pair[0] * pair[1] for pair in pairs)
    return average / sum(strikes[-1].values())


def get_avg_winning_strike(strikes: dict) -> float:
    pairs = zip(strikes[1].keys(), strikes[1].values())
    average = sum(pair[0] * pair[1] for pair in pairs)
    return average / sum(strikes[1].values())
    

def get_max_lots(df: pd.DataFrame) -> float:
    return max(df['Volume'])


def get_min_lots(df: pd.DataFrame) -> float:
    return min(df['Volume'])


def remove_overlapping_ops(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a dataframe with overlapping operations removed.
    An operation overlaps another one if and only if the former's Open Time
    and the former's Close Time is encompassed in the latter.

    This is a previous step in order to not account for duplicated time
    when calculating time in market for the backtest
    """
    indices = set(df.reset_index(drop=True).index)
    for idx in indices:
        open_time = df['Open Time'].iloc[idx]
        close_time = df['Close Time'].iloc[idx]
        duplicated_idx = set(df[(df['Open Time'] >= open_time) & (df['Close Time'] <= close_time)].index)
        # breakpoint()
        if len(duplicated_idx) > 1:
            indices = indices.difference(duplicated_idx)

    return df.iloc[list(indices)]


def calculate_time_in_market(df: pd.DataFrame) -> Tuple[Any, Any, Any, Any]:      
    df_clean = df
    indices = set(df_clean.reset_index(drop=True).index)
    total_time = df_clean.iloc[0]['Duration']
    for idx in range(1,df_clean.shape[0]):
        if df_clean['Open Time'].iloc[idx] < df_clean['Close Time'].iloc[idx-1]:
            added_time = df_clean['Close Time'].iloc[idx] - df_clean['Close Time'].iloc[idx-1]
            total_time += added_time
        else:
            total_time += df_clean['Duration'].iloc[idx]

    days = total_time.days
    hours = (total_time - dt.timedelta(days=days)).seconds // 3600
    minutes = (total_time - dt.timedelta(days=days, hours=hours)).seconds//60
    seconds = (total_time-dt.timedelta(days=days, hours=hours, minutes=minutes)).seconds

    return days, hours, minutes, seconds


def pct_winner(df: pd.DataFrame, pips_mode=True) -> float:
    """
    pips_mode: To ensure only > 0 ops with Profit are considered
    """
    column = 'Pips' if pips_mode else 'Profit'
    return df[df[column] > 0].shape[0] / df.shape[0] * 100
    

def pct_losser(df: pd.DataFrame, pips_mode=True) -> float:
    return pct_winner(df, pips_mode)


def calculate_closing_days(df: pd.DataFrame) -> int:
    """
    Calculates the number of different days where an order has been closed
    """
    years = pd.DatetimeIndex(df['Close Time']).year.values.tolist()
    months = pd.DatetimeIndex(df['Close Time']).month.values.tolist()
    days = pd.DatetimeIndex(df['Close Time']).day.values.tolist()
    dates = zip(years, months, days)
    dates = set(dates)
    return len(dates)


def calculate_sqn(df: pd.DataFrame, pips_mode=True) -> float:
    if pips_mode:
        return df['Pips'].mean()/(df['Pips'].std()/(df.shape[0] ** 0.5))
    else:
        return df['Profit'].mean()/(df['Profit'].std()/(df.shape[0] ** 0.5))


def calculate_sharpe(df: pd.DataFrame, pips_mode=True) -> float:
    return calculate_sqn(df, pips_mode) * (df.shape[0] ** 0.5)


def best_operation(df: pd.DataFrame, pips_mode=True) -> tuple[Any, Any]:
    if pips_mode:
        column = 'Pips'
        factor = 10
    else:
        column = 'Profit'
        factor = 1
    return df[column].max() * factor, df.iloc[df[column].idxmax()]['Close Time']


def worst_operation(df: pd.DataFrame, pips_mode=True) -> tuple[Any, Any]:
    if pips_mode:
        column = 'Pips'
        factor = 1
    else:
        column = 'Profit'
        factor = 10
        
    return df[column].min() * factor, df.iloc[df[column].idxmin()]['Close Time']


def calculate_avg_win(df: pd.DataFrame, pips_mode=True) -> int:
    column = 'Pips' if pips_mode else 'Profit'
    ganancia = df[df[column] >= 0][column].mean()
    return int(np.round(ganancia, 0))


def calculate_avg_loss(df: pd.DataFrame, pips_mode=True) -> int:
    column = 'Pips' if pips_mode else 'Profit'
    perdida = df[df[column] < 0][column].mean()
    return int(np.round(perdida, 0))


def calculate_total_time(df: pd.DataFrame) -> dt.timedelta:
    inicio = df['Open Time'].iloc[0]
    fin = df['Close Time'].iloc[-1]
    return (fin - inicio)


def gross_profit(df: pd.DataFrame, pips_mode=True) -> int:
    column = 'Pips' if pips_mode else 'Profit'
    return df[df[column] >= 0][column].sum()


def gross_loss(df: pd.DataFrame, pips_mode=True) -> int:
    column = 'Pips' if pips_mode else 'Profit'
    return df[df[column] < 0][column].sum()


def _eqm(df: pd.DataFrame, pips_mode=True) -> Tuple[Any, Any, Any]:
    column = 'Pips' if pips_mode else 'Profit'
    x = df.reset_index().index.values.reshape(-1, 1)
    y = df[column].cumsum()

    xhat = np.mean(x)
    yhat = np.mean(y)
    n = x.flatten().size
    xdev = np.sum(np.square(x - xhat))
    ydev = np.sum(np.square(y - yhat))
    xydev = np.square(np.sum((x.flatten() - xhat) * (y - yhat)))
    error = np.sqrt(np.around((ydev - xydev / xdev) / (len(x) - 2), decimals=8)) / np.sqrt(xdev)

    return x, y, error


def kratio(df: pd.DataFrame, pips_mode=True) -> float:
    x, y, error = _eqm(df, pips_mode)
    model = LinearRegression().fit(x, y)
    return model.coef_[0] / (error * len(x))

