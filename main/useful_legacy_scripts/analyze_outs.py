import os
import sys
import argparse
import pandas
import xml.etree.ElementTree as ET
import gen_input as gi
import pandas as pd
import re
from functools import reduce


def get_files_matching(rexpr):

    matches = []
    regex = re.compile(rexpr)

    for root, dirs, files in os.walk(gi.outdir):
        for file in files:
            #print(file)
            fname = f'{gi.outdir}/{file}'
            if regex.match(fname):
                matches.append(fname)
    return matches

def inspect_children(elem):
    for child in elem:
        print(child.tag, child.attrib)

def pretty_print(elem, indent_lvl=0, criteria=None):
    pre = indent_lvl * "   "
    print(pre, "="*50)
    print(pre, f"=={elem.tag.upper()} DETAILS==")

    for key, val in elem.attrib.items():
        if criteria is not None and key not in criteria: continue
        print(pre, f"{key.upper():20s}: {val:20s}")

        
def get_properties(out, criteria1=None, match_func=all, criteria2=None, calculations=None):
    '''
    Get properties with `criterion1` in their name, `criterion2` in subname
    '''
    
   
    tree = ET.parse(out)
    root = tree.getroot()
    
    # clean namespaces
    for elem in tree.iter():
        elem.tag = elem.tag.split("}")[1]
        
    
    print('--')
    # There is some redundant nesting in our case, so just deal with 'job'
    assert len(root) == 1
    job = root[0]

    # Get to the elements with appropriate data
    for jobstep in job.findall('jobstep'):
        command = jobstep.get('command')
        if calculations is not None and command not in calculations: continue
        #print(command)
        
        #pretty_print(jobstep)
        for prop in jobstep.findall('property'):
            if criteria1 is not None:
                if not match_func(
                    prop.get(key) == val for key, val in criteria1
                ):
                    continue
            pretty_print(prop, 1, criteria=criteria2)     

def get_table(out, row, criteria1=None, match_func=all, criteria2=None, calculations=None):
    '''
    Get properties with `criterion1` in their name, `criterion2` in subname
    '''
    
   
    tree = ET.parse(out)
    root = tree.getroot()
    
    # clean namespaces
    for elem in tree.iter():
        elem.tag = elem.tag.split("}")[1]
        
    
    print('--')
    # There is some redundant nesting in our case, so just deal with 'job'
    assert len(root) == 1
    job = root[0]

    # Get to the elements with appropriate data
    data = {}
    for jobstep in job.findall('jobstep'):
        command = jobstep.get('command')
        if calculations is not None and command not in calculations: continue
        
        #print(command)
        row_index = row + [command]
        data[tuple(row_index)] = {}
        #pretty_print(jobstep)
        for prop in jobstep.findall('property'):
            if criteria1 is not None:
                if not match_func(
                    prop.get(key) == val for key, val in criteria1
                ):
                    continue
            

            val = float(prop.get('value'))
            data[tuple(row_index)][prop.get('name')] = val


            
            #pretty_print(prop, 1, criteria=criteria2)  
    return pd.DataFrame(data)

def get_outfile(ansatz, key):
        infile = gi.generate_fname(key, ansatz)
        job_name = infile.rstrip('inp')
        rexpr = f'{job_name}*.xml'
        #print(rexpr)
        matching_files = sorted(get_files_matching(rexpr))
        #print( matching_files)
        assert matching_files, f"{ansatz}, {key} combo returns no matches."
        return matching_files[-1] # get latest with -1
    
def get_output_files(ansatzes, template_keys):
    outfiles = []
    
    for ansatz in ansatzes:
        for key in template_keys:
            outfiles.append(get_outfile(ansatz, key))

    return outfiles

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    
    criteria_dict=[
                ('name', 'total energy'),
                ('name', 'correlation energy'),
    ]
    
    outfiles = get_output_files(gi.ansatzes, ('original', 'cpproute'))



    template_keys = ('original', 'cpproute', 'xg')
    list_df = []
    for ansatz in gi.ansatzes:
        for key in template_keys:
            
            out = get_outfile(ansatz, key)
            print(out)
            get_properties(
                out, 
                criteria1=criteria_dict,
                match_func=any,
                criteria2=['name', 'method', 'value'],
                calculations=['DF-MP2-F12'],
            )
            df = get_table(
                out, 
                row=[ansatz, key],
                criteria1=criteria_dict,
                match_func=any,
                criteria2=['name', 'method', 'value'],
                calculations=['DF-MP2-F12'],
            )

            list_df.append(df)

    df_merged = reduce(
        lambda  left,right: pd.merge(
            left,right, how='outer', left_index=True, right_index=True
        ), 
        list_df
    )
    float_format = '{:20.15f}'
    new_df = df_merged.transpose().droplevel(2, axis=0)
    print(new_df.to_string(
        formatters={
            'correlation energy': float_format.format,
            'total energy': float_format.format,
        }
    ))
  
