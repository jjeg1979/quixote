# Standard library imports
import math
from collections import Counter
import datetime as dt
from datetime import timedelta
from typing import Tuple, Any, Set, List
from decimal import Decimal

# Non-standard library imports
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Project imports
from .btgenbox import BtGenbox

################################################################
# CONSTANTS AND ENUMERATIONS USED BY THIS CLASS
# INFINITE (alilas for numpy.inf)
INF = np.inf
# Set with all available metrics
ALL_METRICS = {
    'PF',
    'EP',
    'DD',
    'Stagnation Period',
    'DD2',
    'Max. Exposure',
    'Max. Losing Strike',
    'Max. Winning Strike',
    'Avg. Losing Strike',
    'Avg. Winning Strike',
    'Max. Lots',
    'Min. Lots',
    'Pct. Win',
    'Pct. Loss',
    'Closing Days',
    'SQN',
    'Sharpe',
    'Best Op',
    'Worst Op',
    'Avg Win',
    'Avg Loss',
    'Backtest Time',
    'Gross Profit',
    'Gross Loss',
    'Kratio',
    'RF',
    'Num Ops',
}
# Precision to present the metrics (decimal places)
DEC_PREC = '0.00'
# Default criteria to determine if a set is valid or not
DEFAULT_CRITERIA = {
            'Kratio':
                {
                    'Min': 0.20,
                    'Max': INF
                },
            'RF':
                {
                    'Min': 8.9,
                    'Max': INF
                },
            'Num Ops':
                {
                    'Min': 250,
                    'Max': INF
                },
            'Max. Exposure':
                {
                    'Min': 0.0,
                    'Max': 0.22
                },
            'Closing Days':
                {
                    'Min': 100,
                    'Max': INF,
                },                
        }

################################################################

