import datetime
import os
import pandas as pd
import matplotlib 
import matplotlib.pyplot as pp
import numpy as np
import sys
from matplotlib.backends.backend_pdf import PdfPages
dailies = os.path.join(
    os.path.dirname(__file__), '../../dailies/'
)

def save_fig_as_pdf(fig, fname, note):
    with PdfPages(fname) as pdf:
        pdf.attach_note(
            note,
            [-1,-1,0,0]
        )
    
        pdf.savefig(fig)

def gen_fname(fname=None, folder=None, ext=None):
    
    now = datetime.datetime.now()
    if folder is None:
        folder = now.strftime("%Y_%m_%d")
    folder = os.path.join(dailies, folder)
    
    if not os.path.exists(folder):
        print(f"Creating {folder}")
        os.mkdir(folder)
    if fname is None:
        fname = now.strftime("%H%M%S")

    if ext is not None and not fname.endswith(ext):
        fname = f"{fname}.{ext}"
        
    fname = os.path.join(folder, fname)
    

    if os.path.exists(fname):
        print(f"{fname} already exists")
        fsplit = fname.split('.')
        
        for d in range(0,10):
            fname = '.'.join(fsplit[:-1] + [f"{d}"] + fsplit[-1:])
            if not os.path.exists(fname):
                break

    if os.path.exists(fname):
        raise FileExistsError(f"{fname} exists, max file name iteration reached")

    return os.path.realpath(fname)
    
def dump_daily(obj, *args, fname=None, folder=None, save_func=None, **kwargs):
    '''
    Create folder and save fname, or generate fname if not provided.
    if obj is fig type, pdf is saved
    if obj is pd.DataFrame, then csv is saved
    '''
    #return fname
    
    if save_func is not None:
        fname = gen_fname(fname=fname, folder=folder)
        save_func(obj, fname, *args, **kwargs)
        
    if isinstance(obj, matplotlib.figure.Figure):
        fname = gen_fname(fname=fname, folder=folder, ext='pdf')
        save_fig_as_pdf(obj, fname, *args, **kwargs) 

    if isinstance(obj, pd.DataFrame):
        fname = gen_fname(fname=fname, folder=folder, ext='csv')
        obj.to_csv(fname, *args, **kwargs)

    if isinstance(obj, str):
        fname = gen_fname(fname=fname, folder=folder)
        with open(fname, 'w') as f:
            f.write(obj)
    print(f"saved {fname}")