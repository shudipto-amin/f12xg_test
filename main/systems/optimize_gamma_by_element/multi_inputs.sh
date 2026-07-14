#!/bin/bash

bases=("cc-pvtz" "aug-cc-pvtz" "awcvtz")
#atoms=("he" "kr")
atoms=(
  h he li be b c n o f ne
  na mg al si p s cl ar k ca
  sc ti v cr mn fe co ni cu zn
  ga ge as se br
)

for atom in "${atoms[@]}"; do
    for basis in "${bases[@]}"; do
        inpfile="outputs/${atom}_${basis}.inp"
        if [[ -f "$inpfile" ]]; then
            echo "Warning: $inpfile already exists, skipping..."
        else
            python gen_input.py -a "$atom" -b "$basis" -g 0.5 3 0.1 > "$inpfile"
        fi
    done
done

