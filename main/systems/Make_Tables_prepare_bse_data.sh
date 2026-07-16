#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
    echo "Usage: $0 mono1 mono2 dimer method [suffix] [bases_families]"
    echo "  bases_families: space-separated list of queryFiles/base.json"
    echo "                  'bases_families' keys (e.g. \"valence\" or"
    echo "                  \"valence core-valence\"). Defaults to all keys"
    echo "                  present in base.json."
    exit 1
fi

mono1=$1
mono2=$2
dimer=$3
method=$4
suffix=$5

base_config="queryFiles/base.json"

if [[ -n "${6:-}" ]]; then
    bases_families=$6
else
    bases_families=$(python3 -c "
import json, sys
base = json.load(open(sys.argv[1]))
print(' '.join(base['bases_families']))
" "$base_config")
fi

make_tables() {
    local system=$1
    local system_type=$2
    local directory="${system}/${method}"
    local data_file="${directory}/data.csv"

    echo "$data_file"
    echo "${directory}"

    for bases_family in $bases_families; do
        local stem=${bases_family//-/_}
        python make_tables_from_query.py \
            "$data_file" \
            "$base_config" \
            --system_type "$system_type" \
            --bases_family "$bases_family" --add_bse \
            --write "${directory}/bse_data_${stem}.csv"
    done
}

make_tables "$mono1" "monomer$suffix"
make_tables "$mono2" "monomer$suffix"
make_tables "$dimer" "dimer$suffix"
