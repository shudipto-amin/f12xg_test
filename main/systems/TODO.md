# TODO

- [ ] Migrate `ne_ar/xg/` to the `base.json`/`system_type` pipeline (see
      README.md "Known gaps"). Its old query config used `core_names`
      filters and a `gamma_set` pivot index instead of `system_type`, so it
      needs its own mapping worked out before it fits the current scheme.
- [ ] Once `ne_ar/xg/` is migrated (above), extend
      `Plot_from_Interaction_Tables.ipynb` to cover XG the same way it now
      covers F12: work out XG's `outer_index` shape (its old `gamma_set`
      likely maps to another `gammas`-like scan, possibly combined with the
      F12 `gammas` axis) and reuse/extend `PFT.get_dfs`'s single-slice
      extraction (`gamma=...`) so the existing interaction-energy plotting
      cells work unmodified for XG too.
