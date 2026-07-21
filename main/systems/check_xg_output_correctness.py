"""
Verify XG `.out` files for correct atom-list gamma assignment
(`xg_maf_type: 1`, i.e. `xg.maf` with `type 1`/`len 1`/`info 0`). Checks
(also tracked as the HIGH PRIORITY item in TODO.md; the bug narrative is in
`DEBUG/atomic_gamma_assignment_error/README.md`, but this docstring is the
up-to-date source of truth for what's actually checked):

1. Contains `F12-XG CALCULATIONS BEGIN` and, on a separate line,
   `F12-XG CALCULATIONS END`.
2. `xg.maf` in the output folder is `type 1`/`len 1`/`info 0`, matching
   `xg_maf_type` in metadata.json.
3. Every `m_assignment_info` occurrence is followed by `0`.
4. Contains `DEBUG: case 1 for m_assignment_type`, and does NOT contain
   `DEBUG: case 0`/`DEBUG: case 2` for the same.
5. In the `ListGeminalAssignment()` section: atom index 0 -> `GammaGroups`
   all `1`; every other atom index -> `GammaGroups` all `2`.
6. Tensor differences (`Difference between F1<x>[...] and ...C[...]`):
   for monomers, expected to be exactly `0` regardless of gamma (in
   practice these currently always come out nonzero -- that's a known,
   separate issue, not something this check is meant to catch); for
   dimers where all three gammas are equal, expected to be below `--tol`.

Reuses `generate_inputs_and_folders.generate_file_paths` (to enumerate the
runs a metadata.json describes) and `check_outputs_and_folders.get_outfile`
(to find each run's latest `.out` file, same "latest by mtime" rule used
by the existing completion checker) rather than re-deriving either.

Output files can be large and there can be many of them, so each file is
scanned once, line by line, rather than read fully into memory and looped
over per check.
"""
import argparse
import os
import re
import sys
from argparse import Namespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from systems import generate_inputs_and_folders as giaf
from systems import check_outputs_and_folders as coaf

DIFF_PATTERN = re.compile(r"Difference between F1.1.*C\[")
ATOM_INDEX_RE = re.compile(r"^\s*\d+\s+atom index:\s*(\d+)")

parser = argparse.ArgumentParser(
    description="Verify XG output correctness against README 'Expected behaviour' rules"
)
parser.add_argument("metadata_path", nargs="+", help="Path(s) to xg metadata.json")
parser.add_argument(
    "--tol", type=float, default=1e-10,
    help="Tolerance for dimer same-gamma tensor differences (default: 1e-10)",
)
parser.add_argument("-v", "--verbose", action="store_true")


def scan_output_file(path):
    """
    Single streaming pass over an `.out` file, tracking each check's state
    with plain flags rather than re-scanning a list of lines per check.
    """
    xg_begin_found = False
    xg_end_found = False

    assignment_info_pending = False
    assignment_info_context = None
    assignment_info_failures = []

    debug_case1_found = False
    debug_bad_case_found = False

    in_gamma_section = False
    gamma_section_found = False
    gamma_pending_atom_index = None
    gamma_groups_failures = []

    diff_pending = False
    diff_context = None
    diff_matches = []

    with open(path, errors="replace") as f:
        for line in f:
            stripped = line.strip()

            if not xg_begin_found and "F12-XG CALCULATIONS BEGIN" in line:
                xg_begin_found = True
            if not xg_end_found and "F12-XG CALCULATIONS END" in line:
                xg_end_found = True

            # A pending flag resolves against *this* line (the one after the
            # trigger), then this line is checked for a new trigger.
            if assignment_info_pending and stripped:
                if stripped != "0":
                    assignment_info_failures.append(
                        {"context": assignment_info_context, "next": stripped}
                    )
                assignment_info_pending = False
            if "m_assignment_info" in line:
                assignment_info_pending = True
                assignment_info_context = stripped

            if "DEBUG: case 1 for m_assignment_type" in line:
                debug_case1_found = True
            elif (
                "DEBUG: case 0 for m_assignment_type" in line
                or "DEBUG: case 2 for m_assignment_type" in line
            ):
                debug_bad_case_found = True

            if "Running ListGeminalAssignment()" in line:
                in_gamma_section = True
                gamma_section_found = True
            elif in_gamma_section and stripped.startswith("===="):
                in_gamma_section = False
            elif in_gamma_section:
                m = ATOM_INDEX_RE.match(line)
                if m:
                    gamma_pending_atom_index = int(m.group(1))
                elif "GammaGroups:" in line and gamma_pending_atom_index is not None:
                    tokens = line.split("GammaGroups:")[1].split()
                    expected = "1" if gamma_pending_atom_index == 0 else "2"
                    if any(t != expected for t in tokens):
                        gamma_groups_failures.append(
                            {"atom_index": gamma_pending_atom_index, "line": stripped}
                        )
                    gamma_pending_atom_index = None

            if diff_pending and stripped:
                try:
                    val = float(stripped)
                except ValueError:
                    val = None
                diff_matches.append((diff_context, val))
                diff_pending = False
            if DIFF_PATTERN.search(line):
                diff_pending = True
                diff_context = stripped

    # Anything still "pending" at EOF means the expected follow-up line
    # never showed up (truncated/incomplete output) -- record as such.
    if assignment_info_pending:
        assignment_info_failures.append({"context": assignment_info_context, "next": None})
    if diff_pending:
        diff_matches.append((diff_context, None))
    if gamma_pending_atom_index is not None:
        gamma_groups_failures.append({"atom_index": gamma_pending_atom_index, "line": None})

    return {
        "xg_begin_found": xg_begin_found,
        "xg_end_found": xg_end_found,
        "assignment_info_failures": assignment_info_failures,
        "debug_case1_found": debug_case1_found,
        "debug_bad_case_found": debug_bad_case_found,
        "gamma_section_found": gamma_section_found,
        "gamma_groups_failures": gamma_groups_failures,
        "diff_matches": diff_matches,
    }


