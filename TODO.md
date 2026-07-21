# TODO

- [ ] **HIGH PRIORITY** XG output verification, i.e. the `*.out` files in the deepest xg/* subfolder (known hereon as "output folder"):
    - [x] Must contain the line `F12-XG CALCULATIONS BEGIN` and, on a separate
          line, `F12-XG CALCULATIONS END`
    - [x] For anything in the `interactions/` folder (dimers and monomers alike),
          `xg.maf` in output folder should contain `type 1\nlen 1\ninfo 0\n`
        - [x] This should also match with `"xg_maf_type" : 1"` in the metadata.json file.
    - [x] `grep -A 1 m_assignment_info <outfile>` — second line should be `0`
    - [x] Must contain `DEBUG: case 1 for m_assignment_type` but NOT
              `DEBUG: case [0,2] for m_assigment_type`
    - [x] For lines after `==== Running ListGeminalAssignment()` section (till the next `====` section break):
        - If `atom index: ` is
            - `0` the following line should contain `GammaGroups: (m_BasisSubset)` followed by `1` or whitespace.
            - (anything else) the following line should contain `GammaGroups: (m_BasisSubset)` followed by `2` or whitespace.
    - [x] Check difference between tensors:
        - `grep -A 1 'Difference between F1.1.*C\[' <outfile>` should
            - for Monomers, second line should be '0' regardless of gamma
            - for dimers, if the gammas are the same, then they should be small values
              where small is less than e-11 (or some tolerance value)
    - [ ] Check the new outputs (per the XG output verification checks above)
- [ ] Redo generation of the datafiles (tabulate, Stage 1, Stage 2, etc.)
      and inspect them in `Interaction_Analysis.ipynb`
- [ ] Fix notebooks broken by the `_Plot_from_Tables.py`/`_interaction_functions.py`/
      `Make_Interaction_Tables.py` -> `__visuals__/matplot.py` + `_Interaction_Analysis.py`
      consolidation (see `Interaction_Analysis.ipynb` for the new import pattern:
      `from __visuals__ import matplot` + `import _Interaction_Analysis as IA`,
      calls `PFT.`/`IF.`/`MIT.` -> `matplot.`/`IA.`):
    - [ ] `Plot_from_Tables.ipynb`
    - [ ] `Make_Tables.ipynb`
    - [ ] `Test_Make_Tables.ipynb`
    - [ ] `data.csv_inspector.ipynb`

# COMPLETED
- [x] Migrate `ne_ar/xg/` to the `base.json`/`system_type` pipeline (see
      README.md "Known gaps"). Its old query config used `core_names`
      filters and a `gamma_set` pivot index instead of `system_type`, so it
      needs its own mapping worked out before it fits the current scheme.
- [x] Once `ne_ar/xg/` is migrated (above), extend in a quick-and-dirty way
      `Plot_from_Interaction_Tables.ipynb` to cover XG the same way it now
      covers F12: work out XG's `outer_index` shape (its  `gamma_set` axis
      is similar to `gammas` F12 `gammas` axis) and reuse/extend `PFT.get_dfs`'s single-slice
      extraction (`gamma=...`) so the existing interaction-energy plotting
      cells work unmodified for XG too.
    - [x] For now, do quick and dirty trick on dimer only xg
    - [x] Continue making new xg column for HF4 + CorrE(4)
    - [x] Plot and compare
- [x] Run XG Monomer for Ne, using same metadata.json as ne_ar minus distances
    - [x] Tabulate
- [x] Run Tabulate for Ar
- [x] Do XG properly, but keep the proxy function as an alternative for any dataframe
- [x] Reorganize the folders - make an interactions folder for all the dimer and monomers.
    - [x] Consider either putting dimer/ ne/ ar/ inside an ne_ar/ folder, and likewise for others
- [x] Add a section to `Interaction_Analysis.ipynb` (renamed from
      `Plot_from_Interaction_Tables.ipynb`) comparing the sum of F12 monomer
      values to XG's dimer value at `distance=9999.0` (its
      monomer-sum-proxy row):
    1. XG's `gamma_set` is a string of the form
       `f"{gamma1:4.2f}_{gamma2:4.2f}_{gamma3:4.2f}"`.
    2. Collect F12 mono1's data at `gamma=gamma1` (from the F12 dataframes
       already loaded in the notebook).
    3. Collect F12 mono2's data at `gamma=gamma2` (same as above).
    4. Sum those two, and subtract from the corresponding XG dimer value at
       `distance=9999.0`.
    5. Display the result as both a difference and a percentage difference.
    - [x] Made the monomer-sum-proxy a proper, reusable function:
          `IA.get_value_at_max_distance` (generalizes the old hardcoded
          `monomer_sum_distance=9999.0` in `get_inter_from_distance_proxy`
          into "extract the value at the row with the largest distance",
          working off index position rather than name/exact value).
    - [x] Added `IA.parse_gamma_set(gamma_set)` -> `(gamma1, gamma2)`,
          reusable anywhere an XG `gamma_set` string needs decoding.
