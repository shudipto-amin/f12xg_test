#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
    echo "Usage: $0 mono1 mono2 dimer method [suffix]"
    exit 1
fi

mono1=$1
mono2=$2
dimer=$3
method=$4
suffix=$5

make_tables() {
    local system=$1
    local suffix=$2
    local directory="${system}/${method}"
    local data_file="${directory}/data.csv"

    echo "$data_file"
    echo "${directory}"
    python make_tables_from_query.py \
        "$data_file" \
        "${directory}/queryFile${suffix}.json" --add_bse \
        --write "${directory}/bse_data.csv"

    python make_tables_from_query.py \
        "$data_file" \
        "${directory}/queryFile_wC${suffix}.json" --add_bse\
        --write "${directory}/bse_data_wC.csv"
}

make_tables "$mono1" "_monomer$suffix"
make_tables "$mono2" "_monomer$suffix"
make_tables "$dimer" "$suffix"
