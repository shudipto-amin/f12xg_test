
import os
import json
import argparse
import subprocess
from argparse import Namespace
import os, sys
import pandas as pd

main_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)
sys.path.append(main_path)
    
from systems import generate_inputs_and_folders as giaf 
from systems import check_outputs_and_folders as coaf


parser = argparse.ArgumentParser(
    description="Parse comparable outfiles"
)

parser.add_argument(
    "comparable_path",
    help="Path to comparable json"
)

def main(args):
    with open(args.comparable_path) as f:
        comparables = json.load(f)

    dirname = os.path.dirname(args.comparable_path)
    ref_metadata_path = os.path.join(dirname, comparables['ref_metadata'])
    cur_metadata_path = os.path.join(dirname, comparables['cur_metadata'])

    ref_metadata = giaf.read_metadata(ref_metadata_path)
    cur_metadata = giaf.read_metadata(cur_metadata_path)
        
    #print(comparables['keys_and_values_to_compare'])

    """# ====== NOTE TO SELF ============#
    I realized it would be better to filter the dictionary first:
    ref_data based on ref_fixed_keys, and then keys_and_values_to_compare for both 
    ref_data and cur_data.

    I thougth doing simultaneous iteration doesn't work, becase XG and default have different numbers of 
    total files.

    So instead, trying to make dataframe first and then filter.
    """
    for key, value in comparables['ref_fixed_keys'].items():
        ref_metadata[key]["values"] = value

    mappings = dict()
    key_maps = dict()

    for key, sub_dict in comparables['keys_and_values_to_compare'].items():
        if sub_dict['values'] == "identical": 
            ref_key = cur_key = key
            ref_values = cur_values = ref_metadata[key]["values"]
        else:
            ref_key = sub_dict['ref_key']
            ref_values = sub_dict['values']['ref']

            cur_key = key
            cur_values = sub_dict['values']['cur']
        
        key_maps[cur_key] = ref_key
        ref_metadata[ref_key]["values"] = ref_values
        cur_metadata[cur_key]["values"] = cur_values

        mappings[key] = {
            val1 : val2 for val1, val2 in zip(cur_values, ref_values)
            }
    print("MAPPINGS:\n", mappings)
    #print(json.dumps(ref_metadata, indent=4))
    #print(json.dumps(cur_metadata, indent=4))

    ref_df = make_DataFrame(ref_metadata_path, ref_metadata, args_type='FilePath')  
    ref_df = clean_df(ref_df, ref_metadata)
    cur_df = make_DataFrame(cur_metadata_path, cur_metadata, args_type='FilePath')   
    cur_df = clean_df(cur_df, cur_metadata)
    #print(ref_df)
    #print(cur_df)
    data_frame_maps = {
                f'_{col}' : cur_df[col].map(maps) for col, maps in mappings.items()
                }
    cur_df2 = cur_df.assign(
            **data_frame_maps
            )

    #print(cur_df2)
    mdf = cur_df2.merge(
            ref_df,
            left_on=[f'_{col}' for col in mappings],
            right_on=[key_maps[col] for col in mappings],
            how = 'left',
            suffixes=[comparables['ref_suffix'], comparables['cur_suffix']]
            ).drop(columns=[f'_{col}' for col in mappings])
    mdf_print = mdf.loc[:, mdf.nunique() > 1]
    mdf_print = mdf_print[sorted(mdf_print.columns, key=lambda x: f"zz{x}" if 'outfile' in x else x)]
    print(mdf_print.to_string())
            

def clean_df(df, metadata):
    columns = [col for col in df.columns]
    for col in df.columns:
        if col not in metadata: continue
        if 'prefix' not in metadata[col]: continue
        if not metadata[col]['prefix']:
            columns.remove(col)
    return df[columns]

def make_DataFrame(*args, **kwargs):
    mega_kwargs = {}
    for infiles, folder_path, _, dkwargs in giaf.generate_file_paths(*args, **kwargs):
        [infile] = infiles
        #print(dkwargs)
        dkwargs['outfile'] = coaf.get_outfile(infile)
        for key, val in dkwargs.items():
            if key in mega_kwargs:
                mega_kwargs[key].append(val)
            else:
                mega_kwargs[key] = [val]

    full_df = pd.DataFrame(mega_kwargs)
    #full_df = pd.concat(dfs, ignore_index=True)
    return full_df
    


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
