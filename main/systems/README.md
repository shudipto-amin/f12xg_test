# `data.csv` → `bse_data*.csv` pipeline

This describes how a directory of Molpro output files becomes a pivoted
energy table, e.g. `ar/dfmp2/data.csv` → `ar/dfmp2/bse_data_valence.csv`.

## Overview

```
<system>/<method>/data.csv                     one row per Molpro run
        |                                      (bases, core, distances, outfile, ...)
        v
make_tables_from_query.py                      parses each .out file, filters,
  + queryFiles/base.json                        relabels, pivots into a wide table
  + queryFiles/query_dict.json
        v
<system>/<method>/bse_data_<bases_family>.csv   pivoted table + metadata header
```

## The pieces

### `data.csv`
One row per Molpro calculation belonging to that `<system>/<method>` directory
(e.g. `ar/dfmp2/data.csv`). Columns include `bases`, `core`, `distances`,
`full_file_prefix`, `outfile` (path to the `.out` file). Produced upstream by
`generate_inputs_and_folders.py` / `run_inputs_and_folders.py` /
`check_outputs_and_folders.py`, driven by that directory's `metadata.json`.
Not covered by this README.

### `queryFiles/query_dict.json`
What to extract from each `.out` file: for each search string (e.g.
`"correlation energy"`), which column to store it under (`col_name`) and
which occurrence to take if it appears more than once in the file
(`match_num`, `-1` = last). Shared by every system/method — there is only
one copy of this file.

### `queryFiles/base.json`
Everything else needed to build a table, parameterized so one file covers
every system/method combination:

```json
{
    "query_dict_file": "query_dict.json",
    "replace": {
        "core": {"": "frozen", "core,0": "all electron"}
    },
    "bases_families": {
        "valence":      ["aug-cc-pVDZ", "aug-cc-pVTZ", "aug-cc-pVQZ", "aug-cc-pV5Z"],
        "core-valence": ["aug-cc-pwCVDZ", "aug-cc-pwCVTZ", "aug-cc-pwCVQZ", "aug-cc-pwCV5Z"]
    },
    "system_type": {
        "monomer":      ["core"],
        "dimer":        ["core", "distances"],
        "monomer_f12":  ["core", "gammas"],
        "dimer_f12":    ["core", "gammas", "distances"]
    },
    "pivot_columns": ["basis_sizes"],
    "pivot_values": ["Correlation Energy", "Reference Energy"]
}
```

- **`bases_families`** — named basis-set lists. `valence` = plain
  `aug-cc-pVXZ`, `core-valence` = core-valence `aug-cc-pwCVXZ` (needed for
  core-correlated / all-electron calculations).
- **`system_type`** — named pivot-table row shapes. Pick based on what the
  directory actually contains:
  - `monomer` — a single atom/species, no `distances` (e.g. `ar/`, `ne/`)
  - `dimer` — a two-body system scanned over `distances` (e.g. `ne_ar/`)
  - `..._f12` variants — same, but the method also scans an F12 `gammas`
    parameter (methods like `default`/`xg`, as opposed to `dfmp2`)
- **`replace`** — value relabeling applied after parsing (e.g. Molpro's
  `core` column values become human-readable `frozen`/`all electron`).
- **`pivot_columns`/`pivot_values`** — fixed: basis size becomes the column
  axis, correlation/reference energy become the value columns.

### `make_tables_from_query.py`
```
python make_tables_from_query.py <data.csv> <base.json> \
    --system_type {monomer,dimer,monomer_f12,dimer_f12} \
    --bases_family {valence,core-valence} \
    [--add_bse] [--write <out.csv>] [--debug]
```
1. Loads `data.csv`, resolves `outfile` paths relative to it, derives a
   `basis_sizes` column from each basis set name.
2. Loads `base.json`; errors out if it's missing `system_type` or
   `bases_families`, or if the requested `--system_type`/`--bases_family`
   value isn't one of its keys.
3. Composes the query config from `base.json` + the two flags (basis list,
   pivot index shape, replace rules, and `query_dict` via
   `query_dict_file`).
4. Parses every referenced `.out` file for the queried values
   (`single_output_parser.OutputParser`), filters to the requested basis
   family, applies `replace`, and pivots into a wide table
   (`system_type`-shaped rows × basis-size columns).
5. `--add_bse` appends a CBS-extrapolated `BSE` column/basis-size.
6. Writes the result with `--write` as a "metacsv" (a small metadata header
   — `Raw_Datafile`, `bases` — followed by the CSV table), or prints it if
   `--write` is omitted.

### `Make_Tables_prepare_bse_data.sh`
Convenience wrapper that runs the above twice (once per `bases_family`) for
each of a monomer/monomer/dimer trio:
```
./Make_Tables_prepare_bse_data.sh <mono1_dir> <mono2_dir> <dimer_dir> <method_dir> [suffix]
```
`suffix` is `""` for plain `system_type`s (`monomer`/`dimer`) or `_f12` for
the F12 variants (`monomer_f12`/`dimer_f12`). Example:
```
./Make_Tables_prepare_bse_data.sh ne ar ne_ar dfmp2 ""
./Make_Tables_prepare_bse_data.sh ne ar ne_ar default "_f12"
```
Writes `<dir>/<method>/bse_data_valence.csv` and
`<dir>/<method>/bse_data_core_valence.csv` for each of the three
directories.

## Output

`<system>/<method>/bse_data_valence.csv` / `bse_data_core_valence.csv` — a
metacsv file: a short metadata header (source `data.csv` path, basis list
used) followed by the pivoted table, indexed by `system_type` (e.g.
`core`/`distances`), columned by basis size, with `Correlation Energy` /
`Reference Energy` (and `BSE` if requested) as value groups.

## Regression baseline

`Test_Suite/<system>/<method>/bse_data_valence.csv` /
`bse_data_core_valence.csv` hold known-good snapshots to diff against after
changing the pipeline — regenerate into a scratch location and `diff`
before overwriting real output.

## Known gaps

- `ne_ar/xg/` is not yet migrated to this pipeline: its old query config
  used a different filter/pivot scheme (`core_names`/`gamma_set` instead of
  `system_type`) that doesn't map onto `base.json` yet.
