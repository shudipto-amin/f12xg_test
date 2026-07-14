# Functions for use in tabulate_outs.py
# All function must take 1 argument (molpro output file) and return a dictionary
# 
"""
This is a test for `tabulate_outs.py`

Each function defined must be of the format:

```
def <func_name> (outfile: str):
    parse output file...
    return value: float 
    
```
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import argparse
import tabulate_outputs_and_folders as to
import json


class OutputParser():
    """
    A parser object containing functions that can be
    applied to output files to return certain values.

    The purpose of this class is to generate one function
    that can be used to make multiple queries on a single 
    output file in one reading loop. 

    Attributes:
        QD (dict) : The queries dictionary passed to this class
            with modifications made by initialization.
    """
    def __init__(self, QueriesDict: dict[str,dict]):
        """
        QueriesDict - object of queries and rules:
            { <query> : <conditions> ... }
            where <conditions> is another dict:
                { <cond_type> : <val> ... }
        
        There must be at least one pair of <query> <conditions>
        The <conditions dict must have the 'col_name' key.
        
        Example:
        QueriesDict = {
            'MP2-F12 correlation energy' : {
                'col_name' : 'Cor_ener'
                },
            ' Reference energy ' : {
                'match_num' : -1,
                'col_name' : 'Ref_ener', 
                },
            ' total energy ' : {
                'match_num' : -1,
                'col_name' : 'Tot_ener'
                }
        }
       
        Possible keys for <conditions> dict:
        
        col_ind (int) : the index of words separated by space AFTER query is 
            removed from line (default -1)
        
        match_num (int) : in case of multiple matches to query, will use the 
            zero-indexed match number. (default 1, first value). A negative 
            value may be used to represent the last match.
            
        """
        self.QD = QueriesDict
        self._complete_queries_dict()

    def _complete_queries_dict(self):
        
        defaults = {
                'match_num' : 1,
                'col_ind' : -1,
        }
        private_keys = {
                '_read' : True,
                '_match_count' : 0,
                '_query_line' : '',
                '_line_num' : -1
                }

        for query, conditions in self.QD.items():
            for key, val in defaults.items():
                if key not in conditions:
                    conditions[key] = val
            for key, val in private_keys.items():
                conditions[key] = val
            self.QD[query] = conditions
        

    def _get_float_(self, line, query, col_ind):
        after_query =line.split(query)[-1]
        value = after_query.split()[col_ind]

        value = float(value.strip())
        return value

    def GetAll(self, outfile):
        float_dict =dict()
        with open(outfile, 'r') as f:
            for n, line in enumerate(f):
                for query, conditions in self.QD.items():
                    if not conditions['_read']: continue
                    if query  not in line: continue
                    if conditions['_match_count'] == conditions['match_num']:
                        conditions['_read'] = False
                    conditions['_query_line'] = line
                    conditions['_line_num'] = n
        for query, conditions in self.QD.items():
            line = conditions['_query_line']
            n = conditions['_line_num']
            try:
                value = self._get_float_(line, query, conditions['col_ind'])
            except Exception as E:
                print(E)
                print(f"Outfile: {outfile}")
                print(f"Line num: {n} : {line}")
                raise E
            float_dict[conditions['col_name']] = value
        
        return float_dict            



QueriesDict = {
    'MP2-F12 correlation energy' : {
        'col_name' : 'Cor_ener'
        },
    'SCS-MP2 correlation energy:' : {
        'col_name' : 'SCS_MP2',
        'col_ind' : 0
        },
    ' Reference energy ' : {
        'match_num' : -1,
        'col_name' : 'Ref_ener', 
        },
    ' total energy ' : {
        'match_num' : -1,
        'col_name' : 'Tot_ener'
        }
}

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Test for applying function to a single output"
    )

    parser.add_argument(                                  
        "output_path",                  
        help="Path to a Molpro output file." )                                                     

    parser.add_argument(
        "-q", "--queryFile",
        help="Path to a json file with queries (default is to read from within this script)",
        default=None
    )

    args = parser.parse_args()
    ener_parser = OutputParser(QueriesDict)

    outparsers = dict(
        outfile = lambda outfile: outfile,
        energies = ener_parser.GetAll
    )

    out = dict()
    for key, func in outparsers.items():
        out[key] = func(args.output_path)

    print(json.dumps(out, indent=4))