def check_maf_file(folder_path, maf_filename, expected_type):
    maf_path = os.path.join(folder_path, maf_filename)
    if not os.path.exists(maf_path):
        return False, {"error": f"missing {maf_path}"}
    content = open(maf_path).read()
    m_type = re.search(r"type\s+(\d+)", content)
    m_len = re.search(r"len\s+(\d+)", content)
    m_info = re.search(r"info\s+(\S+)", content)
    type_val = int(m_type.group(1)) if m_type else None
    len_val = int(m_len.group(1)) if m_len else None
    info_val = m_info.group(1) if m_info else None
    ok = (type_val == 1 and len_val == 1 and info_val == "0")
    if expected_type is not None:
        ok = ok and (type_val == expected_type)
    return ok, {"type": type_val, "len": len_val, "info": info_val, "expected_type": expected_type}


def build_checks(scan, folder_path, maf_filename, expected_maf_type, is_dimer, gammas_equal, tol):
    checks = {
        "begin_end": (
            scan["xg_begin_found"] and scan["xg_end_found"],
            {"begin": scan["xg_begin_found"], "end": scan["xg_end_found"]},
        ),
        "maf": check_maf_file(folder_path, maf_filename, expected_maf_type),
        "assignment_info": (
            len(scan["assignment_info_failures"]) == 0,
            scan["assignment_info_failures"],
        ),
        "debug_case": (
            scan["debug_case1_found"] and not scan["debug_bad_case_found"],
            {"has_case1": scan["debug_case1_found"], "has_bad_case": scan["debug_bad_case_found"]},
        ),
    }

    if not scan["gamma_section_found"]:
        checks["gamma_groups"] = (False, [{"error": "no ListGeminalAssignment() section found"}])
    else:
        checks["gamma_groups"] = (len(scan["gamma_groups_failures"]) == 0, scan["gamma_groups_failures"])

    diff_matches = scan["diff_matches"]
    if not diff_matches:
        checks["tensor_diff"] = (None, [])  # nothing to check
    elif is_dimer:
        if not gammas_equal:
            checks["tensor_diff"] = (None, diff_matches)  # rule doesn't apply
        else:
            ok = all(v is not None and abs(v) < tol for _, v in diff_matches)
            checks["tensor_diff"] = (ok, diff_matches)
    else:
        ok = all(v is not None and v == 0.0 for _, v in diff_matches)
        checks["tensor_diff"] = (ok, diff_matches)

    return checks


def run_checks_for_metadata(metadata_path, tol, verbose):
    meta = giaf.read_metadata(metadata_path)
    args_ns = Namespace(metadata_path=metadata_path, dry_run=False, output=None)
    is_dimer = "distances" in meta
    expected_maf_type = meta.get("xg_maf_type")

    n_total = 0
    n_no_output = 0
    results_by_check = {}
    failures_detail = []

    def record(check_name, ok):
        d = results_by_check.setdefault(check_name, {"pass": 0, "fail": 0, "na": 0})
        d["na" if ok is None else ("pass" if ok else "fail")] += 1

    for infiles, folder_path, _, kwargs in giaf.generate_file_paths(args_ns, meta):
        infile = next((f for f in infiles if f.endswith(".inp")), infiles[0])
        n_total += 1
        outfile = coaf.get_outfile(
            infile, calctype=meta["calc_type"], outformat=None,
            return_all_matches=False, verbose=verbose,
        )
        if outfile is None:
            n_no_output += 1
            continue

        gammas_equal = False
        if "gamma_set" in kwargs:
            g1, g2, g3 = (float(g) for g in kwargs["gamma_set"].split("_"))
            gammas_equal = g1 == g2 == g3

        scan = scan_output_file(outfile)
        checks = build_checks(
            scan, folder_path, meta["xg_maffilename"], expected_maf_type,
            is_dimer, gammas_equal, tol,
        )

        run_had_failure = False
        for name, (ok, _detail) in checks.items():
            record(name, ok)
            if ok is False:
                run_had_failure = True

        if run_had_failure or verbose:
            failures_detail.append((outfile, kwargs, checks))

    return {
        "metadata_path": metadata_path,
        "is_dimer": is_dimer,
        "n_total": n_total,
        "n_no_output": n_no_output,
        "results_by_check": results_by_check,
        "failures_detail": failures_detail,
    }


def print_summary(summary, verbose):
    print("=" * 78)
    print(summary["metadata_path"], "(dimer)" if summary["is_dimer"] else "(monomer)")
    print("=" * 78)
    print(f"  Runs found: {summary['n_total']}   No output file: {summary['n_no_output']}")
    for name, d in summary["results_by_check"].items():
        print(f"  {name:18s} pass={d['pass']:4d}  fail={d['fail']:4d}  n/a={d['na']:4d}")

    if summary["failures_detail"]:
        print("  --- runs with a failing check ---")
        for outfile, kwargs, checks in summary["failures_detail"]:
            failed_names = [n for n, (ok, _) in checks.items() if ok is False]
            if not failed_names:
                continue
            print(f"    {outfile}")
            print(f"      failed: {', '.join(failed_names)}")
            if verbose:
                for name in failed_names:
                    print(f"      {name}: {checks[name][1]}")


def main():
    args = parser.parse_args()
    for metadata_path in args.metadata_path:
        summary = run_checks_for_metadata(metadata_path, args.tol, args.verbose)
        print_summary(summary, args.verbose)


if __name__ == "__main__":
    main()
