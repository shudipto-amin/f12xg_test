#/bin/bash
# !!! Destructive !!! use with caution
outfile=$1
outfile2="${outfile}.dumpless"

pattern1='^ Dump of tensor';
pattern2='===========================================';

if ! grep -q "Block" "$outfile"; then
    echo "Tensor Dump Blocks not found"
    exit 0
fi

echo "==========================================="
echo "Truncating Dumps from $outfile"
echo "/${pattern1}/,/${pattern2}/{/${pattern1}/!{/${pattern2}/!d}}" #$outfile > $outfile2 #&& rm $outfile
sed "/${pattern1}/,/${pattern2}/{/${pattern1}/!{/${pattern2}/!d}}" $outfile > $outfile2 && mv $outfile2 $outfile
