import pandas as pd
import numpy as np
import functions_for_analyze as ffa

def get_HF_and_best_from_multimer_df(df, key1=None, key2=None):
    #dimer_df = df.loc['Dimer distances']
    #distances = dimer_df.index.values

    if key1 is None:
        key1 = ('Correlation Energy', 'BSE')
    if key2 is None:
        key2 = ('Reference Energy', '5')

    
    #display(dimer_df[key1])
    #display(dimer_df[key2])

    HF_ener = df[key2]
    best_energy = HF_ener + df[key1]

    return HF_ener, best_energy

def get_inter(df, totkey=None, sumkey=None):
    if totkey is None:
        totkey = ('HF + ', 'CorrE(CBS)')
    if sumkey is None:
        sumkey = ('Monomers','Sum')

    dfsum = df.loc[sumkey]
    dfdim = df.xs(key='Dimer distances') 
    dfie = dfdim[totkey] - dfsum[totkey]
    return dfie.index.values.astype(np.float16), dfie.values

def get_inter_from_distance_proxy(df, totkey=None, monomer_sum_distance=9999.0):
    """
    Quick-and-dirty interaction energy for systems with no separate monomer
    bse_data files yet: use the same (dimer-only) table's own row at
    `monomer_sum_distance` as a stand-in for a true monomer sum, instead of
    loading/summing separate monomer files (as combine_systems/get_inter do).

    `df` must be indexed purely by 'distances' (already sliced down to a
    single core/gamma_set/etc.) and have `totkey` as a column.
    """
    if totkey is None:
        totkey = ('HF + ', 'CorrE(CBS)')

    distances = df.index.get_level_values('distances').astype(float)
    is_proxy = distances == float(monomer_sum_distance)

    proxy_sum = df.loc[is_proxy, totkey].iloc[0]
    dimer = df.loc[~is_proxy]

    dfie = dimer[totkey] - proxy_sum
    return dimer.index.get_level_values('distances').values.astype(np.float16), dfie.values

def get_cbs_data(
        df, distance, exp=3
    ):
    dfd = df.xs('Dimer distances').xs('Correlation Energy', axis=1)
    dfd = dfd.loc[distance]
    basis_sizes_inv = []
    for x in dfd.index:
        try:
            val = 1 / float(x)**exp
        except:
            val = 0
        basis_sizes_inv.append(val)

    corr_eners = dfd.values
    return np.array(basis_sizes_inv), corr_eners


def get_combined_outfile_name(sysd):
    return f'./{sysd['dimer_dir']}/{sysd['method_dir']}/{sysd['outbasename']}_{sysd['core'].replace(' ', '_')}.csv'
    
def get_combined_tables(metad, dfs_by_core, outer_index=None):
    for core in dfs_by_core:
        cdf = ffa.MakeTables.combine_systems(*dfs_by_core[core], outer_index=outer_index)
        _, cbs_df = get_HF_and_best_from_multimer_df(cdf)
        
        cdf['HF + ','CorrE(CBS)'] = cbs_df
        #print(core)
        #display(cdf.tail())
        metad['core'] = core

        yield metad, cdf

def write_combined(metad, dfs_by_core, *args, **kwargs):
    for metad, cdf in get_combined_tables(metad, dfs_by_core, *args, **kwargs):
        
        fname = get_combined_outfile_name(metad)
        print(f"Writing {fname}")
        ffa.MakeTables.write_metacsv(
            metad, cdf, 
            fname
        )

def check_meta_and_dfs(metad, dfs_by_core):
    print(json.dumps(metad, indent=2))
    for core in dfs_by_core:
        pad.header(2, core)
        for df in dfs_by_core[core]:
            display(df.tail(3))

