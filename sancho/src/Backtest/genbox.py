import numpy as np
import pandas as pd
from pathlib import Path
from pyBTAnalyst.src.btparser import btparser


class Genbox(btparser):
    def __init__(self, path: Path, file: str) -> None:
        super().__init__(path, file)

    def parse_html(self, deposit: float = 10000.00) -> pd.DataFrame:
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
            information such as open and close times, prices...
        """

        raw_data = pd.read_html(self.path/Path(self.file))
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

        # Nombre de las columnas
        columnas = ['Open Time', 'Type', 'Volume', 'Symbol', 'Open Price',
                    'S/L', 'T/P', 'Close Time', 'Close Price', 'Commission', 'Taxes',
                    'Swap', 'Profit']
        ops.columns = columnas

        ops['Duration'] = ops['Close Time'] - ops['Open Time']
        ops['Balance'] = deposit + ops['Profit'].cumsum()

        # Quitamos las columnas de swap, comision e impuestos
        drop_columns = ['Commission', 'Taxes', 'Swap']
        ops.drop(drop_columns, axis=1, inplace=True)

        # Reordenamos las columnas del dataframe para que tanto los de GBX como los de MT4
        # tengan el mismo orden de columnas
        columnas = ['Open Time', 'Close Time', 'S/L', 'T/P', 'Duration',
                    'Type', 'Volume', 'Symbol', 'Open Price', 'Close Price',
                    'Pips', 'Profit', 'Balance']
        # Pips must be split in two different lines if we want to avoid to have all Pips NaN
        ops['Pips'] = self.get_pips(ops)
        ops = ops[columnas]

        # Reasignar número de ticker
        ops.reset_index(inplace=True, drop=True)

        return ops
