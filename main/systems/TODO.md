# TODO

- [ ] Migrate `ne_ar/xg/` to the `base.json`/`system_type` pipeline (see
      README.md "Known gaps"). Its old query config used `core_names`
      filters and a `gamma_set` pivot index instead of `system_type`, so it
      needs its own mapping worked out before it fits the current scheme.
- [ ] Commit currently staged changes (`README.md`, etc.) once ready.
- [ ] Resolve `ne_ar/example_default/example.py` and
      `ne_ar/example_default/single_output_parser.py`: tracked in git but
      missing from disk (unrelated to the pipeline refactor) — decide
      whether to restore or remove from tracking.
