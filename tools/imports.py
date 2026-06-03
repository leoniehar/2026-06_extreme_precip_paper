import os
import xarray as xr 
import pandas as pd

################################################
###### open subset of months for one year ######
################################################

def open_months(year, months, path_to_folder, vars_keep):
    '''
    input: 
        months = ["12","01","02"] 
        year = "2020" # from runner
        path_to_folder = data dir of monthly data
    Dependencies 
        import_defs file => monthly data name pattern 
            (file_pattern = file pattern that has month YYYY-MM input)
    Output: 
        opened monthly datasets for selected month of selected year 
    '''
    import sys
    sys.path.append("../configs")
    from import_defs import monthly_data_name_pattern
    datasets = []
    
    for sel_month in months: 
        month = f"{year}-{sel_month}" # 
        file_pattern_m= monthly_data_name_pattern(month) # 
        
        # Create the full file path pattern
        file = os.path.join(path_to_folder, file_pattern_m)
        # import first fil
        data = xr.open_dataset(file, engine = "h5netcdf")[vars_keep]
        datasets.append(data)
    datasets = xr.concat(datasets,dim = "time") 
    
    return datasets
######################################################
# open all datasets for multiple years #
######################################################
def open_seasonal_data(year, path_to_folder, vars_keep):
    '''
    input: 
        year = year for which data should be opened
        path_to_folder = path where monthly data is located (from 11_xx) 
        vars_keep = variables from monthly data that should be loaded
    Output: ds[<seasonNAME>] with corresponding months opened
    
    '''
    ds = {}
    seasons =[ "DJF","MAM","JJA","SON"]
    season_months = {"DJF": ["12","01","02"], "MAM": ["03","04","05"],"JJA":["06","07","08"],"SON": ["09","10","11"]}

    for season in seasons:
        ds[season]=[]
               
        data = open_months(year, season_months[season],path_to_folder =path_to_folder, vars_keep = vars_keep)
        ds[season]=data
    return ds 
######################################################
# open all datasets for multiple years #
######################################################
def open_multiple_years(years,path_to_folder,vars_keep):
    import sys
    '''
    Input: 
        years = which years to open
        path_to_folder = path to folder with monthly data (from 11_xx)
        vars_keep = which variables to open 
    
    Output: Dataset of all months of the input years (with time coordinate)
    
    Dependencies: 
    - imports.open_months (& import_defs.monthly_data_name_pattern)
    - create_time_coords
    '''
    datasets= []
    months = ["01","02","03","04","05","06","07","08","09","10","11","12"]

    for year in years: 
        sys.path.append("../../tools")
        import imports
        one_year = imports.open_months(year,months,path_to_folder,vars_keep)
        datasets.append(one_year)
    combined = xr.concat(datasets, dim="time")
    return combined
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



    

