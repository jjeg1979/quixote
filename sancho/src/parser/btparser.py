# Standard library imports
import abc
from typing import List
from pathlib import Path
from enum import Enum
from decimal import Decimal

# Non-standard library imports
import numpy as np
import pandas as pd

# Project imports


##########################################################################################################
# CONSTANTS AND ENUMERATIONS USED BY THIS CLASS
# Common separator for filename and extension
EXTENSION_SEP = '.'
GENBOX_FIELD_SEP = '_'

# Class representing unique values for the bt periods:
#   IS   : In sample data
#   OS   : Out of sample data
#   ISOS : IS+OS, i.e., In sample + Out of Sample periods
class BtPeriods(Enum):
    IS = 0
    OS = 1
    ISOS = 2

# Class representing unique values for the bt order types:
#   BUY   : Buy Only orders
#   SELL  : Sell Only orders
#   BOTH  : Both (Buy and Sell)
class BtOrderType(Enum):
    BUY = -1
    SELL = 1
    BOTH = 0

# Class representing unique values for the platform that generated the backtest:
#   MT4  : METATRADER4
#   MT5  : METATRADER5
#   GBX  : GENBOX
#   STM  : STATEMENT FROM REAL ACCOUNT
class BtPlatforms(Enum):
    MT4 = 0
    MT5 = 1
    GBX = 2
    STM = 3
    UKN = 0

# Dictionary for the abbreviations used for the forex pairs
FOREX_PAIRS = {'EUR': 'e', 'USD': 'u', 'JPY': 'j', 'AUD': 'a', 'NZD': 'n', 'CAD': 'cd', 'CHF': 'cf',
               'GBP': 'g'}

# Dictionary with timeframes
BT_TIMEFRAMES = {'M1': 1, 'M5': 2, 'M15': 3, 'M30': 4, 'H1': 5, 'H4': 6, 'D1': 7, 'W': 8, 'M': 9}

# Needs to be a tuple, the method endswith expects a tuple of str or a str, not a list
BT_EXTENSIONS = ('html', 'htm',)
##########################################################################################################

