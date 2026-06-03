import numpy as np
import xarray as xr
###################################
#########   Open bins   ###########
###################################
def load_bins(bin_file):
    '''
    opens bins.npz stored at bin_file (path)
    bin file can be calculated with 'nbooks/01_data_calc/nbook 00_xx' 
    Input: path to binfile
    Output: bin edges and bin sizes
    '''
    import numpy as np
    with np.load(bin_file) as bin_data:
        lon_bins = bin_data['lon_bins'] # x edges
        d_lon = bin_data['d_lon'] # binsize x
        lat_bins = bin_data['lat_bins'] # y edges
        d_lat = bin_data['d_lat'] # binsize y
        print(f"Bins loaded from {bin_file}")
    return lon_bins,lat_bins, d_lon, d_lat
###################################
#### Daily data calculation ######
###################################

# calc sum values 
def calc_daily_data(data,lon_bins, lat_bins):
    from scipy.stats import binned_statistic_2d # for max max 
    import numpy as np
    
    '''
    Input: Segmented cells inkl. precip vars (tobac output) per timestep of the day
    Data needs latitude/longitude
    Output: dataset with daily gridded data with sums of precip. vars of all cells in one grid (lon,lat)
    '''
  
    lon = data["longitude"].values
    lat = data["latitude"].values
    ds ={}
    ds["day_counts"], xedges, yedges = np.histogram2d(lon, lat, bins=(lon_bins, lat_bins)) 
    ### sums
    # precip cell area 
    area = data["area"].values
    ds["day_sum_area"], _, _ = np.histogram2d(lon, lat, bins=(lon_bins, lat_bins), weights=area)

    # maximum precip rate of cell
    maxi = data["max"].values
    ds["day_sum_max"], _, _ = np.histogram2d(lon, lat, bins=(lon_bins, lat_bins), weights=maxi)

    # total precip per cell
    tot = data["total"].values
    ds["day_sum_tot"], _, _ = np.histogram2d(lon, lat, bins=(lon_bins, lat_bins), weights=tot)
    
    #### other (max)
    # maximum of max precip rate per cell (maxmimum value of max precipitation on that day per bin)
    ds["day_max_max"], _, _, _ = binned_statistic_2d(
        lon, lat, maxi, 
        statistic='max', 
        bins=[lon_bins, lat_bins])

    # histogram 2d returns lon,lat but lat,lon output wanted
    for key in ds:
        ds[key] = ds[key].T
    return ds

###################################
#### Add Daily mean statistics ###
###################################
# add mean statistics
def add_daily_stats(ds):
    '''
    Input: daily gridded data with sums
    Output: updated ds with means of the sums => daily mean variables
    '''
    # create a mask
    # day_counts and xxx_sum should have the same 0 values, but somehow there was still an error (runtime) during division => mask
    mask = ds["day_counts"] > 0

    ## Area
    # take shape from sum
    ds["day_mean_area"] = np.zeros_like(ds["day_sum_area"])
    # calculate average area with 0 masked 
    ds["day_mean_area"][mask] = ds["day_sum_area"][mask] / ds["day_counts"][mask] # average area of a precipitation cell in one bin 

    ## Max precip
    # take shape from sum
    ds["day_mean_max"] = np.zeros_like(ds["day_sum_max"])
    # calculate average area with 0 masked
    ds["day_mean_max"][mask] = ds["day_sum_max"][mask] / ds["day_counts"][mask]

    return ds
###################################
####### Add dA and density  ######
###################################

def add_dA(lat_bins, lon_bins, d_lon,d_lat):
    '''
    Input: bin edges and bin size (loaded bin file)
    Output: dataframe with dA
    '''
    # get lamda and phi values in radiant
    lam_bins, phi_bins = np.deg2rad(lon_bins), np.deg2rad(lat_bins)
    
    d_lam = np.deg2rad(d_lon)
    d_phi = np.deg2rad(d_lat)
    
    # set earth radius
    r_earth = 6371 #km
    
    # create array in shape of bins (-1 because bins are the edges => 5 bins mean 6 edges => 5 dA not six
    dA = np.zeros((len(phi_bins)-1, len(lam_bins)-1))
    
    # iterate over all lat bins 
    for i in range(len(phi_bins) - 1):
        dA[i, :] = (r_earth**2 * np.cos(phi_bins[i]) * d_phi * d_lam)
    return dA
  
