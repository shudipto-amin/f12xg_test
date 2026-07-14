import pandas as pd
import numpy as np
import sys
import os
import argparse
import json

# Add parent directory (project root) to sys.path
main_path = os.path.join(
                os.path.dirname(__file__), ".."
                )
sys.path.append(
        os.path.abspath(main_path)
        )

from systems import generate_inputs_and_folders as giaf
from systems import run_inputs_and_folders as riaf
from systems import check_outputs_and_folders as coaf

from systems import functions_for_analyze as ffa
import single_output_parser as sop

parser = argparse.ArgumentParser(
        description="""Table generating script"""
        )

parser.add_argument(
        'dataFile', help='path to `data.csv` or whatever'
        )

parser.add_argument(
        'queryFile', help="JSON file containing query dictionary"
        )
parser.add_argument(
        '-w', '--write',
        help="Write to a file",
        nargs='?',
        const=True,
        default=False
        )
parser.add_argument(
        '-d', '--debug',
        help="print out a bunch of stuff for debugging.",
        action='store_true'
        )
parser.add_argument(
        '--add_bse', help="Add BSE",
        action="store_true"
        )
parser.add_argument(
        '--list', help="list all available functions for --add_func (BETA)",
        action='store_true'
        )

def get_meta_for_csv(datafile, queryData):
    meta_for_csv = dict(
            Raw_Datafile= os.path.relpath(datafile, main_path),
            **queryData['filters']
            )
    return meta_for_csv



def main(raw_df, queryData):
    query_dict = queryData['query_dict']
    filters = queryData['filters']
    pivot_rules = queryData['pivot_rules']

    enerdf = ffa.parse_outfiles_in_df(raw_df, query_dict)
    if args.debug:
        print(enerdf.to_string())
    df = ffa.filter_df(enerdf, filters)
    if "replace" in queryData:
        for key in queryData['replace']:
            df.loc[:,key] = df[key].replace(queryData['replace'][key])

    pdf = pd.pivot(df, **pivot_rules)   

    return pdf

def add_BSE(pdf):
    """
    Assumes input DataFrame is pivotted so that we have
    Basis sizes as columns
    """
    exp = 3
    
    pdf['Correlation Energy', 'BSE'] = pdf['Correlation Energy'].apply(
        ffa.get_cbs_from_series, axis=1, exp=exp
    )

    pdf['Reference Energy', 'BSE'] = pdf['Reference Energy'].apply(
        ffa.get_cbs_from_series, axis=1, HF=True
    )

    pdf = pdf.sort_index(axis=1)
    return pdf

def print_or_write(args, pdf, queryData):
    meta_for_csv = get_meta_for_csv(args.dataFile, queryData)

    if args.write:
        if isinstance(args.write, str):
            csvout = args.write
        else:
            csvout = os.path.join(
                    os.path.dirname(args.dataFile),
                    'pivot_table.csv'
                    )
        ffa.MakeTables.write_metacsv(meta_for_csv, pdf, csvout)
    else:
        print(json.dumps(meta_for_csv, indent=4))
        print(pdf.to_string())
           
def list_add_funcs():
    for key, value in locals().items():
        #if callable(value) and key.startswith("add_"):
            print(key, value)

if __name__ == "__main__":
    args = parser.parse_args()
    if args.list:
        list_add_funcs()
        sys.exit()

    with open(args.queryFile) as f:
        queryData = json.load(f)
    
    if args.debug:
        print(json.dumps(queryData, indent=4))
    
    
    raw_df = ffa.get_data(args.dataFile, make_relative=True).fillna('')
    ffa.assign_basis_size(raw_df)
    
    pdf = main(raw_df, queryData)
    if args.debug:
        print(pdf.to_string())

    if args.add_bse:
        pdf = add_BSE(pdf)
    print_or_write(args, pdf, queryData)
