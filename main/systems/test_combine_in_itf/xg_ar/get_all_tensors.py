import subprocess
import argparse

tensors = 'Ff1 Ff2 Ff3 FC00 FC01 FC11 FC F1C FFC FFbarC F1F2bar'.split()
#tensors = 'FFC FFbarC F1F2bar'.split()

tensors_with_inds = [f"{tens}[MNPQ]" for tens in tensors]
#tensors_with_inds.extend('Mix00[MN] Mix01[MN] Mix11[MN]'.split())
for tens in tensors_with_inds:
    cmd = f'python ../../write_tensor.py metadata.json {tens}'
    print(cmd)
    subprocess.run(f"{cmd}", shell=True)