def add_daily_density(ds):
    '''
    Input: dataset with cell counts per gridcell (day_counts) and area per grid cell (dA)
    Output: updated ds incl. daily cell density
    '''
    # calc density
    ds["day_dens"] = ds["day_counts"]/ds["dA"]
    return ds
    
###################################
#### Create a daily dataset ######
###################################
def create_daily_ds(ds,lat_bins,lon_bins, d_lat,d_lon,date): 
    import pandas as pd
    import xarray as xr
    '''
    very specific / hard for saving teh daily data calculated with calc
    Input: dir with daily data and bins (plus binsizes and date for saving)
    Output: dataset of input ds. coords are midpoints of each bin
    '''
    # Assume `date` is already defined as a string in 'YYYY-MM-DD' format for the current day
    time = pd.to_datetime(date)  # Convert date string to a pandas Timestamp for compatibility
    
    # Use midpoints for the actual data
    lat_midpoints = 0.5 * (lat_bins[:-1] + lat_bins[1:])  
    lon_midpoints = 0.5 * (lon_bins[:-1] + lon_bins[1:])  
    
    # Create an xarray Dataset
    ds = xr.Dataset(
        {key: (("time", "lat", "lon"), arr[None, :, :])
             for key, arr in ds.items()
        },
         coords={
            'time': [time],  # Add the time coordinate
            'lat': (('lat',), lat_midpoints),  # Use midpoints
            'lon': (('lon',), lon_midpoints),  
            'lat_bins': (('lat_bins',), lat_bins),  # Save full bin edges as separate coordinates
            'lon_bins': (('lon_bins',), lon_bins)
        },
    )
    
    ds.attrs['description'] = f'different variables, gridded for {date}'
    ds.attrs['resolution bins'] = f'latitudes: {d_lat}°, longitutdes: {d_lon}°'
    return ds
    
###################################
#### Save the daily dataset ######
###################################
def save_daily_ds(ds, output_path):
    import os
    '''
    Input: (daily) ds
    Output: ds saved as .nc to outputpath
    '''
    # Define encoding bc otherwise to big
    encoding = {
    name: {"dtype": "float32", "compression": "gzip", "compression_opts": 5}
    for name in ds.data_vars
    }
    
    # coordinates too
    encoding.update({
        name: {"dtype": "float32", "compression": "gzip", "compression_opts": 5}
        for name in ds.coords
        if name != "time"
    })
    
    # special case for time
    encoding["time"] = {
        "dtype": "float64",
        "units": "days since 1970-01-01",
        "calendar": "standard",
        "compression": "gzip",
        "compression_opts": 5,
    }
  
    # Save the dataset using the h5netcdf backend
    ds.to_netcdf(output_path, mode='w', engine='h5netcdf', encoding=encoding)
    

####################################################################################
#### Monthly data 
####################################################################################

###################################
#### Monthly Data calculation ######
###################################
def calc_monthly_data(data):
    '''
    input: data dir with daily data of the month
    output: data dir with monthly variables
    '''
    #### # Monthly mean metrics (pure averages)
    # 1. Sum up vars over month
    data['month_sum_day_dens'] = data['day_dens'].sum(dim='time')
    data['month_tot_counts'] = data['day_counts'].sum(dim='time') # counts month-1
    data['month_sum_area'] = data['day_sum_area'].sum(dim='time')
    data['month_sum_max'] = data['day_sum_max'].sum(dim='time')
    data['month_sum_tot'] = data['day_sum_tot'].sum(dim='time')
    # 2. total means (mean density, mean area, mean max of cells of the month)
    data['month_mean_dens'] = data['month_tot_counts'] / data['dA'][0]  # n km-2 
    data['month_mean_area'] = data['month_sum_area'] / data['month_tot_counts']  # km^2 cell-1
    data['month_mean_max'] = data['month_sum_max'] / data['month_tot_counts']  # mm cell-1
    data['month_mean_tot'] = data['month_sum_tot'] / data['month_tot_counts'] # mm/cell
    
    # Months max max precip (=Monthly max of daily max max) 
    data['month_max_max'] = data['day_max_max'].max(dim='time')
    
    #### #Monthly means of daily means/max
    
    # Monthly mean of daily max max 
    # Sum of daily maximas/ n-days
    data['month_sum_day_max_max'] = data['day_max_max'].sum(dim='time')
    data['month_mean_day_max_max'] = data['month_sum_day_max_max'] / data.sizes['time'] # mm 
    
    # Monthly mean of daily density
    data['month_mean_daily_dens'] = data['month_sum_day_dens'] / data.sizes['time']  # n km-2 day-1
    
    data = data.compute()
    
    # Drop unneeded vars
    data = data.drop_vars(['month_sum_day_dens', 'month_sum_day_max_max']) 
   
    return data


