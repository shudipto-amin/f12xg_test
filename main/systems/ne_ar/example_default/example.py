import sys
import json 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import functions_for_analyze as ffa
import pandas as pd

fname = "./queryFile.json"
with open(fname, 'r') as f:
    QD = json.load(f)

data = pd.read_csv("./data.csv")
df = ffa.parse_outfiles_in_df(data, QD['query_dict'])

df = df.drop([
    'ansatzes',
    'core', 'core_names', 'full_file_prefix'
    ], axis=1
             )



print(df.to_string())
df.to_csv("example_data.csv", index=False)
