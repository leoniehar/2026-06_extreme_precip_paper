import os
import xarray as xr 
import pandas as pd

######################################################
# open slopes as dataset #
######################################################
def read_slopes_csv_as_ds(csv_info):
    '''
    Input: CSV info = dir with paths to slope csv per experiment
    Output: loaded csv 
    '''
    dfs = []
    for variant_label, path in csv_info.items():
        df = pd.read_csv(path)
        df['variant'] = variant_label
        dfs.append(df)
    
    # --- concat & convert to xarray ---
    df_all = pd.concat(dfs, ignore_index=True)
    ds = df_all.set_index(['variant', 'variable']).to_xarray()
    
    return ds



    