###################################
#### Create monthly dataset  ######
###################################
def create_monthly_ds(data, month):
    import pandas as pd
    '''
    put monthly data in dataset (inkl. coordinates, dA)
    input: monthly data dir
    output: monthly data in dataset with coords 
    '''
    # save monthly averaged data (for later checking)
    vars = list(data.data_vars)
    vars_month = ['month_tot_counts', 
                  'month_sum_area', 'month_sum_max','month_sum_tot',
                  'month_mean_dens', 'month_mean_area', 'month_mean_max', 'month_mean_tot',# pure monthly averages 
                  'month_max_max', # total max of max precip.
                  'month_mean_day_max_max' , 
                  'month_mean_daily_dens'# plot 1
                 ]
            
    # create dataset for monthly values
    data_month = data[vars_month]
    data_month["dA"] = data["dA"][0]
    
    data_month = data_month.assign_coords(
        lat_bins=("lat", data.coords["lat"].values),
        lon_bins=("lon", data.coords["lon"].values))
    
    # compute it
    data_month = data_month.compute()

    # drop old time and assign correct date
    data_month = data_month.drop("time")
    data_month = data_month.expand_dims(time=[pd.Timestamp(month)]) 
    data_month.attrs["description"] = f"different variables averaged/summed over one month {month}"
    return data_month


####################################################################################
#### ANNUAL Data
####################################################################################

###################################
#### calculate yearly means ######
###################################

def calc_yearly_mean(data_og):
    '''
    Input: monthly data (from 11_xx) for a year 
    Output: Yearly means of monthly variables
    '''
    ## cell mean
    weights = data_og.month_tot_counts
    ds =xr.Dataset()

    ds["area_cell"] =  weighted_sum_year(data_og.month_mean_area, weights)    
    ds["tot_cell"] =  weighted_sum_year(data_og.month_mean_tot, weights)  
    ds["max_cell"] =  weighted_sum_year(data_og.month_mean_max, weights)   
    

    # total counts per month (mean of monthly total counts)
    ds["sum_counts"]  = data_og.month_tot_counts.groupby("time.year").sum() # change to sum if yearly sum 
    # total area per month
    ds["sum_area"] = data_og.month_sum_area.groupby("time.year").sum() # change to sum if yearly sum
    # total precip per month
    ds["sum_tot"] = data_og.month_sum_tot.groupby("time.year").sum() # change to sum if yearly sum 

    # yearly mean monthly mean daily density
    #ds["mean_daily_dens"] = ds["sum_counts"]/data_og.dA #
    ds["mean_daily_dens"] = data_og.month_mean_daily_dens.groupby("time.year").mean() # bc mean its possible
    
    return ds

###################################
#### calculate spatial means ######
###################################
def calc_spatial_mean_per_year(data):
    '''
    Input: Yearly data from the calc_yearly_mean function
    Output: Yearly data averaged spatially (dim reduction)
    '''
    ds = xr.Dataset()
    for key in list(data.data_vars):
        if "dens" in key:
            ds[key] = data[key].mean(dim=("lat", "lon"))
        elif "sum" in key:
            ds[key] = data[key].sum(dim=("lat", "lon"))# change to sum if yearly sum
        else:  # cell-based yearly means =>  simple spatial mean bc weighted bfore
            ds[key] = data[key].mean(dim=("lat", "lon"))
    return ds

