import numpy as np
import json
import argparse
import itertools
import os, sys
import shutil
import pandas as pd
import ast

main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(main_path)

parser = argparse.ArgumentParser(description="Generate folders and inputs")

parser.add_argument(
    "metadata_path", 
    help="Path to the folder to metadata"
)

parser.add_argument(
    "-d", "--dry_run", 
    help="Dry run",
    action="store_true", required=False
)

# ================= General code ============================ #
def safe_format(inp: str, d: dict) -> str:
    """Safely format a string with placeholders, leaving all other braces intact."""
    # Step 1: Escape all braces
    safe_inp = inp.replace('{', '{{').replace('}', '}}')
    
    # Step 2: Re-enable valid placeholders
    for key in d:
        safe_inp = safe_inp.replace('{{' + key + '}}', '{' + key + '}')
    
    # Step 3: Apply format_map with SafeDict
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    
    return safe_inp.format_map(SafeDict(d))

def read_metadata(metadata_path: str) -> dict:
    """
    Reads metadata from a file.
    """
    with open(metadata_path, 'r') as f:
        metadata =  json.load(f)

    if not isinstance(metadata['template'], list):
        metadata['template'] = [metadata['template']]

    return metadata

def write_input(template_file, kwargs, inp=None):
    with open(template_file, 'r') as tinp:
        template = tinp.read()
    input_script = safe_format(template, kwargs)
    if inp is None:
        print(input_script)
    else:
        with open(inp, 'w') as out:
            
            out.write(input_script)

def format_value(value, fmt_spec=None):
    """Apply format string like '06.3f' if specified."""
    if fmt_spec:
        try:
            return format(value, fmt_spec)
        except Exception:
            # fallback in case of bad format or non-numeric value
            return str(value)
    return str(value)

def generate_items(iterables):         
                                    
    key_to_values = {}
    key_to_keys = {}
    for key, obj in iterables.items():
        if 'iterate_with' in obj.keys():
            key_to_values[obj['iterate_with']].append(obj['values'])
            key_to_keys[obj['iterate_with']].append(key)
        else:
            key_to_values[key] = [obj['values']]
            key_to_keys[key] = [key]
        
    value_lists = [zip(*val) for val in key_to_values.values()]
    key_lists = list(itertools.chain(*key_to_keys.values()))
    for combo in itertools.product(*value_lists):
        
        params = dict(zip(key_lists, itertools.chain(*combo)))                        
        yield params                                                                   

clean_filename_dict = {
        "*" : ".",
        "(" : "_",
        ")" : "",
        "," : "-"
        }
def generate_file_paths(args, meta, args_type='Namespace'):
    """Yield (file_path, folder_path, kwargs) tuples for each parameter combination."""
    iterables = {k: v for k, v in meta.items() if isinstance(v, dict) and v.get("iterable")}

    if args_type == 'Namespace':
        working_folder = os.path.dirname(args.metadata_path)
    elif args_type == 'FilePath':
        working_folder = os.path.dirname(args)
    elif args_type == 'DirPath':
        working_folder = args
    else:
        raise ValueError(
                "args_type must be 'Namespace', 'FilePath', or 'DirPath'"
                )

    template_files = []
    for tempf in meta['template']:
        template_file = os.path.join(working_folder, tempf)
        template_files.append(template_file)
    
    def clean_filename(prefix):
        new_prefix = ''
        for c in prefix:
            if c in clean_filename_dict:
                new_prefix += clean_filename_dict[c]
            else:
                new_prefix += c
        return new_prefix
    for params in generate_items(iterables):
        path_parts = [working_folder]
        file_prefix = meta["file_prefix"]

        kwargs = {}
        for key, value in params.items():
            conf = iterables[key]
            fmt_value = format_value(value, conf.get("format"))
            prefix = conf.get("prefix", "{value}").format(value=fmt_value)
            prefix = clean_filename(prefix)
            if conf.get("subfolder"):
                path_parts.append(prefix)
            else:
                file_prefix += prefix + "_"

            kwargs[key] = fmt_value
            
        file_prefix = file_prefix.rstrip("_")
        kwargs["full_file_prefix"] = file_prefix
        folder_path = os.path.join(*path_parts)

        file_paths = []
        for n, tfile in enumerate(template_files):
            ext = tfile.split('.t')[-1]
            filename = file_prefix + "." + ext
            file_path = os.path.join(folder_path, filename)
            file_paths.append(file_path)

        yield file_paths, folder_path, template_files, kwargs


