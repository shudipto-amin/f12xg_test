import pandas as pd
import importlib
import matplotlib as mpl
import matplotlib.pyplot as pp
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import numpy as np
import scipy as sp
from ipywidgets import widgets
import os
from typing import Optional, List, Tuple
from functools import reduce
import datetime
import single_output_parser as sop
from itertools import product
from collections.abc import Iterable
from io import StringIO

class MakeTables(object):
    """
    Class for holding all functions related to Table making
    """
    metadata_begin_marker = "----METADATA----"
    metadata_end_marker = "----------------"

    def __init__(self):
        pass

    @staticmethod
    def add_sum_and_difference(df, prefix, max_dist):
        monomers_key = ("Monomers", *prefix)
        sum_key = ("Monomers", *prefix,  "Sum")
        dimer_key = ("Dimer distances", *prefix,  max_dist)
        difference_key = (
            *prefix,
            "Difference",
            f"Mono - dimer @{max_dist}",
        )
    
        df.loc[sum_key, :] = df.loc[monomers_key].sum()
        df.loc[difference_key, :] = (
            df.loc[sum_key]
            - df.loc[dimer_key]
        )
    
    @classmethod
    def combine_systems(
            cls,
            dimer_df,# = 'ne_ar/dfmp2/bse_data.csv'
            mono1_df,# = 'ar/dfmp2/bse_data.csv'
            mono2_df,# = 'ne/dfmp2/bse_data.csv'
            mono1_name="Monomer_1", mono2_name="Monomer_2",
            outer_index=None
    ):
        max_dist = dimer_df.index.get_level_values("distances").max()
    
        adf = pd.concat(
            [mono1_df, mono2_df],
        )
        #print(dimer_df.index.names)
        if outer_index is not None:
            adf = adf.reorder_levels([outer_index, 0])
        print(adf.index.names)
        #adf.loc[('Monomer_sum'] = adf.groupby('core').sum()
        df = pd.concat(
            [dimer_df, adf], 
            keys = ['Dimer distances', 'Monomers']
        )
        print(df.index.names)
        if outer_index is None:
            cls.add_sum_and_difference(df, (), max_dist)
        else:
            values = (
                df.loc["Monomers"]
                .index
                .get_level_values(outer_index)
                .unique()
            )
           
            for val in values:
                print(val)
                cls.add_sum_and_difference(df, (val,), max_dist)
                
            #mono2.index = [mono2_name]
            #display(dimer)
            max_dist = dimer_df.index.get_level_values(0).max()
    
            
    
        return df

    @classmethod
    def write_metacsv(
            cls, meta_for_csv: dict, df: pd.DataFrame, filepath: str, *args,
            meta_begin_marker=None, meta_end_marker=None, **kwargs
            ):
        if meta_begin_marker is None:
            meta_begin_marker = cls.metadata_begin_marker
        if meta_end_marker is None:
            meta_end_marker = cls.metadata_end_marker

        with open(filepath, 'w') as f:
            
            f.write(f"{meta_begin_marker}\n")
            for key, val in meta_for_csv.items():
                f.write(f"{key},\"{val}\"\n")
            f.write(f"{meta_end_marker}\n")
            df.to_csv(f, *args, **kwargs)

    @classmethod
    def read_metacsv(
            cls, filepath,
            meta_begin_marker=None, meta_end_marker=None,
            contains_meta=True, kwargs1=None, kwargs2=None
            ):
        if meta_begin_marker is None:
            meta_begin_marker = cls.metadata_begin_marker
        if meta_end_marker is None:
            meta_end_marker = cls.metadata_end_marker

        if kwargs1 is None:
            kwargs1 = dict(header=None)
        if kwargs2 is None:
            kwargs2 = dict()
            
        df1_lines = ""
        with open(filepath, 'r') as f:
            if contains_meta:
                for n, line in enumerate(f):
                    if n==0 and line.rstrip('\n') != meta_begin_marker:
                        raise ValueError(f"Metadata begin marker ({meta_begin_marker}) not found")
                    elif n==0:
                        continue
                    if line.rstrip('\n') == meta_end_marker:
                        break
                    df1_lines += line
            df2 = pd.read_csv(f, **kwargs2)
        df1 = pd.read_csv(StringIO(df1_lines), **kwargs1)
        return df1, df2

def get_data(
        data_file, usecols=None, ignore_file_cols=False, ignore_cols=None,
        make_relative=False, col_name='outfile'
        ):
    '''
    Returns a dataframe of data file

    Arguments:
        data_file : path to data file
            Should be a <system>/<method>/data.csv file, e.g.:
            `nh3/standard/data.csv`

        [ignore_file_cols] : if True (default), ignores columns 
            which refer to raw data file 

        [usecols] : if provided, uses columns names provided.

        [make_relative] : Make filepaths in a column (default is outfile)
            relative to the dirname of data_file.

        [col_name] : outfile colname for making make_relative.

    '''
    if ignore_cols is None:
        ignore_cols = ['full_file_prefix']

    df = pd.read_csv(data_file, usecols=None)
    
    if ignore_file_cols and usecols is None:
        cols = [col for col in df.columns if 'file' not in col]
    elif usecols is not None:
        cols = usecols
    else:
        cols = df.columns
       
    if make_relative:
        make_relative_to(df, os.path.dirname(data_file), col_name=col_name)

    cols = [col for col in cols if col not in ignore_cols]
    
    return df[cols]

