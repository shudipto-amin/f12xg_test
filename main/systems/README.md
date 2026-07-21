# `data.csv` → `bse_data*.csv` → `dimer_and_monomer*.csv` pipeline

This describes how a directory of Molpro output files becomes a pivoted
energy table (Stage 1), and how a dimer + its two monomers' tables get
combined into an interaction-energy table (Stage 2), e.g.
`ar/dfmp2/data.csv` → `ar/dfmp2/bse_data_valence.csv` → (combined with
`ne/dfmp2/bse_data_valence.csv`) → `ne_ar/dfmp2/dimer_and_monomer_valence_frozen.csv`.

## Overview

```
Stage 1 (per system/method directory)

<system>/<method>/data.csv                     one row per Molpro run
        |                                      (bases, core, distances, outfile, ...)
        v
make_tables_from_query.py                      parses each .out file, filters,
  + queryFiles/base.json                        relabels, pivots into a wide table
  + queryFiles/query_dict.json
        v
<system>/<method>/bse_data_<bases_family>.csv   pivoted table + metadata header


Stage 2 (dimer + its two monomers, same method/bases_family)

<mono1>/<method>/bse_data_<bases_family>.csv  \
<mono2>/<method>/bse_data_<bases_family>.csv   |
<dimer>/<method>/bse_data_<bases_family>.csv  /
        |
        v
_Interaction_Analysis.py                      combines the three tables, adds
  + queryFiles/base.json                       CBS/HF+CorrE(CBS) and interaction-
                                                energy columns
        v
<dimer>/<method>/dimer_and_monomer_<bases_family>_<core>.csv
```

## The pieces

### `data.csv`
One row per Molpro calculation belonging to that `<system>/<method>` directory
(e.g. `ar/dfmp2/data.csv`). Columns include `bases`, `core`, `distances`,
`full_file_prefix`, `outfile` (path to the `.out` file). Produced upstream by
`generate_inputs_and_folders.py` / `run_inputs_and_folders.py` /
`check_outputs_and_folders.py`, driven by that directory's `metadata.json`.
Not covered by this README. Correctness of the `.out` files themselves
(as opposed to whether the run completed) is checked separately by
`check_xg_output_correctness.py` — see that script's docstring.

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
    "methods": {
        "dfmp2": "",
        "f12": "_f12"
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
    parameter (method `f12`, as opposed to `dfmp2`)
  - `..._xg` variants — same idea, but the method scans a `gamma_set`
    parameter instead (method `xg`)
- **`methods`** — maps a `method_dir` name (e.g. `dfmp2`, `f12`) to the
  suffix appended to `"monomer"`/`"dimer"` to get its `system_type` key
  (`""` for plain, `"_f12"` for the F12/`gammas` shape). Used by
  `_Interaction_Analysis.py` to infer `header`/`index_col` for a given
  method without a separate flag.
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
./Make_Tables_prepare_bse_data.sh ne ar ne_ar f12 "_f12"
```
Writes `<dir>/<method>/bse_data_valence.csv` and
`<dir>/<method>/bse_data_core_valence.csv` for each of the three
directories.

### `_Interaction_Analysis.py`
Stage 2: combines a dimer's `bse_data*.csv` with its two monomers'
`bse_data*.csv` into interaction-energy tables. Replaces the hand-copied
per-system-pair cells that used to live in `Make_Tables.ipynb`.
```
python _Interaction_Analysis.py <mono1_dir> <mono2_dir> <dimer_dir> <method_dir> \
    --bases_family {valence,core-valence} \
    [--mono1_name NAME] [--mono2_name NAME] \
    [--base_json queryFiles/base.json] [--debug]
```
1. Loads `base.json`; errors out if it's missing `system_type`, `methods`,
   or `bases_families`.
2. `method_dir` is looked up in `base['methods']` to get a suffix (`""` or
   `"_f12"`); that suffix picks the `monomer`/`monomer_f12` and
   `dimer`/`dimer_f12` `system_type` shapes, which in turn determine the
   `header`/`index_col` used to read each `bse_data*.csv` — no separate F12
   flag needed.
3. `--bases_family` infers both the input `basename` (`bse_data_<family>.csv`,
   hyphens in the family name become underscores) and the output
   `outbasename` (`dimer_and_monomer_<family>`).
4. `--mono1_name`/`--mono2_name` default to the title-cased directory name
   (e.g. `mono1_dir='ne'` → `'Ne'`) if not given.
5. Reads the three `bse_data*.csv` files
   (`_Interaction_Analysis.prepare_and_combine_dataframes_from_files`),
   combines them per `core` value (adding `Sum`/`Difference` rows and a
   CBS-extrapolated `HF + CorrE(CBS)` column), and writes one output file
   per `core`
   (`_Interaction_Analysis.write_combined` → `<dimer_dir>/<method_dir>/<outbasename>_<core>.csv`).

## Output

- **Stage 1** — `<system>/<method>/bse_data_valence.csv` /
  `bse_data_core_valence.csv`: a metacsv file (short metadata header —
  source `data.csv` path, basis list used — followed by the pivoted table),
  indexed by `system_type` (e.g. `core`/`distances`), columned by basis
  size, with `Correlation Energy` / `Reference Energy` (and `BSE` if
  requested) as value groups.
- **Stage 2** — `<dimer_dir>/<method_dir>/dimer_and_monomer_valence_<core>.csv`
  / `dimer_and_monomer_core_valence_<core>.csv` (one file per `core` value,
  e.g. `frozen`/`all electron`): a metacsv file indexed by
  `Dimer distances`/`Monomers`/`Difference` rows, columned by
  `Correlation Energy`/`Reference Energy`/`HF + CorrE(CBS)` × basis size.

## Regression baseline

`Test_Suite/<system>/<method>/` holds known-good snapshots to diff against
after changing the pipeline — regenerate into a scratch location and `diff`
before overwriting real output:
- `bse_data_valence.csv` / `bse_data_core_valence.csv` (Stage 1)
- `dimer_and_monomer_valence_<core>.csv` / `dimer_and_monomer_core_valence_<core>.csv`
  (Stage 2, currently only populated for `ne_ar/dfmp2`)

## Known gaps

- `analyze.ipynb` still references the pre-rename `default/` method
  directory name and the old `bse_data.csv`/`bse_data_wC.csv` filenames —
  left untouched since it's a deprecated notebook, not part of this
  pipeline.
