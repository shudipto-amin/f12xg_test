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

base_config="queryFiles/base.json"

make_tables() {
    local system=$1
    local system_type=$2
    local directory="${system}/${method}"
    local data_file="${directory}/data.csv"

    echo "$data_file"
    echo "${directory}"
    python make_tables_from_query.py \
        "$data_file" \
        "$base_config" \
        --system_type "$system_type" \
        --bases_family valence --add_bse \
        --write "${directory}/bse_data_valence.csv"

    python make_tables_from_query.py \
        "$data_file" \
        "$base_config" \
        --system_type "$system_type" \
        --bases_family core-valence --add_bse \
        --write "${directory}/bse_data_core_valence.csv"
}

make_tables "$mono1" "monomer$suffix"
make_tables "$mono2" "monomer$suffix"
make_tables "$dimer" "dimer$suffix"
