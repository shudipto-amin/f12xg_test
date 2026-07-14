import numpy as np
import json
import argparse
import itertools
import os, sys
import warnings
import pandas as pd
from argparse import Namespace

# Add parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from systems import generate_inputs_and_folders as giaf
from systems import run_inputs_and_folders as riaf
from systems import check_outputs_and_folders as coaf

import xml_output_parser as xo
import tabulate_outs as to
import glob

from typing import Any
from collections.abc import Callable

parser = argparse.ArgumentParser(
    description="Tabulates ouptputs using metadata"
)

parser.add_argument(
    "metadata_path",
    help="Path to metadata"
)
parser.add_argument(
    "--enertypes",
    nargs="+",
    help="List of energy types to extract (default: total energy, correlation energy)",
)
parser.add_argument(
    "--outtype",
    help="output type",
    default="*.out"
)

parser.add_argument(
    "--overwrite",
    help="overwrite existing data file (no effect if none exist)",
    action='store_true'
)
parser.add_argument(
    "--print_only",
    help="print output only",
    action='store_true'
)

parser.add_argument(
    "--datafile",
    help="output data file to write data to, default is `data.csv` in same folder as metadata_path"
)

parser.add_argument(
    "-r", "--relative_path",
    help="use metadata_path as start of relative path instead of current working directory.",
    action='store_true'
)
    
def _print_nested_dict(d, prefix=""):
    for key, val in d.items():
        if isinstance(val, dict):
            print(key)
            _print_nested_dict(val, prefix="   ")
            continue
        print(f"{prefix}{key:20s} {val}")

get_outfile = coaf.get_outfile

def update_dict(df_dict, kwargs):
    for key, val in kwargs.items():
        if key not in df_dict:
            df_dict[key] = []
        df_dict[key].append(val)


def metadata_to_DataFrame(
        metadata_path, 
        out_parsers: dict[str, Callable] | None = None,
        path_relative_to_metadata=False):
    """
    out_parsers must be of format:
        {<column_name> : Callable}
    """
    meta = giaf.read_metadata(metadata_path)
    mega_kwargs = {}
    for infiles, folder_path, _, dkwargs in giaf.generate_file_paths(
            metadata_path, meta, args_type='FilePath'):
        [infile] = infiles
        #print(dkwargs)
        dkwargs['outfile'] = coaf.get_outfile(infile)
        if path_relative_to_metadata:
            dkwargs['outfile'] = os.path.relpath(
                    dkwargs['outfile'], os.path.dirname(metadata_path)
                    )
            
        if out_parsers is not None:
            for key, func in out_parsers.items():
                func_output = func(dkwargs['outfile'])
                if isinstance(func_output, dict):
                    for k, val in func_output.items():
                        dkwargs[k] = val
                else:
                    dkwargs[key] = func_output

        for key, val in dkwargs.items():
            if key in mega_kwargs:
                mega_kwargs[key].append(val)
            else:
                mega_kwargs[key] = [val]

    full_df = pd.DataFrame(mega_kwargs)
    return full_df
    
def main(args):
    print ('>>> ARGUMENTS PROVIDED')
    _print_nested_dict(vars(args))
    #_print_nested_dict(meta)

    df = metadata_to_DataFrame(args.metadata_path, path_relative_to_metadata=args.relative_path) 
    return df

def write_to_csv(df, args):
    if args.datafile:
        datafile = args.datafile
    else:
        datafile = os.path.join(
            os.path.dirname(args.metadata_path), 'data.csv'
        )
    if os.path.exists(datafile):
        if args.overwrite:
            print(f"Print overwriting {datafile}")
            df.to_csv(datafile, index=False)
        else:
            print(f"Datafile already exists: {datafile}")
    else:
        print(f"Writing to {datafile}")
        df.to_csv(datafile ,index=False)
    
if __name__ == '__main__':
    args = parser.parse_args()
    df = main(args)
    if args.print_only:
        print(df.to_string())
    else:
        write_to_csv(df, args)
       
