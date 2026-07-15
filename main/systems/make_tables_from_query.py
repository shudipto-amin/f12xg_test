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
        'baseFile', help="Path to base.json (bases_families, system_type, replace, query_dict_file, ...)"
        )
parser.add_argument(
        '--system_type', required=True,
        help="Key into base.json's 'system_type' dict; selects the pivot index shape"
        )
parser.add_argument(
        '--bases_family', required=True,
        help="Key into base.json's 'bases_families' dict; selects the basis set list"
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

def resolve_query_dict_file(queryData, queryFile_path):
    """
    If queryData has a 'query_dict_file' key, load 'query_dict' from it
    (path resolved relative to queryFile_path's real location, so this
    works transparently through symlinks).
    """
    if "query_dict_file" in queryData:
        base_dir = os.path.dirname(os.path.realpath(queryFile_path))
        qd_path = os.path.join(base_dir, queryData.pop("query_dict_file"))
        with open(qd_path) as f:
            queryData["query_dict"] = json.load(f)
    return queryData

def load_base_config(base_path):
    with open(base_path) as f:
        base = json.load(f)
    for key in ("system_type", "bases_families"):
        if key not in base:
            parser.error(f"'{key}' not found in {base_path}")
    return base

def build_query_data(base, base_path, system_type, bases_family):
    if system_type not in base["system_type"]:
        parser.error(
            f"system_type '{system_type}' not found in {base_path}'s "
            f"'system_type' (choices: {list(base['system_type'])})"
        )
    if bases_family not in base["bases_families"]:
        parser.error(
            f"bases_family '{bases_family}' not found in {base_path}'s "
            f"'bases_families' (choices: {list(base['bases_families'])})"
        )

    queryData = {
        "filters": {"bases": base["bases_families"][bases_family]},
        "pivot_rules": {
            "index": base["system_type"][system_type],
            "columns": base.get("pivot_columns", ["basis_sizes"]),
            "values": base.get(
                "pivot_values", ["Correlation Energy", "Reference Energy"]
            ),
        },
    }
    if "replace" in base:
        queryData["replace"] = base["replace"]
    if "query_dict_file" in base:
        queryData["query_dict_file"] = base["query_dict_file"]
    elif "query_dict" in base:
        queryData["query_dict"] = base["query_dict"]
    else:
        parser.error(f"{base_path} must contain either 'query_dict' or 'query_dict_file'")

    queryData = resolve_query_dict_file(queryData, base_path)
    return queryData

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

    base = load_base_config(args.baseFile)
    queryData = build_query_data(base, args.baseFile, args.system_type, args.bases_family)

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
