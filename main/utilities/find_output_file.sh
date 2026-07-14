#!/bin/bash
file_to_compare=$1
folder_to_search=$2
for f in ${folder_to_search}/*.out; 
    do cmp -s "$f" $file_to_compare && echo "Files $f is identical to $file_to_compare"; done

