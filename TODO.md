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
- [ ] Run Tabulate for Ar
