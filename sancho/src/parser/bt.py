import pandas as pd
import numpy as np
from pathlib import Path

METATRADER = 'MT4'
GENBOX = 'GBX'
FOREX_PAIRS = {'EUR': 'e', 'USD': 'u', 'JPY': 'j', 'AUD': 'a', 'NZD': 'n', 'CAD': 'cd', 'CHF': 'cf',
               'GBP': 'g'}


def classify_bts(path: str, files: list) -> dict:
    classification = {}
    for file in files:
        if len(pd.read_html(Path(path, file))) == 2:
            classification[file] = METATRADER
        else:
            classification[file] = GENBOX

    return classification


def parse_mt4_html(path, file: str) -> pd.DataFrame:
    """
        Parse data from html
    """
    raw_data = pd.read_html(Path(path, file))
    header = raw_data[0]
    symbol = header.iloc[0, 2].split(' ')[0]
    ops = raw_data[1]

    ops.columns = ops.iloc[0, :]

    ops.drop(0, inplace=True)
    ops.set_index('#', drop=True, inplace=True)

    ops.Orden = ops.Orden.astype(int)
    ops.Tiempo = pd.to_datetime(ops.Tiempo)
    ops.Tipo = ops.Tipo.astype(str)
    ops.Volumen = pd.to_numeric(ops.Volumen)
    ops.Precio = pd.to_numeric(ops.Precio)
    ops['S / L'] = pd.to_numeric(ops['S / L'])
    ops['T / P'] = pd.to_numeric(ops['T / P'])
    ops.Beneficios = pd.to_numeric(ops.Beneficios)
    ops.Balance = pd.to_numeric(ops.Balance)

    return ops, symbol.lower()


def parse_genbox_html(path, file: str, deposit: float = 10000.00) -> pd.DataFrame:
    raw_data = pd.read_html(Path(path, file))
    # Leemos las operaciones y quitamos las dos primeras
    # filas, ya que contienen información irrelevante
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
    ops['Pips'] = get_pips(ops)
    ops = ops[columnas]   

    # Reasignar número de ticker
    ops.reset_index(inplace=True, drop=True)

    return ops


def get_type_multiplier(tipo: pd.Series) -> list:
    multiplier = []
    for t in tipo:
        if t.lower() == 'buy':
            multiplier.append(1)
        elif t.lower() == 'sell':
            multiplier.append(-1)
    return multiplier


def get_symbol_digits(price: float) -> int:
    return len(str(price).split('.')[1])


def get_point_value(digits: int) -> float:
    return 10 ** (digits - 1)


def get_points(df: pd.DataFrame) -> list:
    if 'Symbol' in df.columns:
        if len(df['Symbol'].unique()) > 1:
            digits = list(df['Open Price'].apply(get_symbol_digits))
        else:
            digits = get_symbol_digits(df['Open Price'].iloc[0]) * np.ones(df.shape[0])
    else:
        digits = get_symbol_digits(df['Open Price'].iloc[0]) * np.ones(df.shape[0])
    
    return [10 ** (digit - 1) for digit in digits]


def get_pips(df: pd.DataFrame) -> pd.Series:
    points = get_points(df)
    multiplier = get_type_multiplier(df['Type'])
    factor = [multiple * point for multiple, point in zip(points, multiplier)]
    return (df['Close Price'] - df['Open Price']).values * factor


def format_mt4_ops(df: pd.DataFrame, symbol: str, deposit: float = 10000.00) -> pd.DataFrame:
    columnas = ['#', 'Open Time', 'Close Time', 'S/L', 'T/P', 'Duration',
                'Type', 'Volume', 'Symbol', 'Open Price', 'Close Price', 'Pips', 'Profit']
    ordenes = []
    digits = get_symbol_digits(df.Precio.iloc[0])
    for orden in df.Orden.unique():
        # Seleccionamos una orden a la vezics
        df_sub = df[df.Orden == orden]
        profit_pips = (df_sub.Precio.iloc[-1] - df_sub.Precio.iloc[0]) * (10 ** (digits - 1))
        fila = [df_sub.Orden.iloc[0], df_sub.Tiempo.iloc[0], df_sub.Tiempo.iloc[-1],
                df_sub.iloc[0]['S / L'], df_sub.iloc[0]['T / P'],
                df_sub.Tiempo.iloc[-1] - df_sub.Tiempo.iloc[0], df_sub.Tipo.iloc[0],
                df_sub.Volumen.iloc[0], symbol, df_sub.Precio.iloc[0], df_sub.Precio.iloc[-1],
                profit_pips, df_sub.Beneficios.iloc[-1]]
        ordenes.append(fila)

    df_out = pd.DataFrame(ordenes, columns=columnas)
    df_out['Balance'] = deposit + df_out['Profit'].cumsum()
    df_out.drop('#', axis=1, inplace=True)
    df_out.reset_index(inplace=True, drop=True)

    return df_out


def get_forex_short_names(symbol: str) -> str:
    """
    This method returns a short name according to FOREX_PAIRS variable
    """

    if len(symbol) != 6:
        return ''
    else:
        first, last = symbol[:3], symbol[3:]

    return f'{FOREX_PAIRS[first]}{FOREX_PAIRS[last]}'
