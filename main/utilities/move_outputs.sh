#!/bin/bash
# --- Helper message ---
usage() {
    echo "Usage: $0 <destination>"
    echo "Move all output files to <destination> folder"
    exit 1
}

# --- Check argument count ---
if [[ $# -ne 1 ]]; then
    echo "Error: Exactly 1 argument required."
    usage
fi
 

mv j-*.o* $1/
mv *.out $1/
mv *.xml $1/
mv *.log $1/
