#/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}
help="
3 arguments required: <tensor-name> <outfile> <tensor_file>
  <tensor-name> ITF tensor name as declared. Eg: 'F1C\\[xJij\\]'
  <outfile> a molpro output file
  <tensor-file> the file to write tensor to
"

[ "$#" -eq 3 ] || die "$help" 

tensor=$1
outfile=$2
tensor_file=$3

awk "/Dump of tensor\: .*\:\:${tensor}/,/===========================================/" $outfile > $tensor_file
