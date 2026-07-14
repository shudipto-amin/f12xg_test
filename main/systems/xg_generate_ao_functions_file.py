import argparse as ap
import os, sys
import json
from argparse import Namespace

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)
from systems import generate_inputs_and_folders as giaf
from systems import check_outputs_and_folders as coaf

parser = ap.ArgumentParser()

parser.add_argument(
    "metadata_path", 
    help="Path to the folder to metadata"
)

parser.add_argument(
        "-f", "--fname",
        required=False,
        default='ao_file.txt'
        )

def get_orbitals_info(outfile):
    with open(outfile, 'r') as f:
        for n, line in enumerate(f):
            if 'AO(A)-basis' in line:
                break
    return int(line.split()[-1])

def main(args):
    meta = giaf.read_metadata(args.metadata_path)
    args_dict = {
        "metadata_path": args.metadata_path,
        "dry_run": False,
        "output": None,
    }
    args_ns = ap.Namespace(**args_dict)

    header = 'basis_set num_aos'
    lines_to_write = [header]
    for infiles, folder_path, _, kwargs in giaf.generate_file_paths(args_ns, meta):
        for infile in infiles:
            if infile.endswith('.inp'): break
        outfile = coaf.get_outfile(
                infile, calctype=meta['calc_type'], outformat='out'
                )
        num_aos = get_orbitals_info(outfile)

        lines_to_write.append(f"{kwargs['bases']} {num_aos}")

    content_to_write = '\n'.join(lines_to_write) + '\n'

    write_path = os.path.join(
            os.path.dirname(args.metadata_path), args.fname
            )
    with open(write_path, 'w') as f:
        f.write(content_to_write)
                              

if __name__ == '__main__':
    args = parser.parse_args()

    print(args)
    main(args)
