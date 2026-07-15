> This is the file I gave to chatgpt to generate the mmd scripts

# Project goals

Test and benchmark F12XG calculations against standard F12 and non-F12.
Different approximations and parameters such as basis sets, correlations factors, 
core approximations, etc are explored.

# 1. Initial Setup - generating inputs
* Create a system folder.
* Create a subfolder for each calculation method with:
    - `metadata.json`
    - `*.tinp` template input files
    - Other files (only for XG runs)
* Generate inputs files with:
    - `python generate_inputs_and_folders.py <path_to_metadata>` -> nested subfolders with input files

# 2. Run the input scripts
`python run_inputs_and_folders.py <path_to_metadata>` -> runs generated inputs and logs the run.

# 3. Check or modify after running
* To stagger expensive jobs use the script:
    - `../utilities/stagger_750_jobs.sh` -> change execution times of already submitted jobs
* To see if there are any completed outputs, and if the completed ones were successful:
    - `python check_outputs_and_folders.py <path_to_metadata>` -> prints completion status with full path.

# 4. Collect data in csv files
* `python tabulate_outputs_and_folders.py -r <path_to_metadata>` -> `data.csv` record type
  table with all input parameters, and corresponding output file names.
* Make a `queryFile*.json` or symlink existing one from `queryFiles/`
    - Should contain a `query_dict`
    - Optional but almost necessary `filters`, `replace`, and `pivot_rules` 
    - See `querFiles/` for examples.

## 4.1 General tables
* `python make_tables_from_query.py <path to data.csv> <queryFile> [--write FILE]` -> print or write queried data according to `pivot_rules`
## 4.2 Table for interactions
1. For each set of filtering and pivoting parameters, like different basis sets, create a new `queryFile`  
    - `python make_tables_from_query.py <path to data.csv> <queryFile> --add_bse --write "bse_data[ID].csv"` -> add bse column and then write
2. Do step 1. for each system (monomer1, monomer2, and dimer)
    - The dimer queryFile will have distances in index, but monomers will not
3. Combine the different `bse_data[ID].csv`
    - `Make_Tables.ipynb` - uses `functions_for_analyze.MakeTables.combine_interaction_energies`
    - Outputs: `f'./{system}/{method}/dimer_and_monomer_wC_{core.replace(' ', '_')}.csv'`
    - TODOS:
        * Right now I have to do this by hand, maybe can put the function in script file (ffa? IE?)
        * The system and method are typed into the notebook - need to make that a parameters as well
        * I think a json file for which csvs to use, which are the monomer names, etc would be bse_data

## 5. Final visualisation
1. `Plot_from_Tables.ipynb`