###################################
#### calculate spatial means WIEGHTED ######
###################################
def calc_spatial_mean_per_year_weighted(data, weights_variable):
    '''
    Input: Yearly data from the calc_yearly_mean function
    Output: Yearly data averaged spatially (dim reduction)
    '''
    ds = xr.Dataset()
    has_counts = weights_variable in data.data_vars 
    if has_counts:
        weights = data[weights_variable]
        for key in list(data.data_vars):
            if "dens" in key:
                #ds[key] = data[key].mean(dim=("lat", "lon")) # quatsch=> if global annual mean density => calculated directly? 
                # best would probably be area weighted spatial mean for the density => butdA is not included in the input
                continue
            elif "sum" in key:
                ds[key] = data[key].sum(dim=("lat", "lon"))# change to sum if yearly sum
            else:  # cell-based yearly means =>  simple spatial mean bc weighted bfore
                weighted = data[key].weighted(weights )
                ds[key] = weighted.mean(dim=("lat", "lon")) # weight by data["sum_counts"]
    else: 
        print(f"no {weights_variable} variable found, cannot calc spatial mean")
    return ds


###################################
#### calculate relative mean ######
###################################
def rel_means(dataset):
    '''
    Input: Dataset (Yearly data from the calc_yearly_mean function)
    Output: Dataset with variables of input dataset reltaive to mean (Yearly data averaged spatially (dim reduction))
    '''
    rels = xr.Dataset()
    for key in list(dataset.data_vars):
        rels[key]= dataset[key]/dataset[key].mean()
    return rels
###################################
#### calculate weighted  mean  help function ######
###################################
def weighted_sum_year(tmp,weights):
    '''
    Input: Monthly data of one year (1 Variable)
            weights (cell counts per month) 
            => used in calc_yearly_mean fct!
    Output: Yearly mean of cell variables (as weights by counts)
    '''
    ave = (tmp * weights).groupby("time.year").sum()/weights.groupby("time.year").sum()
    return ave
###################################
#### calculate yearly stats ######
###################################
def get_yearly_stats(data_og):
    '''
    Input
        data_og => monthly data for timeperiod
    Output: Annual stats, globally averaged => dir with absolute and relative stats
    '''
    import calc_data
    # yearly means
    year_ave = calc_data.calc_yearly_mean(data_og)
    # yearly global means
    abso = calc_data.calc_spatial_mean_per_year_weighted(year_ave, "sum_counts")
    # rel yearly global means
    rela = calc_data.rel_means(abso)    
    #abso,rela
    
    yearly_stats = { # to match the sturcture of boot dir
        "abso": {"mean": abso},
        "rela": {"mean": rela},
    }
    return yearly_stats

###################################
#### create yearly bootstrapps  ######
###################################
def create_bootstrap_samples(data,years,n_boot=500):
    '''
    Input
        data => monthly data for timeperiod
        years => years array
        n_boot => how many bootstrapping samples
    Output: dataset with annual stats for each bootstrapped sample
    '''
    #n_boot = 500
    # data
    
    res_boot = []
    np.random.seed(123)
    
    # dataset bootstrappen und jeweils means ausrechnen
    for _ in range(n_boot):
        # create n bootstrap samples
        sampled_dfs = []
        years_int = [int(y) for y in years]
        for y in years_int:
            months_in_year = data.sel(time=data.time.dt.year == y)
            # monate mit zurücklegen
            sampled_months = months_in_year.isel(time=np.random.randint(0, months_in_year.time.size, months_in_year.time.size))
            sampled_dfs.append(sampled_months)
        ds_sample = xr.concat(sampled_dfs, dim="time")
        
        # calculate global yearly means for each sample (avergae over lon, lat, time)
        import calc_data
        year_ave = calc_data.calc_yearly_mean(ds_sample)
        spatial_ave = calc_data.calc_spatial_mean_per_year_weighted(year_ave, "sum_counts")
    
        # append to one dir
        res_boot.append(spatial_ave)
    return res_boot

