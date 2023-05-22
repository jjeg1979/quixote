import abc
from pathlib import Path
import numpy as np
import pandas as pd


class Btparser(metaclass=abc.ABCMeta):
    def __init__(self, path: Path, file: str) -> None:
        self._path = path
        self._file = file

    @property
    def path(self):
        return self._path if self._path is not None else None

    # TODO: Error in case value is not path-like string or it doesn't exist
    @path.setter
    def path(self, value: Path):
        self._file = value if value is not None else None

    @property
    def file(self):
        return self._file if self._file is not None else None

    @abc.abstractmethod
    def parse_html(self, deposit: float = 10000.00) -> pd.DataFrame:
        pass

    def get_type_multiplier(self, tipo: pd.Series) -> list:
        multiplier = []
        for t in tipo:
            if t.lower() == 'buy':
                multiplier.append(1)
            elif t.lower() == 'sell':
                multiplier.append(-1)
        return multiplier

    def get_symbol_digits(self, price: float) -> int:
        return len(str(price).split('.')[1])

    def get_point_value(self, digits: int) -> float:
        return 10 ** (digits - 1)

    def get_points(self, df: pd.DataFrame) -> list:
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
        multiplier = self.get_type_multiplier(df['Type'])
        factor = [multiple * point for multiple, point in zip(points, multiplier)]
        return (df['Close Price'] - df['Open Price']).values * factor
