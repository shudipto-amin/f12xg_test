import re
import numpy as np
import os, sys, glob
import subprocess
import json

def get_coefficients_from_output(output_fname):
    #with open(output_fname, 'r') as out:
    search_str1 = " Geminal optimization for beta="
    search_str2 = "F12 Coeffs"
    num_lines = 7
    
    command = f"awk '/{search_str1}/,/{search_str2}/' {output_fname}"
    capture = subprocess.check_output(command, shell=True)
    results = capture.decode('utf-8').split(search_str1)

    # filter results
    filtered_results = []
    for res in results:
        if "NO CONVERGENCE IN GEMINAL FIT" in res:
            continue
        if res:
            lines = []
            for line in res.split('\n'):
                if line:
                    lines.append(line)
            filtered_results.append(lines)
    return filtered_results

def results_to_dict(results):

    data = dict()
    for res in results:

        for n, row in enumerate(res):
            if n == 0:
                beta = f"{float(row):4.2f}"
                continue
            if 'Weight function' in row:
                m = float(re.split('m=|,', row)[1])
                omega = float(re.split('omega= ', row)[1])
                continue
            if 'F12 Alphas' in row:
                string_alphas = row.split()[2:]
                alphas = [float(a) for a in string_alphas]
                continue
            if 'F12 Coeffs' in row:
                string_coeffs = row.split()[2:]
                coeffs = [float(a) for a in string_coeffs]
                continue

        data[beta] = dict(
                m = m,
                omega = omega,
                alphas = alphas,
                coeffs = coeffs,
            )
    return data
    #return coefficients

results = get_coefficients_from_output('betas_for_He.out')
data = results_to_dict(results)

with open('gamma_to_gauss.dat','w') as f:
    json.dump(data, f)