###################################
#### calculate yearly boottrap stats ######
###################################

def get_yearly_bootstrap_stats(res_boot, alpha = 0.1):
    '''
    INPUT: res_boot: bootstrap sampled (from create_bootstrap_samples)
    OUTPUT: dir with abs and rel yearly averages, inkl. ci
    structure: yearly_stats_boot["abso"]["mean"]
    '''
    # create dir for bootstraps per variables
    all_vars = {var: [] for var in list(res_boot[0].data_vars)}
    
    for d in res_boot:
        for var in d.data_vars:
            all_vars[var].append(d[var])
            
    # calc robust stats per variables
    robust_stats = {}
    
    for var, darrs in all_vars.items():
        da_boot = xr.concat(darrs, dim="boot")  # (boot, year)
    
        robust_stats[var] = {
            "mean": da_boot.mean(dim="boot"),
            "ci_low": da_boot.quantile((0+(alpha/2)), dim="boot"),
            "ci_up": da_boot.quantile((1-(alpha/2)), dim="boot"),
        }
    
    # same shape as abso above
    abso_boot = xr.Dataset()
    for k in robust_stats.keys():
        abso_boot[k] = robust_stats[k]["mean"]  
    ci_low_abso = xr.Dataset()
    for k in robust_stats.keys():
        ci_low_abso[k] = robust_stats[k]["ci_low"]
    ci_high_abso= xr.Dataset()
    for k in robust_stats.keys():
        ci_high_abso[k] = robust_stats[k]["ci_up"]
    import calc_data
    # caclulate relative means
    rela_boot = calc_data.rel_means(abso_boot)   
    ci_low_rel = calc_data.rel_means(ci_low_abso)   
    ci_high_rel = calc_data.rel_means(ci_high_abso) 


    # put in dir
    yearly_stats_boot = {
        "abso": {
            "mean": abso_boot,
            "ci_low": ci_low_abso,
            "ci_high": ci_high_abso,
        },
        "rela": {
            "mean": rela_boot,
            "ci_low": ci_low_rel,
            "ci_high": ci_high_rel,
        },
    }
    

    return (yearly_stats_boot)
    
###################################
#### calculate yearly slopes ######
###################################

def calc_slope(data, n_boot = 500):
    from sklearn.utils import resample
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    from scipy import stats
    import pandas as pd
    '''
    Input: dataset with annual data for variables
    Output: linear slope based on bootstrapping and CIs etc. as Dataframe
    '''
    
    dir_lm = []
    
    for var in list(data.data_vars):
        x = np.array(data.year, dtype=int).reshape((-1, 1))
        y = data[var].values
    
        # fit linear regression auf OG daten
        model = LinearRegression().fit(x, y)
        intercept_ = model.intercept_
        slope_ = model.coef_[0]
    
        # predictions und residuals
        y_pred = model.predict(x)
        residuals = y - y_pred
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        r_sq = model.score(x, y)
    
        # Bootstrap für unsicherhiet slope
        slopes_boot = []
        for _ in range(n_boot):
            x_sample, y_sample = resample(x, y)
            model_boot = LinearRegression().fit(x_sample, y_sample)
            slopes_boot.append(model_boot.coef_[0])
    
        slope_ci_lower = np.percentile(slopes_boot, 2.5)
        slope_ci_upper = np.percentile(slopes_boot, 97.5)
    
        # Save results
        dir_lm.append({
            "variable": var,
            "intercept": intercept_,
            "slope": slope_,
            "slope_ci_lower": slope_ci_lower,
            "slope_ci_upper": slope_ci_upper,
            "mse": mse,
            "rmse": rmse,
            "r_sq": r_sq
        })
        
    df_results = pd.DataFrame(dir_lm)
    return df_results

###################################
#### change to per K (slope)  ######
# ###################################
# def change_to_per_T(df_results, T_trend = 0.044):
#     # change from %/year to %/K
#     #T_trend = 0.044  # K / year
    
