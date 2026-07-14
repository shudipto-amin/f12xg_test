import numpy as np
import matplotlib.pyplot as pp
import argparse as ap
import subprocess as sp
import sys
import pandas as pd
import os

import xml_output_parser as xop 
from typing import Optional, Any

parser = ap.ArgumentParser(
    description="""
    This script takes in multiple output files and prints out a
    table (pandas.DataFrame) of energies per output file. 

    RESTRICTIONS:
    * Output files MUST only be for a single point energy.
    * For standard and default, must be XML output.
    """,
    fromfile_prefix_chars='@'
        )

parser.add_argument('--outs', '-o', nargs='+',
                    help='default or standard molpro XML output files')
parser.add_argument('--xgouts', '-x', nargs='+',
                    help='XG molpro output files')
parser.add_argument(
    "--enertypes",
    nargs="+",
    help="List of energy types to extract (default: total energy, correlation energy)",
)
parser.add_argument('--input_csv', '-i', type=str,
                    help='Path to CSV file with outputs and labels'
                    )

def ener_not_found_error(outfile):
    print(f"No energy found! Output file: {outfile}")

def get_xg_energy_lines(outfile):
    start_marker = "Printing Energies step by step"
    end_marker = "F12-XG CALCULATIONS END"
    printing = False
    last_line = None
    output_lines = []
    with open(outfile, "r") as f:
        for line in f:
            last_line = line
            if start_marker in line:
                printing = True
            if printing:
                output_lines.append(line)
            if printing and end_marker in line:
                printing = False
    output_lines.append(last_line)
    return "".join(output_lines)


def get_ener(outfile, enertype='total energy', method='DF-MP2-F12', out_type="std"):
    if out_type == "std":
        ener = xop.get_xmlener(outfile, enertype=enertype, command=method) 
        return ener            
    if out_type == "xg":
        out = get_xg_energy_lines(outfile)
        if 'Molpro calculation terminated' not in out:
            ener_not_found_error(outfile)
            return None

        lines = out.split('\n')
        for line in lines[-1::-1]:
            stripped_method = method.lstrip('DF-')
            if f'{stripped_method}' in line and enertype in line:
                energy = float(line.split()[-1])
                return energy
        ener_not_found_error(outfile)


    return None

def parse_inputcsv(args):
    std_basis = []
    xg_basis = []
    df = pd.read_csv(args.input_csv, skipinitialspace=True)

    # -------------------------
    # Step 3: Update args.outs and args.xgouts from CSV
    # -------------------------
    args.outs = df.loc[df['calctype'] == 'std', 'file'].tolist()
    args.xgouts = df.loc[df['calctype'] == 'xg', 'file'].tolist()

    # -------------------------
    # Step 4: Store additional columns
    # -------------------------
    std_basis = df.loc[df['calctype'] == 'std', 'basis'].tolist()
    xg_basis = df.loc[df['calctype'] == 'xg', 'basis'].tolist()

    # Map file -> basis
    std_dict = dict(zip(args.outs, std_basis))
    xg_dict = dict(zip(args.xgouts, xg_basis))
    return df

def update(outfile: str, data, **energies: Optional[float]) -> None:
        for etype, val in energies.items():
            data[etype].append(val)
        data["labels"].append(
            os.path.basename(outfile).removesuffix(".out")
        )
        
def process_files(outfiles: list[str], energy_types, data, out_type: str = "std") -> None:
    for outfile in outfiles:
        energies = {}
        for etype in energy_types:
            energies[etype] = get_ener(outfile, enertype=etype, out_type=out_type)
        update(outfile, data, **energies)


def main(args):    
    data: dict[str, list[Optional[float]]] = {"labels": []}
    if args.input_csv:
        df = parse_inputcsv(args)
        for col in df.columns:
            data[col] = df[col].tolist()
        
    #print(args)
    #print(sys.argv)
    # Default energy types if not provided
    energy_types = args.enertypes or ["total energy", "correlation energy"]

    for etype in energy_types:
        data[etype] = []   # use energy type name directly as column header


    if len(sys.argv) <= 1:
        print("At least one output file must be provided\n")
        parser.print_help()
        sys.exit(1)


    if args.outs:
        process_files(args.outs, energy_types, data, out_type="std")

    if args.xgouts:
        process_files(args.xgouts,energy_types, data, out_type="xg")

    df = pd.DataFrame(data)
    if args.input_csv:
        df = df.drop(['labels'], axis=1)
        cols = list(df.columns)
        cols.append(cols.pop(cols.index('file')))
        df = df[cols]

    return df

if __name__ == "__main__":
    args = parser.parse_args()
    # Dynamic data container
    df = main(args)
    print(df.to_string())
