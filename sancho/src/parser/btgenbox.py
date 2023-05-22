# Standard library imports
import os
from pathlib import Path

# Non-standard library imports
import numpy as np
import pandas as pd

# Project imports
from .btparser import (BtParser,
                       BtPlatforms, 
                       BtPeriods, 
                       BtOrderType,
                       EXTENSION_SEP, 
                       GENBOX_FIELD_SEP,)
# from .metrics import Metrics


##########################################################################################################
# CONSTANTS AND ENUMERATIONS USED BY THIS CLASS
# Column names for operations dataframe
OPS_INITIAL_COLUMN_NAMES = ['Open Time', 'Type', 'Volume', 'Symbol', 'Open Price',
                        'S/L', 'T/P', 'Close Time', 'Close Price', 'Commission', 'Taxes',
                        'Swap', 'Profit']
OPS_DROP_COLUMN_NAMES = ['Commission', 'Taxes', 'Swap']
OPS_FINAL_COLUMN_NAMES = ['Open Time', 'Close Time', 'S/L', 'T/P', 'Duration',
                        'Type', 'Volume', 'Symbol', 'Open Price', 'Close Price',
                        'Pips', 'Profit', 'Balance']
##########################################################################################################


class BtGenbox(BtParser):
    """
    Represents a Genbox Backtest object

    Instance variables:
        path (Path): Path where the backtests in html or htm are stored
        
        file (str):  Filename for the backtest to be parsed

    Instance properties (inherited):
        * path
        * file

    Instance properties
        * name
        * platform
        * period
        * symbol
        * ordertype

    Instance methods (inherited):
        * get_order_multiplier
        * get_symbol_digits
        * get_point_value
        * get_points
        * get_pips
        * get_platform_to_text
        * _bt_platform
    """

    def __init__(self, path: Path, file: str) -> None:
        """
        Creates and returns a Genbox object

        Parameters
        ----------
        path: Path
                Path where the Genbox backtest in html or htm are stored
        
        file: str
                Filename for the Genbox backtest to be parsed

        Returns
        -------
        None
        """

        super().__init__(path, file)
        # TODO: Change self.operations for something more descriptive
        
        if path == '.' or path is None:             
            self.operations = Path(self.file)
        else:
            self.operations = Path(self.path/self.file)
        self.platform = self._bt_platform()
        self.period = self._bt_period()
        
    
    @property
    def name(self) -> str:
        """Read-only property that returns the name of the backtest
           The name of the backtest is the same for 3 backtests (IS, OS, and ISOS)
           since it should be the same parametrization over different periods of time
        """
        if self.period == BtPeriods.ISOS:
            return self.file.split(EXTENSION_SEP)[0]
        else:
            return '_'.join(self.file.split(EXTENSION_SEP)[0].split(GENBOX_FIELD_SEP)[:-1])

    @property
    def platform(self) -> BtPlatforms:
        return self._platform if self._platform else BtPlatforms.UKN
    
    @platform.setter
    def platform(self, value: BtPlatforms):        
        self._platform = value if value in BtPlatforms else BtPlatforms.UKN

    @property
    def period(self) -> BtPeriods:
        return self._period if self._period else BtPeriods.ISOS
    
    @period.setter
    def period(self, value: BtPeriods):
        self._period = value if value in BtPeriods else BtPeriods.ISOS

    @property
    def operations(self) -> pd.DataFrame:
        return self._ops
    
    @operations.setter
    def operations(self, value) -> None:
        """Reads the html file passed as argument and parses the operations"""
        '''
        if os.path.exists(value):
            self._ops = self.parse_html()
        else:
            raise FileNotFoundError
        '''
        self._ops = self.parse_html()
    
    @property
    # TODO - for next version, try to check symbol really exists
    #        i.e. it is valid
    def symbol(self) -> str:
        return str(self.operations['Symbol'].unique()[0]).upper()
    
    @property
    def ordertype(self) -> BtOrderType:        
        value = str(self.operations['Type'].unique()[0].upper())
        return self.from_text_to_ordertype(value)
    
    @property
    def timeframe(self) -> str:
        return ''

    def parse_html(self,  deposit: float = 10000.00) -> pd.DataFrame:
        """
        Parses Backtest for Genbox-like backtest as html file.

        Parameters
        ----------
        deposit: float, optional
            Initial deposit to start the backtest from

        Returns
        -------
        pandas.DataFrame:
            A dataframe with all the operations parsed including relevant
            information such as open and close times, prices.
            This information is used later to get the metrics
        """
        if self.path == '.':
            pd.read_html(Path(self.file))
        else:
            raw_data = pd.read_html(Path(self.path/self.file))
        
        # Read operations
        ops = raw_data[0].iloc[2:, :]

        # Quitar las filas que contienen la cadena "Genbox"
        # Estas filas tienen NaN en las celdas
        ops = ops.dropna()

        # Reseteamos el índice
        ops.reset_index(inplace=True, drop=True)

        # Asignar el nombre de las columnas
        # Eliminar la fila con el nombre de las columnas
        ops.columns = ops.iloc[0, :]

        # Quitamos la fila con las columnas y la que
        # marca el depósito
        ops.drop([0, 1], inplace=True)
        # ops.drop(1, inplace=True)
        ops.reset_index(inplace=True, drop=True)

        # El informe termina con la cadena 'Closed P/L:'
        end_of_data = 'Closed P/L:'
        idx = ops.index[ops.Ticket == end_of_data].to_list()[0]

        # Seleccionamos sólo las operaciones
        ops = ops.iloc[0:idx, :]

        # Reseteamos el índice de nuevo
        ops.set_index('Ticket', drop=True, inplace=True)

        # Convertimos al formato adecuado las columnas
        # Columnas temporales
        ops[ops.columns[0]] = pd.to_datetime(ops[ops.columns[0]])
        ops[ops.columns[7]] = pd.to_datetime(ops[ops.columns[7]])

        # Columnas de texto
        ops[ops.columns[1]].astype(str)
        ops[ops.columns[3]].astype(str)

        # Columnas numéricas
        num_col = [2, 4, 5, 6, 8, 9, 10, 11, 12]
        for col in num_col:
            ops[ops.columns[col]] = ops[ops.columns[col]].astype(float)

        # Nombre inicial de las columnas        
        ops.columns = OPS_INITIAL_COLUMN_NAMES

        ops['Duration'] = ops['Close Time'] - ops['Open Time']
        ops['Balance'] = deposit + ops['Profit'].cumsum()

        # Quitamos las columnas que sobran        
        ops.drop(OPS_DROP_COLUMN_NAMES, axis=1, inplace=True)

        # Reordenamos las columnas del dataframe para que tanto los de GBX como los de MT4
        # tengan el mismo orden de columnas
        
        # Pips must be split in two different lines if we want to avoid to have all Pips NaN
        ops['Pips'] = self.get_pips(ops)
        ops = ops[OPS_FINAL_COLUMN_NAMES]

        # Reasignar número de ticker
        ops.reset_index(inplace=True, drop=True)

        return ops
    
    def _bt_period(self, field_sep: str = GENBOX_FIELD_SEP) -> BtPeriods:
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

        # For Genbox-generated BTs, the fields are separated with _
        period = self.file.split(EXTENSION_SEP)[0].split(field_sep)[-1]
        match period:
            case 'IS':
                return BtPeriods.IS
            case 'OS':
                return BtPeriods.OS
            case _:
                return BtPeriods.ISOS        