#     # update df
#     df_results_updated = df_results.copy()
#     df_results_updated["slope"] = df_results["slope"] / T_trend
#     df_results_updated["slope_ci_lower"] = df_results["slope_ci_lower"] / T_trend
#     df_results_updated["slope_ci_upper"] = df_results["slope_ci_upper"] / T_trend
#     return df_results_updated

######################################################
# calculate mean along time dim for opended datasets #
######################################################

def get_temporal_mean_dataset(dataset): 
    import xarray as xr
    '''
    input: dataset with time dimension
    dataset = dataset with time dim to average (name sets is remainer from before)
    '''
    # Assuming `datasets` contains the datasets to be averaged
    sel_months_df = dataset.mean(dim="time")
    return sel_months_df


def get_temporal_mean_per_ds_in_dir(data):
    '''
    Input: dir with subdirs that monthly datasets with time dim
    Ouptut: Dir with 
    '''
    ds ={}
    dir_keys = data.keys()
    
    for subset in dir_keys:  
        ds[subset]= data[subset].mean(dim="time")
    return ds  

######################################################
# create mask for subsetting #
######################################################
def create_mask(ds, shp_path):
    '''
    Input: dataset (1 file with grid for which mask shoul dbe created) + path to shapefile for land ocean mask
    Output: Dir as mask with "surface_mask" (land/ocean) and hemisphere mask (SH/NH)
    '''
    import xarray as xr
    import numpy as np
    from shapely.geometry import Point
    import geopandas as gpd
    # function to create ocean/land mask for given data
    lat = ds.lat.values
    lon = ds.lon.values
    
    # === 2. Create point geometries for each grid cell center ===
    lon2d, lat2d = np.meshgrid(lon, lat)
    points = [Point(x, y) for x, y in zip(lon2d.ravel(), lat2d.ravel())]
    gdf_points = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
    
    # === 3. Natural earth (manual download)
    # Download from: natural earth 110m
    ocean = gpd.read_file(shp_path)  # <-- adjust path
    if ocean.crs != "EPSG:4326":
        ocean = ocean.to_crs("EPSG:4326")
    
    # === 4. Determine which grid points are ocean ===
    ocean_union = ocean.unary_union
    gdf_points["is_ocean"] = gdf_points.geometry.within(ocean_union)
    
    # === 5. Convert to 2D mask (1 = ocean, 0 = land) ===
    mask_flat = np.where(gdf_points["is_ocean"], 1, 0)
    mask_2d = mask_flat.reshape(lat.size, lon.size)
    
    # # === Add NH / SH flag ===
    gdf_points["NH"] = gdf_points.geometry.y > 0
    
    # === 5. Convert to 2D mask (1 = NH, 0 = SH) ===
    mask_flat = np.where(gdf_points["NH"], 1, 0)
    mask_2d_hem = mask_flat.reshape(lat.size, lon.size)
    
    # === 6. Build xarray Dataset ===
    ds_mask = xr.Dataset(
        {
            "surface_mask": (("lat", "lon"), mask_2d),
            "hemisphere_mask": (("lat", "lon"), mask_2d_hem)
        },
        coords={
            "lat": lat,
            "lon": lon,
        },
    )
    ds_mask.attrs["description"] = "surface_mask (1=ocean, 0=land), hemisphere_mask (1 = NH, 0 = SH)"
    ds_mask.attrs["source"] = "Natural Earth 110m Ocean polygon"
    return ds_mask
########################################
# split ds in ref and comp #####
#######################################
def split_ds(data,years_ref, years_comp):
    '''
    Input: dataset with yearly data for each pixel
    Output: splited datasets
    '''
    # calc
    ref = data.sel(year=[int(y) for y in years_ref])
    comp = data.sel(year=[int(y) for y in years_comp])
    
    return(ref,comp)  
########################################
# get bootstrammped sampled of T data and annual means of each #####
#######################################
def bootstrapped_T_mean(data,years,n_boot = 500):
    res_boot = []
    np.random.seed(123)
    
    # dataset bootstrappen und jeweils means ausrechnen
    for _ in range(n_boot):
        # create n bootstrap samples
        sampled_dfs = []
        years_int = [int(y) for y in years]
        for y in years_int:
            months_in_year = data.sel(time=data.time.dt.year == y)
            # monate mit zurücklegen
            sampled_months = months_in_year.isel(time=np.random.randint(0, months_in_year.time.size, months_in_year.time.size))
            sampled_dfs.append(sampled_months)
        ds_sample = xr.concat(sampled_dfs, dim="time")

        # calc yearly mean
        year_ave = ds_sample.groupby("time.year").mean()

        res_boot.append(year_ave)
    return res_boot
