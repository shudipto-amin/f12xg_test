#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
    echo "Usage: $0 mono1 mono2 dimer method [suffix]"
    echo "    mono1 : dir"
    echo "    mono2 : dir"
    echo "    dimer : dir"
    echo "    method : subdir in all of above"
    echo "    suffix : suffix to json file, example '_f12'"

    exit 1
fi

mono1=$1
mono2=$2
dimer=$3
method=$4
suffix=$5

link_queries() {
    local system=$1
    local suffix=$2

    cd "$system/$method"

    for qd in \
        "queryFile_wC${suffix}.json" \
        "queryFile${suffix}.json"
    do
        ln -sf "../../queryFiles/${qd}" .
    done

    cd - >/dev/null
}

link_queries "$mono1" "_monomer$suffix"
link_queries "$mono2" "_monomer$suffix"
link_queries "$dimer" "$suffix"