class BtMetrics:
    """
    Represents a Btmetrics object. From a backtest, it calculates different metrics to characterize the
    backtest and to ensure that the

    Instance variables:
       bt (Genbox): Backtest object
    
    Instance properties:    
        * operations
        * metrics

    Instance methods:
        * selected_metrics
        * is_valid
        * calculate_pf
        * drawdown
        * stagnation_period
        * dd2
        * esp
        * exposures
        * _get_strikes
        * get_max_losing_strike
        * get_max_winning_strike
        * get_avg_losing_strike
        * get_avg_winning_strike
        * get_max_lots
        * get_min_lots
        * calculate_time_in_market
        * pct_win
        * pct_loss
        * calculate_closing_days
        * calculate_sqn
        * calculate_sharpe
        * best_operation
        * worst_operation
        * calculate_avg_win
        * calculate_avg_loss
        * calculate_total_time
        * gross_profit
        * gross_loss
        * calculate_kratio
    """

    def __init__(self, bt: BtGenbox, calc_metrics_at_init: bool = False, pips_mode: bool = True) -> None:
        """Creates and returns a Metrics object

        Args:
            bt   (BtGenbox):                Genbox Backtest Object
            calc_metrics_at_init (bool):    Calculate metrics at init or not
            pips_mode:                      Metrics calculation mode:
                                                True:   in pips terms
                                                False:  in monetary terms
        
        Returns:
            None

        TODO:   Include pips_mode as argument for the constructor in order
                to homogenize the call to the metrics functions
        """
        self.bt = bt
        self._ops = bt.operations
        self._available_metrics = self.available_metrics
        self.calc_metrics_at_init = calc_metrics_at_init
        self._pips_or_money = pips_mode
        self._metrics_functions = \
        {
            'PF': self.calculate_pf(pips_mode),
            'EP': self.esp(pips_mode),
            'DD': Decimal(self.drawdown(pips_mode).min()).quantize(Decimal(DEC_PREC)),
            'Stagnation Period': max(self.stagnation_periods(pips_mode)),
            'DD2': Decimal(self.dd2(pips_mode).min()).quantize(Decimal(DEC_PREC)),
            'Max. Exposure': max(self.exposures()[1]),
            'Max. Losing Strike': self.get_max_losing_strike(),
            'Max. Winning Strike': self.get_max_winning_strike(),
            'Avg. Losing Strike': self.get_avg_losing_strike(),
            'Avg. Winning Strike': self.get_avg_winning_strike(),
            'Max. Lots': self.get_max_lots(),
            'Min. Lots': self.get_min_lots(),
            'Time in Market': self.calculate_time_in_market(),
            'Pct. Win': self.pct_win(pips_mode),
            'Pct. Loss': self.pct_loss(pips_mode),
            'Closing Days': self.calculate_closing_days(),
            'SQN': self.calculate_sqn(pips_mode),
            'Sharpe': self.calculate_sharpe(pips_mode),
            'Best Op': self.best_operation(pips_mode),
            'Worst Op': self.worst_operation(pips_mode),
            'Avg Win': self.calculate_avg_win(pips_mode),
            'Avg Loss': self.calculate_avg_loss(pips_mode),
            'Backtest Time': self.calculate_total_time(),
            'Gross Profit': self.gross_profit(pips_mode),
            'Gross Loss': self.gross_loss(pips_mode),
            'Kratio': self.calculate_kratio(pips_mode),
            'RF' : self.calculate_rf(pips_mode),
            'Num Ops': self.num_ops,
        }
        self._all_metrics = self._calculate_all_metrics(self.pips_or_money) if calc_metrics_at_init else None

    @property
    def operations(self) -> pd.DataFrame:
        """Operations in the backtest. The data available for the operations are:
                * Open Time
                * Close Time
                * Pips
                * Profit
                * ...
            
            Args:
            
            Returns:
                (pandas.DataFrame): DataFrame with the operations
        """
        return self._ops

    @operations.setter
    def operations(self, value: pd.DataFrame) -> None:
        self._ops = value if value is pd.DataFrame else None
        
    @property
    def num_ops(self) -> int:
        return self._ops.shape[0]

    @property
    def pips_or_money(self) -> bool:
        return self._pips_or_money
    
    @pips_or_money.setter
    def pips_or_money(self, value: bool) -> None:
        self._pips_or_money = value
    
    @property
    def valid(self) -> str:
        match self.is_valid(DEFAULT_CRITERIA):
            case True:
                return 'Y'
            case False:
                return 'N'

    @property
    def all_metrics(self) -> dict:
        """ Property that returns a dict with the names of all the metrics and
            the corresponding values calculated."""
        return self._all_metrics if self._all_metrics is not None else self._calculate_all_metrics()
    
    @property
    def ratio(self) -> Decimal:
        if not self.calc_metrics_at_init:
            self._calculate_all_metrics()
            
        avg_loss = self.calculate_avg_loss(self.pips_or_money)
        avg_win = self.calculate_avg_win(self.pips_or_money) 
        ratio = math.fabs(avg_win/avg_loss) if avg_loss != 0.0 else INF
        return Decimal(ratio).quantize(Decimal(DEC_PREC))

    @property
    def available_metrics(self) -> Set[str]:
        """Property that returns a dict with the names of the metrics and the corresponding function
        in this class that calculates the metrics.

        Returns:
            (Set): Set with the following structure:
                    {'metric_name1', 
                     'metric_name2',
                     ...                     
                     }
                    For example:
                        {'PF',
                         'EP',
                         ...
                        }
        """
        # return {
        #     'PF'                  : self.calculate_pf,                  # Profit Factor
        #     'EP'                  : self.esp,                           # Expectancy
        #     'DD'                  : self.drawdown,                      # Drawdown
        #     'Stagnation Period'   : self.stagnation_periods,             
        #     'DD2'                 : self.dd2,                           
        #     'Max. Exposure'       : self.exposures,                                             
        #     'Max. Losing Strike'  : self.get_max_losing_strike,         
        #     'Max. Winning Strike' : self.get_max_winning_strike,
        #     'Avg. Losing Strike'  : self.get_avg_losing_strike,
        #     'Avg. Winning Strike' : self.get_avg_winning_strike,
        #     'Max. Lots'           : self.get_max_lots,
        #     'Min. Lots'           : self.get_min_lots,
        #     'Time in Market'      : self.calculate_time_in_market,
        #     'Pct. Win'            : self.pct_win,
        #     'Pct. Loss'           : self.pct_loss,
        #     'Closing Days'        : self.calculate_closing_days,
        #     'SQN'                 : self.calculate_sqn,
        #     'Sharpe'              : self.calculate_sharpe,
        #     'Best Op'             : self.best_operation,
        #     'Worst Op'            : self.worst_operation,
        #     'Avg Win'             : self.calculate_avg_win,
        #     'Avg Loss'            : self.calculate_avg_loss,
        #     'Backtest Time'       : self.calculate_total_time,             # Total time for the bactest
        #     'Gross Profit'        : self.gross_profit,
        #     'Gross Loss'          : self.gross_loss,
        #     'Kratio'              : self.calculate_kratio,
        #     'RF'                  : self.calculate-rf,
        # }
        return ALL_METRICS
    
    def _calculate_one_metric(self, metric_name: str) -> Any:
        """ Calculates the value for metric_name. 
            It has to be one valid metric_name (i.e. already known by BtMetrics class)
            
        Args:
            metric_name:    String with the metric name
            
        Returns:
            (Any):  Depending on the demanded metric (Decimal, datetime, dict...)
        """
        if metric_name in self.available_metrics:
            return self._metrics_functions[metric_name]
        else:
            raise IndexError

    def _calculate_all_metrics(self) -> dict:
        """Method that returns a dict with the values for the matrics included in this class

        Args:
            

        Returns:
            (dict): Dictionary with the following structure:
                    {'metric_name': metric_value }
                    For example:
                        {'PF': value,
                         'EP': value,m
                         ...
                        }
        """
        pips_mode = self.pips_or_money
        
        return {
            'PF': self.calculate_pf(pips_mode),
            'EP': self.esp(pips_mode),
            'DD': Decimal(self.drawdown(pips_mode).min()).quantize(Decimal(DEC_PREC)),
            'Stagnation Period': max(self.stagnation_periods(pips_mode)),
            'DD2': Decimal(self.dd2(pips_mode).min()).quantize(Decimal(DEC_PREC)),
            'Max. Exposure': max(self.exposures()[1]),
            'Max. Losing Strike': self.get_max_losing_strike(),
            'Max. Winning Strike': self.get_max_winning_strike(),
            'Avg. Losing Strike': self.get_avg_losing_strike(),
            'Avg. Winning Strike': self.get_avg_winning_strike(),
            'Max. Lots': self.get_max_lots(),
            'Min. Lots': self.get_min_lots(),
            'Time in Market': self.calculate_time_in_market(),
            'Pct. Win': self.pct_win(pips_mode),
            'Pct. Loss': self.pct_loss(pips_mode),
            'Closing Days': self.calculate_closing_days(),
            'SQN': self.calculate_sqn(pips_mode),
            'Sharpe': self.calculate_sharpe(pips_mode),
            'Best Op': self.best_operation(pips_mode),
            'Worst Op': self.worst_operation(pips_mode),
            'Avg Win': self.calculate_avg_win(pips_mode),
            'Avg Loss': self.calculate_avg_loss(pips_mode),
            'Backtest Time': self.calculate_total_time(),
            'Gross Profit': self.gross_profit(pips_mode),
            'Gross Loss': self.gross_loss(pips_mode),
            'Kratio': self.calculate_kratio(pips_mode),
            'RF': self.calculate_rf(pips_mode),
            'Num Ops': self.num_ops,
        }

    def selected_metrics(self, selected_metrics: List[str]) -> dict:
        """Method that returns a list with the values of the selected metrics.
        
        Args:
            selected_metrics List[str]: List that contains the names of the selected metrics

        Returns:
            dict:   List with the values of the selected metrics
                    {'metric_name': metric_value }
                    For example:
                        {'PF': value,
                         'EP': value,
                         'DD2': value,
                         ...
                        }
        """
        # First check if we want to retrieve all the metrics
        if len(selected_metrics) == len(self.available_metrics):
            return self.all_metrics

        # If all metrics were calculated at init, no need to calculate them
        # again
        if self.calc_metrics_at_init:
            return {metric: self.all_metrics[metric] for \
                metric in selected_metrics}
        else:
            return {metric: self._calculate_one_metric[metric] for \
                metric in selected_metrics}

    def is_valid(self, criteria: dict) -> bool:
        """ Based on certain thresholds for some criteria determine if a 
            backtest is valid.
        
        Args:
            criteria (dict):    Dict of dicts with criteria to te applied to determine whether or not
                                a set is valid. This function supposes that the criteria is incluve, i.e.,
                                all the provided criteria must be fulfilled in order to return a True value
                                Each dict in the set contains the min and max values
                                for the criteria to be accepted. If any of the min or max values are not 
                                required, INF (infinite) value is to be provided.
                                Example:
                                {
                                    'PF':
                                        {'Min': 1.3,
                                         'Max': INF,
                                        },
                                    'Closing days':
                                        {'Min': 100,
                                         'Max': 300,
                                        },
                                    'kratio':
                                        {'Min': INF,
                                         'Max': 0.40,                                            
                                        },
                                        ....
                                }
        
        Returns:
            (bool): True or False            
        """
        if self.calc_metrics_at_init:
            metrics = self.all_metrics
        else:
            metrics = {}
            for crit in criteria:
                metrics[crit] = self._calculate_one_metric(crit)
        
        res = True
        
        for crit in criteria:
            val = metrics[crit] >= criteria[crit]['Min'] and \
                 metrics[crit] <= criteria[crit]['Max']
            res = val and res
            
        return res        

    def calculate_pf(self, pips_mode=True) -> Decimal:
        """Calculates the Profit Factor for the backtest operations

        Args:
            pips_mode (bool):   Indicates whether the results must be in Pips or 
                                in monetary terms

        Returns:
            (Decimal): Value for the Profit Factor
        """
        column = 'Pips' if pips_mode else 'Profit'
        profit = self.operations[self.operations[column] > 0][column].sum()
        loss = -self.operations[self.operations[column] < 0][column].sum()
        pf = Decimal(profit / loss) if loss > 0 else Decimal('inf')
        return pf.quantize(Decimal('0.00'))

    def drawdown(self, pips_mode=True) -> pd.Series:
        """Calculates the Drawdown 

        Args:
            pips_mode (bool): Indicates whether the results must be in Pips or in monetary terms

        Returns:
            pd.Series: Pandas series with the drawdown values
        """
        column = 'Pips' if pips_mode else 'Profit'
        return self.operations[column].cumsum() - \
               self.operations[column].cumsum().cummax()
               
    def max_dd(self, pips_mode=True, f:str='dd') -> Decimal:
        """Calculates the max drawdown in absolute value
        
        Args:
            pips_mode (bool): Indicates whether the results must be in Pips or in monetary terms
            f (str): Indicates which function to use for the drawdown series
            
        Returns:
            Decimal: value with the maximum drawdown                        
        """
        match f:
            case 'dd':
                return Decimal(self.drawdown(pips_mode).min()).quantize(Decimal(DEC_PREC))
            case 'dd2':
                return Decimal(self.dd2(pips_mode).min()).quantize(Decimal(DEC_PREC))
       
    def stagnation_periods(self, pips_mode=True) -> List[timedelta]:
        """Calculates the periods where the balance curve is not increasing 

        Args:
            pips_mode (bool):   Indicates whether the results must be in Pips
                                or in monetary terms

        Returns:
            List[timedelta]: List with the stagnation durations
        """
        # TODO: Add a parameter to select the drawdown function
        # TODO: Check why pips_mode changes the result (stagnation should be the same)
        dd = self.drawdown(pips_mode).to_list()
        stagnation = [self.operations['Close Time'].iloc[dd.index(d)] for \
                      d in dd if d != 0]

        durations = pd.Series(stagnation).diff().to_list()

        # Need to remove first value (NaT)
        return durations[1:]

    def dd2(self, pips_mode=True) -> pd.Series:
        """Calculates the Drawdown in a different way from the self.drawdown method of this class

        Args:
            pips_mode (bool): Indicates whether the results must be in Pips or in monetary terms

        Returns:
            pd.Series: Numpy array with the drawdown values

        TODO: - Return value should be pd.Series, to be consisten with self.drawdown method
        """
        operations = self.operations['Pips'] if pips_mode is True else self.operations['Profit']
        d, dd_actual = [], 0

        for p in operations:
            dd_actual -= p
            if p < 0:
                dd_actual = 0
            d.append(dd_actual)

        return pd.Series(d)

    def esp(self, pips_mode=True) -> Decimal:
        """Calculates the Expectancy in either pips or money for the backtest operations

        Args:
            pips_mode (bool): Indicates whether the results must be in Pips or in monetary terms

        Returns:
            (Decimal): Value for the Expectancy
        """
        esp = self.operations['Pips'].mean() if pips_mode is True else self.operations['Profit'].mean()
        return Decimal(esp).quantize(Decimal(DEC_PREC))

    def exposures(self) -> Tuple[List[int], List[float]]:
        """
        This method calcualtes the maximum exposure in ops and in volume
        """
        exp = []
        vols = []
        operations = self.operations
        for _, op in operations.iterrows():
            open_time = op['Open Time']
            close_time = op['Close Time']
            ops = operations[(operations['Open Time'] >= open_time) & \
                             (operations['Close Time'] <= close_time)]
            exp.append(ops.shape[0])
            vols.append(ops['Volume'].sum())
        return exp, vols

    def _get_strikes(self, pips_mode=True) -> dict:
        """
        This method returns a Counter object where the positive and negative
        strikes are shown.
        """

        column = 'Pips' if pips_mode else 'Profit'
        self.operations['Strike Type'] = np.where(self.operations[column] > 0, 1, -1)
        strikes = {1: [], -1: []}
        counter = 0
        for idx in range(1, self.operations.shape[0]):
            if self.operations['Strike Type'].iloc[idx] == self.operations['Strike Type'].iloc[idx - 1]:
                counter += 1
            else:
                if self.operations['Strike Type'].iloc[idx - 1] == 1:
                    # Changed from winning strike to losing strike
                    strikes[1].append(counter)
                elif self.operations['Strike Type'].iloc[idx - 1] == -1:
                    # Changed from losing strike to winning strike
                    strikes[-1].append(counter)
                counter = 1
        return {1: Counter(strikes[1]), -1: Counter(strikes[-1])}

    def get_max_losing_strike(self, pips_mode: bool = True) -> int:
        strikes = self._get_strikes(pips_mode)
        return max(strikes[-1].keys())

    def get_max_winning_strike(self, pips_mode: bool = True) -> int:
        strikes = self._get_strikes(pips_mode)
        return max(strikes[1].keys())

    def get_avg_losing_strike(self, pips_mode: bool = True) -> Decimal:
        strikes = self._get_strikes(pips_mode)
        pairs = zip(strikes[-1].keys(), strikes[1].values())
        average = sum(pair[0] * pair[1] for pair in pairs)
        avg_losing_strike = average / sum(strikes[-1].values())
        return Decimal(avg_losing_strike).quantize(Decimal(DEC_PREC))

    def get_avg_winning_strike(self, pips_mode: bool = True) -> Decimal:
        strikes = self._get_strikes(pips_mode)
        pairs = zip(strikes[1].keys(), strikes[1].values())
        average = sum(pair[0] * pair[1] for pair in pairs)
        avg_winning_strike = average / sum(strikes[1].values())
        return Decimal(avg_winning_strike).quantize(Decimal(DEC_PREC))

    def get_max_lots(self) -> Decimal:
        max_lots = max(self.operations['Volume'])
        return Decimal(max_lots).quantize(Decimal(DEC_PREC))

    def get_min_lots(self) -> Decimal:
        min_lots = min(self.operations['Volume'])
        return Decimal(min_lots).quantize(Decimal(DEC_PREC))

    def _remove_overlapping_ops(self) -> pd.DataFrame:
        """
        Returns a dataframe with overlapping operations removed.
        An operation overlaps another one if and only if the former's Open Time
        and the former's Close Time is encompassed in the latter.

        This is a previous step in order to not account for duplicated time
        when calculating time in market for the backtest
        """
        indices = set(self.operations.reset_index(drop=True).index)
        for idx in indices:
            open_time = self.operations['Open Time'].iloc[idx]
            close_time = self.operations['Close Time'].iloc[idx]
            duplicated_idx = set(self.operations[(self.operations['Open Time'] >= open_time) & \
                                                 (self.operations['Close Time'] <= close_time)].index)
            # breakpoint()
            if len(duplicated_idx) > 1:
                indices = indices.difference(duplicated_idx)

        return self.operations.iloc[list(indices)]

    def calculate_time_in_market(self) -> Tuple[int, int, int, int]:
        operations_clean = self.operations
        # indices = set(self.operations_clean.reset_index(drop=True).index)
        total_time = operations_clean.iloc[0]['Duration']
        for idx in range(1, operations_clean.shape[0]):
            if operations_clean['Open Time'].iloc[idx] < operations_clean['Close Time'].iloc[idx - 1]:
                added_time = operations_clean['Close Time'].iloc[idx] - operations_clean['Close Time'].iloc[idx - 1]
                total_time += added_time
            else:
                total_time += operations_clean['Duration'].iloc[idx]

        days = total_time.days
        hours = (total_time - dt.timedelta(days=days)).seconds // 3600
        minutes = (total_time - dt.timedelta(days=days, hours=hours)).seconds // 60
        seconds = (total_time - dt.timedelta(days=days, hours=hours, minutes=minutes)).seconds

        return days, hours, minutes, seconds

    def num_winners(self, pips_mode=True) -> int:
        """ Returns the number of winning ops
        """
        column = 'Pips' if pips_mode else 'Profit'
        return int(self.operations[self.operations[column] > 0].shape[0])
    
    def pct_win(self, pips_mode=True) -> Decimal:
        """
        pips_mode: 
        """
        column = 'Pips' if pips_mode else 'Profit'
        pct_win = self.operations[self.operations[column] > 0].shape[0] / self.operations.shape[0] * 100
        return Decimal(pct_win).quantize(Decimal(DEC_PREC))

    def pct_loss(self, pips_mode=True) -> Decimal:
        pct_loss = 100 - self.pct_win(pips_mode)
        return Decimal(pct_loss).quantize(Decimal(DEC_PREC))

    def calculate_closing_days(self) -> int:
        """
        Calculates the number of different days where an order has been closed
        """
        years = pd.DatetimeIndex(self.operations['Close Time']).year.values.tolist()
        months = pd.DatetimeIndex(self.operations['Close Time']).month.values.tolist()
        days = pd.DatetimeIndex(self.operations['Close Time']).day.values.tolist()
        dates = zip(years, months, days)
        dates = set(dates)
        return len(dates)

    def calculate_sqn(self, pips_mode=True) -> Decimal:
        if pips_mode:
            sqn = self.operations['Pips'].mean() / (self.operations['Pips'].std() / (self.operations.shape[0] ** 0.5))
        else:
            sqn = self.operations['Profit'].mean() / (
                    self.operations['Profit'].std() / (self.operations.shape[0] ** 0.5))
        return Decimal(sqn).quantize(Decimal(DEC_PREC))

    def calculate_sharpe(self, pips_mode=True) -> Decimal:
        sr = self.calculate_sqn(pips_mode) * Decimal((self.operations.shape[0] ** 0.5))
        return sr.quantize(Decimal(DEC_PREC))

    def best_operation(self, pips_mode=True) -> Tuple[Decimal, 
                                                      ]:
        if pips_mode:
            column = 'Pips'
            factor = 10
        else:
            column = 'Profit'
            factor = 1
        magnitude, moment = self.operations[column].max() * factor, \
                            self.operations.iloc[self.operations[column].idxmax()]['Close Time']
        magnitude, moment = Decimal(magnitude).quantize(Decimal(DEC_PREC)), moment
        return magnitude, moment

    def worst_operation(self, pips_mode=True) -> Tuple[Decimal, dt]:
        if pips_mode:
            column = 'Pips'
            factor = 1
        else:
            column = 'Profit'
            factor = 10

        magnitude, moment = self.operations[column].min() * factor, \
                            self.operations.iloc[self.operations[column].idxmin()]['Close Time']
        magnitude, moment = Decimal(magnitude).quantize(Decimal(DEC_PREC)), moment
        return magnitude, moment

    def calculate_avg_win(self, pips_mode=True) -> Decimal:
        column = 'Pips' if pips_mode else 'Profit'
        ganancia = self.operations[self.operations[column] >= 0][column].mean().item()
        return Decimal(ganancia).quantize(Decimal(DEC_PREC))

    def calculate_avg_loss(self, pips_mode=True) -> Decimal:
        column = 'Pips' if pips_mode else 'Profit'
        perdida = self.operations[self.operations[column] < 0][column].mean().item()
        return Decimal(perdida).quantize(Decimal(DEC_PREC))

    def calculate_total_time(self) -> dt.timedelta:
        inicio = self.operations['Open Time'].iloc[0]
        fin = self.operations['Close Time'].iloc[-1]
        return fin - inicio

    def gross_profit(self, pips_mode=True) -> Decimal:
        column = 'Pips' if pips_mode else 'Profit'
        gp = self.operations[self.operations[column] >= 0][column].sum()
        return Decimal(gp).quantize(Decimal(DEC_PREC))

    def gross_loss(self, pips_mode=True) -> Decimal:
        column = 'Pips' if pips_mode else 'Profit'
        gl = self.operations[self.operations[column] < 0][column].sum()
        return Decimal(gl).quantize(Decimal(DEC_PREC))
    
    def calculate_rf(self, pips_mode=True) -> Decimal:
        column = 'Pips' if pips_mode else 'Profit'
        max_dd = -self.max_dd(pips_mode, 'dd')
        rf = self.gross_profit(pips_mode) / max_dd
        return Decimal(rf).quantize(Decimal(DEC_PREC))

    def _eqm(self, pips_mode=True) -> Tuple[Any, Any, Any]:
        column = 'Pips' if pips_mode else 'Profit'
        x = self.operations.reset_index().index.values.reshape(-1, 1)
        y = self.operations[column].cumsum()

        xhat = np.mean(x)
        yhat = np.mean(y)
        n = x.flatten().size
        xdev = np.sum(np.square(x - xhat))
        ydev = np.sum(np.square(y - yhat))
        xydev = np.square(np.sum((x.flatten() - xhat) * (y - yhat)))
        error = np.sqrt(np.around((ydev - xydev / xdev) / (len(x) - 2), decimals=8)) / np.sqrt(xdev)

        return x, y, error

    def calculate_kratio(self, pips_mode=True) -> Decimal:
        x, y, error = self._eqm(pips_mode)
        model = LinearRegression().fit(x, y)
        kr = model.coef_[0] / (error * len(x))
        return Decimal(kr).quantize(Decimal(DEC_PREC))   
    
    def metrics_to_df(self, criteria: set = None, export_to_csv: bool = False) -> None:
        filename = 'metrics.csv'
        default_columns = [
            'NAME',
            'PERIOD',
            '¿VALIDA?',           
                #self.bt.name,
                #self.bt.from_periods_to_text(self.bt.period),                
            ]
        default_values = [
            self.bt.name,
            self.bt.from_period_to_text(self.bt.period),
            self.valid,
        ]
        if criteria is None:
            columns = [
            'PIPS',
            'kratio',
            'SQN',
            'EP',
            'DD',
            'RF',
            '# Ops',
            'Win Ops',
            '% w',
            'Mejor Op',
            'Peor Op',
            'Max. Ganancia consecutiva',
            'Max. Perdida consecutiva',
            'Max. Exposición Mercado',
            'Pérdida Media',
            'Ganancia Media',
            'Ratio',
            'Días',
            '% tiempo mercado',
            'Tiempo medio op.',
            'Op más larga',
            'Op más corta',                
            ]
            days, hours, minutes, seconds = self.calculate_time_in_market()
            op_promedio = self.bt.operations.Duration.sum() / self.bt.operations.shape[0]
            avg_days = op_promedio.days
            avg_hours = (op_promedio - dt.timedelta(days=avg_days)).seconds // 3600
            avg_minutes = (op_promedio - dt.timedelta(days=avg_days, hours=avg_hours)).seconds//60
            values = [
                self.gross_profit(self.pips_or_money),
                self.calculate_kratio(self.pips_or_money),
                self.calculate_sqn(self.pips_or_money),
                self.esp(self.pips_or_money),
                Decimal(self.drawdown(self.pips_or_money).min()).quantize(Decimal(DEC_PREC)),
                self.calculate_rf(self.pips_or_money),
                self.num_ops,                
                self.num_winners(self.pips_or_money),
                self.pct_win(self.pips_or_money),
                self.best_operation(self.pips_or_money)[0],
                self.worst_operation(self.pips_or_money)[0],
                self.get_max_winning_strike(self.pips_or_money),
                self.get_max_losing_strike(self.pips_or_money),
                max(self.exposures()[1]),
                self.calculate_avg_loss(self.pips_or_money),
                self.calculate_avg_win(self.pips_or_money),                
                self.ratio,
                self.calculate_closing_days(),
                Decimal(dt.timedelta(days=days, hours=hours, minutes=minutes) / \
                    self.calculate_total_time() * 100).quantize(Decimal(DEC_PREC)),
                dt.timedelta(days=avg_days, hours=avg_hours, minutes=avg_minutes),
                self.operations.Duration.max(),
                self.operations.Duration.min(),
            ]
        else:
            columns = criteria
            values = [self._calculate_one_metric[column] for column in criteria]
            
        # Join columsn to default_columns
        all_columns = default_columns + columns
        all_values = [default_values + values]        
        df = pd.DataFrame(data=all_values, columns=all_columns)
        self.df_metrics = df
        if export_to_csv:
            df.to_csv(filename, index=False, decimal=',')
        return df
            