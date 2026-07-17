# TODO

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
    - [ ] Tabulate
- [x] Run Tabulate for Ar
- [x] Do XG properly, but keep the proxy function as an alternative for any dataframe
- [x] Reorganize the folders - make an interactions folder for all the dimer and monomers.
    - [x] Consider either putting dimer/ ne/ ar/ inside an ne_ar/ folder, and likewise for others
- [ ] Add a section to `Plot_from_Interaction_Tables.ipynb` comparing the sum
      of F12 monomer values to XG's dimer value at `distance=9999.0` (its
      monomer-sum-proxy row):
    1. XG's `gamma_set` is a string of the form
       `f"{gamma1:4.2f}_{gamma2:4.2f}_{gamma3:4.2f}"`.
    2. Collect F12 mono1's data at `gamma=gamma1` (from the F12 dataframes
       already loaded in the notebook).
    3. Collect F12 mono2's data at `gamma=gamma2` (same as above).
    4. Sum those two, and subtract from the corresponding XG dimer value at
       `distance=9999.0`.
    5. Display the result as both a difference and a percentage difference.