########################################
# get slopes of sir with dataarrays #####
#######################################
def calc_slope_normal_dirwithdataarrays(ts_means):
    from scipy.stats import linregress
    
    # Prepare containers
    T_trends = {}
    
    
    # annual means and then trend
    for key, ts in ts_means.items():
        t_annual  = ts 
        # Exclude specific years
        exclude_years = [2020]#, 2021, 2022]
        t_annual_var_filtered = t_annual.sel(year=~t_annual["year"].isin(exclude_years))
        
        # Years and values for regression
        years_filtered = t_annual_var_filtered["year"].values
        values_filtered = t_annual_var_filtered.values
        
        # Linear regression over years, excluding 2020
        # use year coordinate, not np.arange
        slope, intercept, r_value, p_value, std_err = linregress(years_filtered, values_filtered)
      
        T_trends[key] = slope
        print(f"{key}: annual warming trend = {slope:.4f} °C/year")
    return  T_trends

########################################
# get slopes relative to T #####
#######################################

def calc_slope_perT(data, ts_mean, n_boot=500):
    from sklearn.utils import resample
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    import pandas as pd
    '''
    Input: dataset with annual data for variables, ts_mean is annual mean T DataArray with year dim
    Output: linear slope per K (instead of per year) based on bootstrapping and CIs
    '''
    
    dir_lm = []
    
    # use annual mean T as x instead of year
    x = ts_mean.sel(year=data.year).values.reshape((-1, 1))
    
    for var in list(data.data_vars):
        y = data[var].values
    
        # fit linear regression on original data
        model = LinearRegression().fit(x, y)
        intercept_ = model.intercept_
        slope_ = model.coef_[0]
    
        # predictions and residuals
        y_pred = model.predict(x)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        r_sq = model.score(x, y)
    
        # Bootstrap for slope uncertainty
        slopes_boot = []
        for _ in range(n_boot):
            x_sample, y_sample = resample(x, y)
            model_boot = LinearRegression().fit(x_sample, y_sample)
            slopes_boot.append(model_boot.coef_[0])
    
        slope_ci_lower = np.percentile(slopes_boot, 2.5)
        slope_ci_upper = np.percentile(slopes_boot, 97.5)
    
        dir_lm.append({
            "variable": var,
            "intercept": intercept_,
            "slope": slope_,
            "slope_ci_lower": slope_ci_lower,
            "slope_ci_upper": slope_ci_upper,
            "mse": mse,
            "rmse": rmse,
            "r_sq": r_sq
        })
        
    df_results = pd.DataFrame(dir_lm)
    return df_results
    
########################################
# get slopes relative to T FROM ERROR BAR SPACE #####
#######################################