def collect_interaction_data(dfs, expanded_filters, func=get_inter, **func_kwargs):
    """
    Build plot-ready data from `dfs` using expanded filter dictionaries.

    Parameters
    ----------
    dfs : dict
        {
            core: {
                "meta": dict,
                "df": pandas.DataFrame,
            },
            ...
        }

    expanded_filters : list[dict]
        Each filter must contain:
            - "core": key into dfs
            - "df_key": column/key passed to func(..., totkey=...)

    get_inter_func : callable
        Function with signature:
            func(df, ...)

    Returns
    -------
    list
        [
            [xdata, ydata, labels],
            ...
        ]
    """
    data = []

    for filt in expanded_filters:
        core = filt["core"]
        if "func_kwargs" in filt:
            func_kwargs.update(filt['func_kwargs'])

        df = dfs[core]["df"]

        xdata, ydata = func(df, **func_kwargs)
        #xdata = y.index.values
        #ydata = y.values

        labels = {}
        for key, val in filt.items():
            if isinstance(val, dict):
                labels.update(val)
            else:
                labels[key] = val

        data.append([xdata, ydata, labels])

    return data

def get_cbs_data(
        df, distance=None, exp=3
    ):
    dfd = df.xs('Dimer distances').xs('Correlation Energy', axis=1)
    if distance is None:
        distance = dfd.index.values[-1]
        
    s = dfd.loc[distance]
    basis_sizes_inv = []
    for x in s.index:
        try:
            val = 1 / float(x)**exp
        except:
            val = 0
        basis_sizes_inv.append(val)

    corr_eners = s.values
    return np.array(basis_sizes_inv), corr_eners

def extend_meta(meta1, meta2):
    for key, val in meta2.items():
        if key in meta1:
            if meta1[key] != val:
                if isinstance(meta1[key], list):
                    meta1[key].append(val)
                else:
                    meta1[key] = [meta1[key], val]
        else:
            meta1[key] = val
            
def prepare_and_combine_dataframes_from_files(sysd):
    """
    This is specifically for combining different csv files and getting 
    interaction energy

    Arguments:
        sysd : dict
        example:
        ```
        sys_dict = dict(
            mono1_name = 'Ar',
            mono2_name = 'Ne',
            mono1_dir = 'ne/',
            mono2_dir = 'ar/',
            method_dir = 'dfmp2',
            basename = '{sysd['basename']}'
            )
        ```
    """
    method = sysd['method_dir']
    mono1_name = sysd['mono1_name']
    mono2_name = sysd['mono2_name']
    mono1_dir = sysd['mono1_dir']
    mono2_dir = sysd['mono2_dir']

    method_folder = f'{sysd['dimer_dir']}/{method}/'

    dimer_bse_datafile = f'{method_folder}/{sysd['basename']}'
    mono1_bse_datafile = f'{mono1_dir}/{method}/{sysd['basename']}'
    mono2_bse_datafile = f'{mono2_dir}/{method}/{sysd['basename']}'
    
    #print(dimer_bse_datafile)
    if 'mono_kwargs2' in sysd:
        mono_kwargs2 = sysd['mono_kwargs2']
    else:
        mono_kwargs2 = dict(header=[0,1], index_col=[0])
    if 'dimer_kwargs2' in sysd:
        dimer_kwargs2 = sysd['dimer_kwargs2']
    else:
        dimer_kwargs2 = dict(header=[0,1], index_col=[0,1])

    
    metad, dimer = ffa.MakeTables.read_metacsv(dimer_bse_datafile,        
                           kwargs2=dimer_kwargs2    
                           )                                            
                                                                       
    meta1, mono1 = ffa.MakeTables.read_metacsv(mono1_bse_datafile,        
                           kwargs2=mono_kwargs2
                           )                                            
    
    meta2, mono2 = ffa.MakeTables.read_metacsv(mono2_bse_datafile,        
                           kwargs2=mono_kwargs2
                           )                                            

    
    mono1 = pd.concat([mono1], keys=[mono1_name])
    mono2 = pd.concat([mono2], keys=[mono2_name])
    
    metad = dict(metad.values)
    meta1 = dict(meta1.values)
    meta2 = dict(meta2.values)
    
    for meta in (meta1, meta2, sysd):
        extend_meta(metad, meta)

    # Add aditional keys to metad
    metad['bse_data_files'] = [dimer_bse_datafile, mono1_bse_datafile, mono2_bse_datafile]
                    
    cores = list(set(dimer.index.get_level_values(0)))
    dfs_by_core = {}
    
    for core in cores:
        dfs_by_core[core] = [
            dimer.loc[core], 
            mono1.xs(key=core, level='core'), 
            mono2.xs(key=core, level='core')
        ]    
    return metad, dfs_by_core