def make_relative_to(df, path, col_name='outfile'):
    '''
    Make a column with path names relative to another'
    '''
    newpathFunc = lambda file: os.path.join(path, file)
    df[col_name] = df[col_name].apply(newpathFunc)
    

def parse_outfiles_in_df(
        df, query_dict, col_name='outfile', drop_col_name=True
        ):
    OutParser = sop.OutputParser(query_dict)
    additional_df = df[col_name].apply(lambda f: pd.Series(OutParser.GetAll(f)))
    new_df = pd.concat([df, additional_df], axis=1)
    if drop_col_name:
        new_df = new_df.drop(columns=[col_name])
    return new_df 

def filter_df(df, filters: dict):
    for key,val in filters.items():
        if isinstance(val, list):
            df = df[df[key].isin(val)]
        else:
            df = df[df[key] == val]
    return df

def _as_list(value):
    """Treat scalars/strings as one value; lists/tuples/sets as many."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]
    
def expand_filter_grid(common_filter, cross_filters):
    """
    Combine `common_filter` with the Cartesian product of `cross_filters`.

    Parameters
    ----------
        common_filter : {
            "key1": value,
            ...
        },
        cross_filters : {
            "key2": [value1, value2],
            "key3": [valueA, valueB],
            ...
        }

    Returns
    -------
    list[dict]
        One filter dictionary per combination.
    """

    if not cross_filters:
        return [dict(common_filter)]

    keys = list(cross_filters.keys())
    value_lists = [_as_list(cross_filters[key]) for key in keys]
    
    filters = []

    for combo in product(*value_lists):
        combined = dict(common_filter)
    
        for key, value in zip(keys, combo):
            combined[key] = value

        filters.append(combined)

    return filters
    
def assign_basis_size(df):
    '''
    Assigns basis set size, assuming that the 2nd last character indicates size
    eg. cc-pVXz, etc

    Inserts the corresponding sizes as a new column in the DataFrame provided.
    '''
    basis_sizes = []
    size_dict = {
        'D' : 2, 'T' : 3, 'Q' : 4
    }
    for basis in df.bases:
        
        size_str = basis[basis.find("Z") - 1]
        if size_str in size_dict:
            size = size_dict[size_str]
        else:
            size = int(size_str)
        basis_sizes.append(size)
    df.insert(1, 'basis_sizes', basis_sizes
             )    

## Interaction energy helpers
def add_suffix(df, suffix, cols_to_merge):
    '''Add suffix only to cols not included in merge'''
    df.columns = [
        f"{col}_{suffix}" if col not in cols_to_merge else col for col in df.columns
    ]

## Basis set extrapolation
def get_cbs_from_values(X, E, exp=3, HF=False):
    '''Return the CBS limit extrapolated from a pair of data points'''
    X = X*1.0 # converting to float
    if HF:
        x0, x1, x2 = X[-3:][::-1]
        e0, e1, e2 = E[-3:][::-1]
        return (e0 * e2 - e1**2) / (e2 - 2*e1 + e0)
    else:
        x1, x2 = X[-2:]
        e1, e2 = E[-2:]
        return (e1 * x2**(-exp) - e2 * x1**(-exp)) / (x2**(-exp) - x1**(-exp))

def get_cbs_from_series(s, **kwargs):
    #print(s)
    X = s.index.values
    E = s.values
    return get_cbs_from_values(X, E, **kwargs)
    
def plot_cbs_extrapolation(
    basis_sizes, corr_eners, *args,
    exp=3,
    ax=None,
    extrapolate=True,
    basis_inds=None,
    **kwargs
):
    '''Plot one single energy vs x^-3, where x is basis size'''
    x = 1/basis_sizes**(exp)
    
    if ax is None:
        fig, ax = pp.subplots()
    line, = ax.plot(x, corr_eners, *args, **kwargs)

    if basis_inds is None:
        basis_inds = [-2,-1]
    if extrapolate: # extrapolate from last 2 values
        cbs = get_cbs_from_pair(basis_sizes[basis_inds], corr_eners[basis_inds], exp=exp)
        ax.plot(
            (0, x[-2]), 
            (cbs, corr_eners[-2]),
            linestyle='--', color=line.get_color(),
            linewidth=line.get_linewidth(),
            marker='x',
            markevery=[0]
        )
        ax.axhline(cbs, 
                   linestyle='--', color=line.get_color(),
            linewidth=line.get_linewidth(),)
    return line, ax


