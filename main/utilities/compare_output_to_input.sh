#!/bin/bash

# --- Helper message ---
usage() {
    echo "Usage: $0 FILE1.out FILE2.inp"
    echo " Check if the given Molpro output corresponds to the given molpro input file"
    echo "  FILE1 must exist and end with .out"
    echo "  FILE2 must exist and end with .inp"
    exit 1
}

# --- Check argument count ---
if [[ $# -ne 2 ]]; then
    echo "Error: Exactly 2 arguments required."
    usage
fi

out_file="$1"
inp_file="$2"

# --- Check file extensions ---
if [[ ! "$out_file" =~ \.out$ ]]; then
    echo "Error: First argument must end with .out"
    usage
fi

if [[ ! "$inp_file" =~ \.inp$ ]]; then
    echo "Error: Second argument must end with .inp"
    usage
fi

# --- Check file existence ---
if [[ ! -f "$out_file" ]]; then
    echo "Error: File '$out_file' does not exist."
    usage
fi

if [[ ! -f "$inp_file" ]]; then
    echo "Error: File '$inp_file' does not exist."
    usage
fi

awk '/Variables initialized/{flag=1; next} /Commands initialized/{flag=0} flag' $out_file > __input.tmp

sed -i 's/^ //g' __input.tmp

diff __input.tmp $inp_file

