import numpy as np
import pandas as pd

def get_evsgamma(atom, basis, charge=0, names=None):
    fname = f"outputs/table_{atom}_{charge}_{basis}.csv"
    try:
        data = pd.read_csv(fname, names=names, skipinitialspace=True)
    except FileNotFoundError:
        print(f"{fname} not found")
        return None
    return data

def get_min(data):
    gammas = data['GEM_BETA'].values
    gamma_min = gammas[data['E'] == data['E'].min()]
    return gamma_min

def get_table_files(basis=None, elem=None):
    csvs = []
    elements = {}
    for f in os.listdir('./outputs/'):
        if not f.endswith('.csv'): continue
        if basis is not None:
            if basis not in f: continue
        if elem is not None:
            if elem not in f: continue
        csvs.append(f'./outputs/{f}')
    return csvs

def min_gamma_for_cols(df: pd.DataFrame, cols: list[str] | None = None) -> pd.Series:
    """
    For each column in `cols`, find the row index of its minimum,
    and return the corresponding value from column A.

    If cols is None, all columns except the first are used.
    """
    if cols is None:
        cols = df.columns[1:]  # everything except the first column
        
    min_indices = df[cols].idxmin()
    return pd.Series({col: df.loc[min_indices[col], "GEM_BETA"] for col in cols})