def write_generated_files(args, meta):
    """Write input files based on generated file paths."""
    non_iterables = {k: v for k, v in meta.items() if not (isinstance(v, dict) and v.get("iterable"))}
    for file_paths, folder_path, template_files, kwargs in generate_file_paths(args, meta):
        kwargs.update(non_iterables)
        for n, file_path in enumerate(file_paths):
            template_file = template_files[n]
            if args.dry_run:
                print(f"Dry-run, would write to {file_path}:")
                write_input(template_file, kwargs)
            else:
                os.makedirs(folder_path, exist_ok=True)
                write_input(template_file, kwargs, inp=file_path)

        if meta['calc_type'] == 'xg':
            gamma_2_gauss_file = os.path.join(main_path, 'f12xg_inputs', 'gamma_to_gauss.dat')
            with open(gamma_2_gauss_file, 'r') as f:
                data = json.load(f)
            write_expfile(folder_path, kwargs, args, data)
            write_maffile(folder_path, kwargs, args)

def generate_files(args, meta):
    """Backward-compatible entry point."""
    write_generated_files(args, meta)

# =================== XG specific code ===================== #
def combine_gammas(beta1, beta2):
    return round((beta1 + beta2) / 2, 2)
    
def write_expfile(folder_path, kwargs, args, data):
    if 'gamma_set' in kwargs:
        gamma_set = kwargs['gamma_set']
        gamma1, gamma2, gamma3 = [float(g) for g in gamma_set.split('_')]

    else:
        gamma1 = kwargs['gamma1']
        gamma2 = kwargs['gamma2']
        gamma3 = kwargs['gamma3']

    if gamma3 is None:
        gamma3 = combine_gammas(gamma1, gamma2)
    file_content = []
    file_content.append(
        f"# gamma_1 = {gamma1:4.2f}; " + \
        f"gamma_2 = {gamma2:4.2f}; gamma_3 = {gamma3:4.2f}"
    )
    file_content.append("# gamma_index type_of_data data")

    all_gammas = [gamma1, gamma2, gamma3]
    for n, gamma in enumerate(all_gammas):
        i = n + 1
        dat = data[f"{gamma:4.2f}"]
        alphas = dat['alphas']
        coeffs = dat['coeffs']

        file_content.append(f"{i} nCo 1")
        file_content.append(f"{i} Gam {gamma:4.2f}")
        file_content.append(f"{i} Exp {','.join((str(a) for a in alphas))}")
        file_content.append(f"{i} Coe {','.join((str(a) for a in coeffs))}")

    
    target_fname = os.path.join(folder_path, kwargs['xg_expfilename'])

    if args.dry_run:
        print(f"Dry-run, would write to {target_fname}:")
        print('\n'.join(file_content) + '\n')
    else:
        with open(target_fname, 'w') as out:
            out.write('\n'.join(file_content) + '\n')


def write_maffile(folder_path, kwargs, args):
    working_folder = os.path.dirname(args.metadata_path)
    ao_stats_file = os.path.join(working_folder, kwargs["xg_ao_functions_file"])
    ao_stats = pd.read_csv(ao_stats_file, delimiter=r'\s+')
    df = ao_stats[ao_stats["basis_set"] == kwargs['bases']]
    num_aos = df['num_aos'].values[0]
    gamma2_inds = ast.literal_eval(df['gamma2_inds'].values[0])

    if 'xg_maf_type' in kwargs:
        maf_type = kwargs['xg_maf_type']
    else:
        maf_type = 2
    if maf_type == 1:
        info = [str(g) for g in gamma2_inds]
        info_len = len(info)
        info_str = ' '.join(info)
    else:
        info = ['2' if i in gamma2_inds else '1' for i in range(num_aos)]
        info_len = len(info)
        info_str = ' '.join(info)
    maf_content = f"type {maf_type}\n" \
            f"len  {info_len}\n" \
            f"info {info_str}\n"
    dst = os.path.join(folder_path, kwargs['xg_maffilename'])
    if args.dry_run:
        print(f"Dry-run, would write the following to {dst}")
        print(maf_content)
    else:
        with open(dst, 'w') as out:
            out.write(maf_content)


# ==========================================================

if __name__ == "__main__":
    args = parser.parse_args()
    metadata = read_metadata(args.metadata_path)
    generate_files(args, metadata)
    
        
