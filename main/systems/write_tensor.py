import os
import json
import argparse
import subprocess
from argparse import Namespace
import os, sys

main_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.append(main_path)
    
from systems import generate_inputs_and_folders as giaf 


from systems import run_inputs_and_folders as riaf
from systems import check_outputs_and_folders as coaf

parser = argparse.ArgumentParser(
    description="For each output file, extract the Dump of a particular tensor."
)

parser.add_argument(
    "metadata_path",
    help="Path to metadata"
)

parser.add_argument(
    "tensor_name",
    help="ITF name of tensor with indices"
)


def get_outs_and_kwargs(meta):
    args_dict = {
        "metadata_path": args.metadata_path,
        "dry_run": False,
        "output": None,
    }
    args_ns = Namespace(**args_dict)
    for infiles, folder_path, _, kwargs in giaf.generate_file_paths(args_ns, meta):
        for infile in infiles:
            if infile.endswith('.inp'): break


        outfile = coaf.get_outfile(
                infile, calctype=meta['calc_type']
                )
        yield infile, outfile, folder_path, kwargs

def parse_tensor_name(tensor_name):
    tensor_file_name = tensor_argument_name = tensor_name
    for symb in '[:]':
        tensor_file_name = tensor_file_name.replace(symb, '_')
        tensor_argument_name = tensor_argument_name.replace(symb, f'\\{symb}')
    return tensor_file_name, tensor_argument_name

def main(metadata_path):
    meta = giaf.read_metadata(metadata_path)

    for infile, outfile, folder_path, kwargs in get_outs_and_kwargs(meta):
        tensor_script = os.path.join(
                main_path, 'utilities', 'get_tensor.sh'
                )
        tensor_file_name, tensor_argument_name = parse_tensor_name(args.tensor_name)
        tensor_file = os.path.join(
                folder_path, f'tens_{tensor_file_name}.txt'
                )
        
        cmd = f"bash {tensor_script} '{tensor_argument_name}' {outfile} {tensor_file}"
        subprocess.run(f"{cmd}", shell=True)
if __name__ == "__main__":
    args = parser.parse_args()
    main(args.metadata_path)