class BtParser(metaclass=abc.ABCMeta):
    """
    Abstract representation of a class for Parsing Backtests

    Instance variables:
        path (Path): Path where the backtests in html or htm are stored
        
        file (str):  Filename for the backtest to be parsed

    Instance properties:
        - path
        - file
        
    Instance methods:    
        * get_order_multiplier
        * get_symbol_digits
        * get_point_value
        * get_points
        * get_pips
        * _platform_to_text
        * _bt_platform
    """

    def __init__(self, path: Path, file: str) -> None:
        """
        Creates and returns a Btparser object

        Args:
        
            path (Path): Path where the backtests in html or htm are stored
        
            file (str):  Filename for the backtest to be parsed

        Returns:        
            None.
        """
        self._path = path or Path('.')
        self._file = file or ''

    @property
    def path(self) -> Path:
        return self._path if self._path is not None else Path('.')

    # TODO: Error in case value is not path-like string or it doesn't exist
    @path.setter
    def path(self, value: Path):
        self._file = value if value is not None else '.'

    @property
    def file(self):
        return self._file if self._file is not None else None
    
    @abc.abstractproperty
    def symbol(self) -> str:
        pass

    @abc.abstractproperty
    def ordertype(self) -> str:
        pass

    @abc.abstractproperty
    def timeframe(self) -> str:
        pass

    @abc.abstractmethod
    def parse_html(self, deposit: Decimal = Decimal(10000.00)) -> pd.DataFrame:
        pass

    def get_order_multiplier(self, tipo: pd.Series) -> List[int]:
        multiplier = []
        for t in tipo:
            if t.lower() == 'buy':
                multiplier.append(1)
            elif t.lower() == 'sell':
                multiplier.append(-1)
        return multiplier

    def get_symbol_digits(self, price: float) -> int:
        return len(str(price).split('.')[1])

    def get_point_value(self, digits: int) -> int:
        return 10 ** (digits - 1)

    def get_points(self, df: pd.DataFrame) -> List[int]:
        if 'Symbol' in df.columns:
            if len(df['Symbol'].unique()) > 1:
                digits = list(df['Open Price'].apply(self.get_symbol_digits))
            else:
                digits = self.get_symbol_digits(df['Open Price'].iloc[0]) * np.ones(df.shape[0])
        else:
            digits = self.get_symbol_digits(df['Open Price'].iloc[0]) * np.ones(df.shape[0])

        return [10 ** (digit - 1) for digit in digits]

    def get_pips(self, df: pd.DataFrame) -> pd.Series:
        points = self.get_points(df)
        multiplier = self.get_order_multiplier(df['Type'])
        factor = [multiple * point for multiple, point in zip(points, multiplier)]
        return (df['Close Price'] - df['Open Price']).values * factor
    
    def from_platform_to_text(self, platform: BtPlatforms) -> str:
        """
        Takes a value from the BtPlatform Enumeration and returns a
        string representation for the platform (more human readable)

        Args:
            platform (BtPlatform): Enumeration value

        Returns:
            (str): A human readable representation of the platform
        """

        match platform:
            case BtPlatforms.MT4:
                return 'METATRADER4'
            case BtPlatforms.MT5:
                return 'METATRADER5'
            case BtPlatforms.GBX:
                return 'GENBOX'
            case BtPlatforms.STM:
                return 'STATEMENT'
            case BtPlatforms.UKN:
                return 'UNKNOWN'
            case _:
                # TODO - Custom Exception for this type
                return ValueError
            
    def from_period_to_text(self, period: BtPeriods) -> str:
        """
        Takes a value from the BtPeriods Enumeration and returns a
        string representation for the backtest period (more human readable)

        Args:
            period (BtPeriod): Enumeration value

        Returns:
            (str): A human readable representation of the backtest period
        """

        match period:
            case BtPeriods.IS:
                return 'IS'
            case BtPeriods.OS:
                return 'OS'
            case BtPeriods.ISOS:
                return 'ISOS'
            case _:
                # TODO - Custom Exception for this type
                return ValueError
    
    def from_ordertype_to_text(self, order_type: BtOrderType) -> str:
        """
        Takes a value from the BtOrderType Enumeration and returns a
        string representation for the backtest order type (more human readable)

        Args:
            period (BtOrderType): Enumeration value

        Returns:
            (str): A human readable representation of the backtest order type
            
        Raises:
            ValueError if the type does not belong to BtOrderType Enum
        """

        match order_type:
            case BtOrderType.BUY:
                return 'Buy'
            case BtOrderType.SELL:
                return 'Sell'
            case BtOrderType.BOTH:
                return 'Buy&Sell'
            case _:
                # TODO - Custom Exception for this type
                return ValueError
            
    def from_text_to_ordertype(self, order_type: str) -> BtOrderType:
        """
        Takes a string value with the for the backtest order type and returns
        a value from the enumeration BtOrderType

        Args:
            order_type (str): String which can take up one of the following values:
                - 'BUY'
                - 'SELL'
                - 'BUY&SELL'

        Returns:
            (BtOrderType): A BtOrderType enumeration value
            
        Raises:
            ValueError: If order_type cannot be translated into one of the 
                        BtOrderType Enum values
        """
        
        match order_type:
            case 'BUY':
                return BtOrderType.BUY
            case 'SELL':
                return BtOrderType.SELL
            case 'BUY&SELL':
                return BtOrderType.BOTH
            case _:
                return ValueError
            

            
    def _bt_platform(self) -> BtPlatforms:
        """
        Classifies backtest according the platform

        Parameters
        ----------

        Returns
        -------
        BtPlatforms
            One of the values from BtPlatforms enumeration
        """
        # TODO - Ensure it includes more options
        # Check if self.path is empty
        if self.path == []:
            path = '.'
        else:
            path = self.path

        return BtPlatforms.MT4 if len(pd.read_html(path/Path(self.file))) == 2 else\
               BtPlatforms.GBX 

    @abc.abstractmethod
    def _bt_period(self, field_sep: str) -> BtPeriods:
        """
        Classifies backtest according the time period

        Parameters
        ----------
        field_sep: str
            Character with the field separation for the platform

        Returns
        -------
        BtPeriods
            One of the values from BtPeriods enumeration
        """
        pass
