import argparse
import json
import os

import _interaction_functions as IF

parser = argparse.ArgumentParser(
        description="""Combine a dimer + two monomer bse_data*.csv files into
        dimer_and_monomer*.csv, with interaction-energy/CBS-extrapolation
        columns added."""
        )

parser.add_argument(
        'mono1_dir', help="Monomer 1 directory (e.g. 'ne')"
        )
parser.add_argument(
        'mono2_dir', help="Monomer 2 directory (e.g. 'ar')"
        )
parser.add_argument(
        'dimer_dir', help="Dimer directory (e.g. 'ne_ar')"
        )
parser.add_argument(
        'method_dir', help="Method subdirectory name; must be a key in base.json's 'methods'"
        )
parser.add_argument(
        '--bases_family', required=True,
        help="Key into base.json's 'bases_families'; infers basename/outbasename (e.g. valence, core-valence)"
        )
parser.add_argument(
        '--base_json', default='queryFiles/base.json',
        help="Path to base.json (default: queryFiles/base.json)"
        )
parser.add_argument(
        '--mono1_name', default=None,
        help="Label for monomer 1's rows; defaults to title-case of mono1_dir"
        )
parser.add_argument(
        '--mono2_name', default=None,
        help="Label for monomer 2's rows; defaults to title-case of mono2_dir"
        )
parser.add_argument(
        '-d', '--debug',
        help="print sysd and combined dataframes before writing",
        action='store_true'
        )


def load_base_config(base_path):
    with open(base_path) as f:
        base = json.load(f)
    for key in ("system_type", "methods", "bases_families"):
        if key not in base:
            parser.error(f"'{key}' not found in {base_path}")
    return base


def resolve_method_shapes(base, base_path, method_dir):
    if method_dir not in base["methods"]:
        parser.error(
            f"method_dir '{method_dir}' not found in {base_path}'s "
            f"'methods' (choices: {list(base['methods'])})"
        )
    suffix = base["methods"][method_dir]
    mono_shape_key = f"monomer{suffix}"
    dimer_shape_key = f"dimer{suffix}"
    for shape_key in (mono_shape_key, dimer_shape_key):
        if shape_key not in base["system_type"]:
            parser.error(
                f"'{shape_key}' (derived from methods['{method_dir}']='{suffix}') "
                f"not found in {base_path}'s 'system_type' (choices: {list(base['system_type'])})"
            )
    return mono_shape_key, dimer_shape_key


def resolve_bases_family(base, base_path, bases_family):
    if bases_family not in base["bases_families"]:
        parser.error(
            f"bases_family '{bases_family}' not found in {base_path}'s "
            f"'bases_families' (choices: {list(base['bases_families'])})"
        )


def default_name_from_dir(dir_path):
    return os.path.basename(dir_path.rstrip('/')).title()


def bases_family_to_filename_stem(bases_family):
    return bases_family.replace('-', '_')


def build_sysd(args, base):
    mono1_name = args.mono1_name or default_name_from_dir(args.mono1_dir)
    mono2_name = args.mono2_name or default_name_from_dir(args.mono2_dir)

    mono_shape_key, dimer_shape_key = resolve_method_shapes(base, args.base_json, args.method_dir)
    resolve_bases_family(base, args.base_json, args.bases_family)

    stem = bases_family_to_filename_stem(args.bases_family)
    basename = f'bse_data_{stem}.csv'
    outbasename = f'dimer_and_monomer_{stem}'

    header = [0, 1]
    mono_index_col = list(range(len(base['system_type'][mono_shape_key])))
    dimer_index_col = list(range(len(base['system_type'][dimer_shape_key])))

    outer_index = next(
        (k for k in base['system_type'][dimer_shape_key] if k not in ('core', 'distances')),
        None,
    )

    sysd = dict(
        mono1_name=mono1_name, mono2_name=mono2_name,
        mono1_dir=args.mono1_dir, mono2_dir=args.mono2_dir,
        dimer_dir=args.dimer_dir, method_dir=args.method_dir,
        basename=basename, outbasename=outbasename,
        mono_kwargs2=dict(header=header, index_col=mono_index_col),
        dimer_kwargs2=dict(header=header, index_col=dimer_index_col),
    )
    return sysd, outer_index


def main(args):
    base = load_base_config(args.base_json)
    sysd, outer_index = build_sysd(args, base)

    if args.debug:
        print(json.dumps(sysd, indent=2))

    metad, dfs_by_core = IF.prepare_and_combine_dataframes_from_files(sysd)

    if args.debug:
        for metad_dbg, cdf in IF.get_combined_tables(metad, dfs_by_core, outer_index=outer_index):
            print(f"--- core: {metad_dbg['core']} ---")
            print(cdf.tail().to_string())

    IF.write_combined(metad, dfs_by_core, outer_index=outer_index)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