def calc_slope_perT_fromerr(var_means, t_means, var_ci_low, var_ci_upper, 
                             t_ci_low, t_ci_upper, n_boot=500, alpha=0.1):
    """
    Input: 
        var_means   : xarray Dataset with annual variable data
        t_means     : xarray DataArray with annual temperature data
        var_ci_low  : xarray Dataset, lower CI for variables
        var_ci_upper: xarray Dataset, upper CI for variables
        t_ci_low    : xarray DataArray, lower CI for temperature
        t_ci_upper  : xarray DataArray, upper CI for temperature
        n_boot      : number of bootstrap samples
        alpha       : significance level for CI (default 0.1 => 90% CI)
    Output: 
        df_results      : DataFrame with slope statistics (same schema as calc_slope)
        df_all_slopes   : DataFrame with all bootstrap slope values per variable
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    import pandas as pd
    from scipy.stats import norm

    dir_lm = []
    all_slopes = {}  # variable -> list of bootstrap slopes
    all_intercepts = {}

    # T array (x axis)
    t_vals     = t_means.values.astype(float)
    t_low      = t_ci_low.values.astype(float)
    t_high     = t_ci_upper.values.astype(float)
    n_years    = len(t_vals)

    # T distri of CI for bootstrapping
    z_score = norm.ppf(1 - alpha / 2)  # to get 1.64 for alpha 10% e.g. 
    t_std  = (t_high - t_low) / (2 * z_score) # ci = mean+- 1.64 * sigma => ci low-ci up / 2 = 1.64 * sigma => umstellen

    for var in list(var_means.data_vars):
        y_vals  = var_means[var].values.astype(float)
        y_low   = var_ci_low[var].values.astype(float)
        y_high  = var_ci_upper[var].values.astype(float)

        # # fit on original data (mean of bootstrapped annual means)
        # x_orig = t_vals.reshape(-1, 1)
        # model  = LinearRegression().fit(x_orig, y_vals)
        # intercept_ = model.intercept_
        # slope_      = model.coef_[0]
        # # maybe also just leave this out 
        # y_pred    = model.predict(x_orig)
        # residuals = y_vals - y_pred
        # mse       = mean_squared_error(y_vals, y_pred)
        # rmse      = np.sqrt(mse)
        # r_sq      = model.score(x_orig, y_vals)

        ####  Bootstrap by sampling within CI error-bar space
        # get y distri of CI
        y_std  = (y_high - y_low) / (2 * z_score)
        
        slopes_boot = []
        intercepts_boot = []
        
        for _ in range(n_boot):
            # sample T and var independently, year by year, within CI
            t_sample = np.random.normal(t_vals, t_std)
            y_sample = np.random.normal(y_vals, y_std)
            
            model_boot = LinearRegression().fit(t_sample.reshape(-1, 1), y_sample)
            slopes_boot.append(model_boot.coef_[0])
            intercepts_boot.append(model_boot.intercept_)  

        all_slopes[var] = slopes_boot
        all_intercepts[var] = intercepts_boot

        # get mean slope and mean intercept 
        slope_mean = np.mean(slopes_boot)
        intercept_mean = np.mean(intercepts_boot)

        # pick ci lower/upper slope and corresponding intercept
        # Sort bootstrap samples by slope
        sorted_idx = np.argsort(slopes_boot)
        slopes_sorted     = np.array(slopes_boot)[sorted_idx]
        intercepts_sorted = np.array(intercepts_boot)[sorted_idx]

        # get percentils correpsonding to alpha
        lo_pct = (alpha / 2) * 100          # e.g. 5.0  for alpha=0.10
        hi_pct = (1 - alpha / 2) * 100      # e.g. 95.0 for alpha=0.10
        
        # Pick the pairs at the CI percentile positions
        lo_idx = int(np.floor(lo_pct / 100 * n_boot))
        hi_idx = int(np.ceil(hi_pct / 100 * n_boot)) - 1
        
        slope_ci_lower     = slopes_sorted[lo_idx]
        slope_ci_upper     = slopes_sorted[hi_idx]
        intercept_ci_lower = intercepts_sorted[lo_idx]   # intercept paired with lowest slope
        intercept_ci_upper = intercepts_sorted[hi_idx]   # intercept paired with highest slope

        
        dir_lm.append({
            "variable":        var,
            # from "og" data (mean of annualbootstrapping)
            # "intercept":       intercept_,
            # "slope":     slope_,

            # "mse":             mse,
            # "rmse":            rmse,
            # "r_sq":            r_sq,
            
            # from bootstrapping slopes in CI space
            "slope":slope_mean,
            "intercept": intercept_mean,
            "slope_ci_lower":  slope_ci_lower,
            "slope_ci_upper":  slope_ci_upper,
            "intercept_ci_lower":intercept_ci_lower,
            "intercept_ci_upper":intercept_ci_upper})

    df_results   = pd.DataFrame(dir_lm)
    df_all_slopes = pd.DataFrame(all_slopes)   # shape: (n_boot, n_vars)
    df_all_intercepts = pd.DataFrame(all_intercepts)

    return df_results, df_all_slopes,df_all_intercepts
    
