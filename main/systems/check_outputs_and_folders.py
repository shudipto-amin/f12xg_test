import numpy as np
import json
import argparse
import itertools
import os, sys
import warnings
import pandas as pd
from argparse import Namespace

# Add parent directory (project root) to sys.path
sys.path.append(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
            )
        )

from systems import generate_inputs_and_folders as giaf
from systems import run_inputs_and_folders as riaf

import xml_output_parser as xo
import tabulate_outs as to
import glob

parser = argparse.ArgumentParser(
    description="Checks ouptputs using metadata and run log"
)

parser.add_argument(
    "metadata_path",
    help="Path to metadata"
)

parser.add_argument(
    "--outformat",
    help="output format (eg: 'out', 'xml', etc. The default is to infer from calctype.",
    nargs=1,
    default='out',
)

parser.add_argument(
    "--update_logfile",
    help="Update log files",
    action='store_true'
)

parser.add_argument(
    "--verbose",
    help="Print to std out verbosely (good for debugging)",
    action='store_true'
)

parser.add_argument(
    "--remove_fail",
    help="Remove failed runs from log file",
    action='store_true'
)

def get_outfile(infile, calctype='xg', outformat=None, return_all_matches=False, verbose=False):
    """
    Given an input file path (e.g. 'path/to/file.inp'),
    find all matching output files ('path/to/file.*.out').
    If multiple exist, issue a warning but return the latest one.
    """
    # Split path and base filename (without extension)
    base, _ = os.path.splitext(infile)
    if outformat is None:
        if calctype == 'xg':
            pattern = f"{base}.*.out"
        else:
            pattern = f"{base}.*.xml"
    else:
        pattern = f"{base}.*.*{outformat}"

    # Find matching files
    matches = glob.glob(pattern)

    if not matches:
        if verbose:
            warnings.warn(f"No matching output files found for pattern: {pattern}")
        return None
    # Sort by modification time (latest last)
    matches.sort(key=os.path.getmtime)

    if len(matches) > 1:
        if verbose:
            warnings.warn(
                f"Multiple output files found for {infile}:\n"
                + "\n".join(matches)
                + f"\nUsing latest: {matches[-1]}"
            )
    
    if return_all_matches:
        return matches
    else:
        return matches[-1]

def _print_nested_dict(d, prefix=""):
    for key, val in d.items():
        if isinstance(val, dict):
            print(key)
            _print_nested_dict(val, prefix="   ")
            continue
        print(f"{prefix}{key:20s} {val}")

def update_run_log_line(lines, query, status, remove=False):
    '''
    Update a line in run log to contain status of run
    Arguments:
        lines : <list> of lines, as obtained from inp.readlines()
        query : <string> to search and update
        status : <string> append this to line
    '''
    for n, line in enumerate(lines):
        if query in line:
            if remove:
                new_line = ''
            else:
                new_line = f"{line.replace('\n','')} {status}\n"
            break
    lines[n] = new_line

def main(args):
    def dprint(*print_args, **print_kwargs):
        "Debug printing, when verbose is true"
        if args.verbose:
            print(*print_args, **print_kwargs)

    dprint ('| ARGUMENTS PROVIDED')
    if args.verbose:
        _print_nested_dict(vars(args))
    meta = giaf.read_metadata(args.metadata_path)
    if args.verbose:
        _print_nested_dict(meta)
    args_dict = {
        "metadata_path": args.metadata_path,
        "dry_run": False,
        "output": None,
    }
    args_ns = Namespace(**args_dict)
    completed = []
    failed = []
    
    for infiles, folder_path, _, kwargs in giaf.generate_file_paths(args_ns, meta):
        for infile in infiles:
            if infile.endswith('.inp'): break


        outfiles = get_outfile(
                infile, calctype=meta['calc_type'], outformat=args.outformat,
                return_all_matches=True, verbose=args.verbose
                )
        if outfiles is not None:
            outfile = outfiles[-1]
            last_line = read_last_line(outfile)
            if 'Molpro calculation terminated' in last_line:
                completed.append(outfiles)
            else:
                failed.append((outfiles, last_line, infile, folder_path, kwargs))
        else:
            failed.append((outfiles, "!! NO OUTPUT FILE FOUND !!", infile, folder_path, kwargs))


    print("========================")
    print("   COMPLETED RUNS    ")
    print("========================")

    for outfiles in completed:
        print(outfiles[-1], end='')
        if len(outfiles) > 1:
            print(f"   # Latest of {len(outfiles)} files")
        else:
            print()
        
    print("========================")
    print("   FAILED RUNS    ")
    print("========================")

    run_logs = dict()

    for outfiles, last_line, infile, folder_path, kwargs in failed:
        if outfiles is None:
            print(f">>>> !! NO OUTPUT FOR {infile} !!")
        else:
            file = outfiles[-1]
            print('>>>>' , file, end='' )
            if len(outfiles) > 1:
                print(f"   # Latest of {len(outfiles)} files")
            else:
                print()

        dprint(  "  LAST LINE: ", last_line.rstrip('\n'))
        dprint( "  FOLDER: ", folder_path)
        dprint( "  METADATA kwargs:")
        for key, val in kwargs.items():
            dprint(f"    {key:15s} : {val}")
        
        run_log_file = os.path.join(folder_path, 'runs.log')

        dprint(run_log_file)
        if run_log_file not in run_logs:
            with open(run_log_file, 'r') as inp:
                run_logs[run_log_file] = inp.readlines()

        update_run_log_line(run_logs[run_log_file], f"{kwargs['full_file_prefix']}.", 'FAIL', remove=args.remove_fail)

    dprint('\n---------- Updated content of runs.log of failed runs -----------')
    dprint(':: To remove lines with FAIL keyword, pass `--remove_fail`')
    dprint(':: To update the logfile with the following content, pass `--update_logfile`\n')
    for run_log_file, lines in run_logs.items():
        dprint("!!!!", run_log_file)
        content = ''.join(lines)
        dprint(content)

        #run_logs[run_log_file
        if args.update_logfile:
            dprint('------------- Writing new log files -----------')
            with open(run_log_file, 'w') as out:
                out.write(content)


def read_last_line(file):
    # Source - https://stackoverflow.com/a/54278929
    # Posted by Eugene Yarmash, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-01-28, License - CC BY-SA 4.0
    with open(file, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line

if __name__ =='__main__':
    args = parser.parse_args()
    main(args)
