import os 
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import seaborn as sns
#################################
###### basic plots (one line) ###
#################################
def plot_distri_precip_cells_simple(data, 
                                    var_colored="name of variable to be colored", factor= 1,  var_colored_unit="unit of colored variable", var_colored_label="set label",
                                    cmap="Spectral_r",log_on =True, vmin=None, vmax=None, subplot_shape=(1,1,1), fig=None,
                                   draw_bottom_label = True, draw_top_label = True, draw_colorbar=True,plot_label = None): 

    '''
    Input: 
        data = input dataset with variable named like 
        var_colored = varibale to be shown (included in data)
        various visualtions arguemnts
        fig = figrue where to add the (sub)plot (default None => new figure is created)
    Output: (sub)plot of one variable of tropcial belt
    '''
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.colors as mcolors
    import numpy as np
    # Check if fig is None
    if fig is None:
        fig = plt.figure(figsize=(15, 3)) 
    
    # Add subplot using Mollweide projection
    ax1 = fig.add_subplot(subplot_shape[0], subplot_shape[1], subplot_shape[2], projection=ccrs.Mollweide())
    
    # Add base map features
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.2)
    ax1.add_feature(cfeature.BORDERS, linewidth=0.2)

    # Add grid and grid labels
    gl = ax1.gridlines(draw_labels=True, linewidth=0.2, color='grey', linestyle='--', x_inline=False, y_inline=False)
    gl.xlocator = plt.FixedLocator(range(-120, 121, 60))  # Longitude: from -180° to 180°, every 60°
    gl.ylocator =  plt.FixedLocator([-23.5, 0, 23.5])    # Latitude: from -90° to 90°, every 30°

    gl.xlabel_style = {'size': 8}  # Font size for longitude labels
    gl.ylabel_style = {'size': 8}  # Font size for latitude labels

    gl.bottom_labels = draw_bottom_label
    gl.right_labels = False
    gl.top_labels = draw_top_label

    # Convert lat/lon bins for plotting
    lon_bins = data['lon_bins'].compute()
    lat_bins = data['lat_bins'].compute()

    # mask pixels with 0
    masked_data = np.ma.masked_where(data[var_colored] == 0, data[var_colored].compute())

    # Add data using pcolormesh (for gridded data)
    #pcm = ax1.pcolormesh(lon_bins, lat_bins, 
    #                    masked_data*factor, cmap=cmap, 
    #                     norm=mcolors.LogNorm(vmin = vmin, vmax=vmax),
    #                    # vmax = vmax, # aus wenn log scale
    #                     transform=ccrs.PlateCarree())

    if log_on == True: 
        # Add data using pcolormesh (for gridded data)
        pcm = ax1.pcolormesh(lon_bins, lat_bins, 
                             masked_data*factor, cmap=cmap, 
                             norm=mcolors.LogNorm(vmin = vmin, vmax=vmax),
                            # vmax = vmax, # aus wenn log scale
                             transform=ccrs.PlateCarree())
    else: 
        pcm = ax1.pcolormesh(lon_bins, lat_bins, 
                             masked_data*factor, cmap=cmap, 
                             vmin = vmin, vmax=vmax,
                             transform=ccrs.PlateCarree())

    
    # Add colorbar
    if draw_colorbar:
        cbar = fig.colorbar(pcm, ax=ax1, orientation='vertical', shrink=0.8)
        cbar.set_label(f'{var_colored_label}\n({var_colored_unit})', fontsize=10)

    if plot_label is not None:
        ax1.text(-0.1, 0.5, plot_label, transform=ax1.transAxes, fontsize=10, #fontweight="bold", 
                 ha="center", va="center", rotation = 90)

######################################
##### FCT for vmin/ max settings ######
######################################

def get_percentiles(data,low_p,high_p): 
    '''
    get percentile of data["variable"]
    if vmin = 0 -> next bigger unique value is chose
    Input: dataframe, low_p = lower percentile edge , high_p = upper percentile edge
    Output: array with low_p and high_p
    '''
    ds = data.values.flatten()
    vmin = np.nanpercentile(ds, low_p)  # Compute the low percentile
    vmax = np.nanpercentile(ds, high_p)  # Compute the high percentile
    #vmin = max(vmin, 1e-12)
    if vmin == 0:
        vmin = np.nanmin(ds[ds > 0])
    vmin_vmax = (vmin, vmax)  # Store results
    return vmin_vmax
#################################
###### percentiles calc for dataset ###
#################################
def get_vmin_vmax_p_pervariable(data,vars_plot,vmin_p,vmax_p):
    '''
    Input: data dir incl. vars_plot, percentile edges
    uses get_percnetiles function
    Output: dir for lower percentiles and dir of upper percentiles per variable
    '''
    vmin_fix_dir ={}
    vmax_fix_dir ={}
    for var in vars_plot:
        v_border = get_percentiles(data[var],vmin_p,vmax_p)
        vmin = v_border[0]
        vmax = v_border[1]
        vmin_fix_dir[var] = vmin 
        vmax_fix_dir[var] = vmax
    return vmin_fix_dir,vmax_fix_dir


#################################
###### global multiplot ###
#################################
def global_plot(data,vars_plot,  var_meta, title, output_path,mode="average",
                              fixed_v_border= False, vmin_p=10, vmax_p=90, 
                              vmin_fix = 1, vmax_fix = 2):
    '''
   Input: 
       Dataset with vars_plot
       var_meta: dir with factor, unit, label for each vars_plot
       title, outputpath (path!)
        fixed_border = False => 
            vmin/ vmax -> calculated with get_percentiles fct (above)
            if vmin = 0 -> next bigger unique value is chose
        fixed_border = True
            vminfix/vmaxfix used!
            vmin_fix = dir with variable names (like output from get_vmin_vmax_p_pervariable() output
        mode: ["average","change"] default average
    Output: plot with subplot for each vars_plot (using function plot_distri_precip_cells_simple) 
    '''
    # Create the figure
    fig = plt.figure(figsize=(12,6))

    
    if fixed_v_border == True:
        vmin  = vmin_fix
        vmax = vmax_fix
    else:
        vmin,vmax = get_vmin_vmax_p_pervariable(data,vars_plot, vmin_p = vmin_p, vmax_p = vmax_p)
        if mode == "change":
            # symmetric around zero
            for var in vars_plot:
                maxvalue = max(abs(vmin[var]), abs(vmax[var]))
                vmin[var] = -maxvalue
                vmax[var] =  maxvalue
        

    for i, var in enumerate(vars_plot, start=1):
        meta = var_meta[var]
        masked_data = data[var].squeeze() # drop dims with length 1 (e.g. time dim)
        
        plot_distri_precip_cells_simple(
            masked_data,
            fig=fig,
            var_colored=var,
            factor=meta["factor"],
            var_colored_unit=meta["unit"],
            var_colored_label=meta["label"],
            subplot_shape=(len(vars_plot), 1, i),
            cmap="BrBG" if mode == "change" else "Spectral_r",
            vmin=vmin[var] * meta["factor"],
            vmax=vmax[var] * meta["factor"],
            draw_bottom_label=(i == len(vars_plot)),
            draw_top_label=(i == 1),
            log_on=(mode == "average")
        )

    
    # Add title to the whole figure
    fig.suptitle(title, fontsize=14)
    
    # Show the figure
    plt.savefig(output_path,dpi=300, bbox_inches='tight')

#################################
###### global multiplot ###
#################################
def plot_seasonal_multiplot_ds_in_dir(data,year,
                            output_directory, vars_plot,
                            name_experiment,res_bins_name,
                            var_meta,vmin_fix,vmax_fix):
    '''
    Input: dir with ds per season 
    Output plots per season for year
    '''
    seasons = data.keys()
    for season in seasons:
        output_file = f'plot_aggr_season_{res_bins_name}_deg_{year}_{season}.png' 
        output_path  = os.path.join(output_directory,output_file)
        import plotting 
        plotting.global_plot(data = data[season], vars_plot = vars_plot, var_meta = var_meta,
                            title=  f'{year} - {season} seasonal mean of precip. cells ({name_experiment})',
                            output_path = output_path,
                            fixed_v_border = True, vmin_fix = vmin_fix, vmax_fix = vmax_fix, # this bc same scale for all months! 
                            #fixed_v_border= False,  vmin_p=5, vmax_p=95
                            )

#################################
###### BELOW annual time series plots ###
#################################


#################################
###### rel change ###
#################################
def plot_yearly_rel_change(
    data,
    variables,
    name_experiment,
    experiment,
    var_meta,
    slopes_data="",
    slopes= True,
    ylim=(0.97, 1.05),
    save = False,
    output_directory=".",
    title=""
):
    '''
    input: data, = dataset with annual data
    variables, = variables to plot (are plotted in one plot!)
    name_experiment, = nicely formatted name of threshold defeinition in tobac
    experiment, = name of tobac threshold (file name formatted) 
    var_meta, = dir with meta data for variables
    slopes_data="", = if slopes are wanted to plot => data
    slopes= True,
    ylim=(0.97, 1.05),
    save = False,
    output_directory=".", 
    title="

    Output: Line plot
    '''
    years = data.year
    years = np.array(years, dtype=int).reshape((-1, 1))

    plt.figure(figsize=(12, 6))

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    # time series + regressiom
    for var in variables:
        meta = var_meta[var]

        # time series
        plt.plot(
            years,
            data[var],
            marker="s",
            color=meta["color"],
            label=meta["label"]
        )
        if slopes == True:
            # regression parameters
            row = slopes_data.loc[slopes_data["variable"] == var].iloc[0]
            slope = row["slope"]
            intercept = row["intercept"]
            r_sq = row["r_sq"]
    
            # regression line
            plt.plot(
                years,
                intercept + slope * np.array(years),
                linestyle="--",
                linewidth=1,
                color=meta["color"],
                label=f"Slope {np.round(slope*1000, 2)} [%/dec]\nR² {np.round(r_sq, 2)}"
            )

    # layout
    plt.axhline(1, color="gray", linestyle="--", linewidth=1)
    plt.ylim(*ylim)

    plt.title(title)
    plt.xlabel("Year")

    # y-label logic
    if len(variables) == 1:
        plt.ylabel(var_meta[variables[0]]["label"])
    else:
        plt.ylabel("Relative change")

    plt.xticks(rotation=45)

    plt.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False
    )

    plt.tight_layout()

    # save
    if save == True: 
        output_file = (
            f"yearly_evolution_{experiment}_global_rel_change_line_combi{'_'.join(variables)}.png"
        )
        plt.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()


#################################
###### rel change BAR Plot ###
#################################
def plot_yearly_dev_rel(
    data,
    variables,
    name_experiment,
    experiment,
    var_meta,
    slopes_data="",
    slopes= False,
    ylim=(0.97, 1.05),
    save = False,
    output_directory=".",
    title=""):
    '''
    input: data, = dataset with annual data
    variables, = variables to plot (are plotted in one plot!)
    name_experiment, = nicely formatted name of threshold defeinition in tobac
    experiment, = name of tobac threshold (file name formatted) 
    var_meta, = dir with meta data for variables
    slopes_data="", = if slopes are wanted to plot => data
    slopes= True,
    ylim=(0.97, 1.05),
    save = False,
    output_directory=".", 
    title="

    Output: barplots
    '''
    years = data.year
    years = np.array(years, dtype=int).reshape((-1, 1))

    plt.figure(figsize=(12, 6))

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    # ---- time series + regression ----
    for var in variables:
        meta = var_meta[var]
        
        # time series
        plt.bar(
            years.flatten(),
            data[var]-1,
            #marker="s",
            color=meta["color"],
            label=meta["label"],
            width = 1
        )
        if slopes == True:
            # regression parameters
            row = slopes_data.loc[slopes_data["variable"] == var].iloc[0]
            slope = row["slope"]
            intercept = row["intercept"]-1
            r_sq = row["r_sq"]
    
            # regression line
            plt.plot(
                years,
                intercept + slope * np.array(years),
                linestyle="--",
                linewidth=1,
                color=meta["color"],
                label=f"Slope {np.round(slope*1000, 2)} [%/dec]\nR² {np.round(r_sq, 2)}"
            )

    # ---- layout & styling ----
    plt.axhline(1, color="gray", linestyle="--", linewidth=1)
    plt.ylim(*ylim)

    plt.title(title)
    plt.xlabel("Year")

    # y-label logic
    plt.ylabel("Relative change (%/yr)")

    plt.xticks(rotation=45)

    plt.legend(
        #loc="center left",
        #bbox_to_anchor=(1.02, 0.5),
        #frameon=False
        loc="lower right"
    )
    sns.despine(right=True, top=True)
    plt.tight_layout()

    #---- save ----
    if save == True: 
        output_file = (
           f"yearly_evolution_{experiment}_global_rel_change_bar_combi{'_'.join(variables)}.png"
        )
        plt.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()
    return plt

#################################
###### absolute change BAR Plot ###
#################################
def plot_yearly_dev_abs(
    data,
    variables,
    name_experiment,
    experiment,
    var_meta,
    save = False,
    output_directory=".",
    title=""):
    '''
    input: data, = dataset with annual data
    variables, = variables to plot (are plotted in one plot!)
    name_experiment, = nicely formatted name of threshold defeinition in tobac
    experiment, = name of tobac threshold (file name formatted) 
    var_meta, = dir with meta data for variables
    save = False,
    output_directory=".", 
    title="

    Output: Barplot with absolute chanegs
    '''
    
    years = data.year
    years = np.array(years, dtype=int).reshape((-1, 1))

    plt.figure(figsize=(12, 6))

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    # ---- time series + regression ----
    for var in variables:
        meta = var_meta[var]
        
        # time series
        plt.bar(
            years.flatten(),
            data[var]*meta["factor"],
            #marker="s",
            color=meta["color"],
           # label=meta["label"],
            width = 1
        )

    # ---- layout & styling ----
    plt.axhline(1, color="gray", linestyle="--", linewidth=1)

    data_range = np.max(data[var]) - np.min(data[var])
    ymin = (np.min(data[var]) - 0.05 * data_range) * meta["factor"]
    ymax = (np.max(data[var]) + 0.05 * data_range) * meta["factor"]
    
    # ymin = (np.min(data[var])-0.01*np.min(data[var]))*meta["factor"]
    # ymax = (np.max(data[var])+0.01*np.max(data[var]))*meta["factor"]
    ylim = [ymin,ymax]
    plt.ylim(*ylim)

    plt.title(title)
    plt.xlabel("Year")

    # y-label logic
    plt.ylabel(meta["label_factor"])

    plt.xticks(rotation=45)

    #plt.legend(
        #loc="center left",
        #bbox_to_anchor=(1.02, 0.5),
        #frameon=False
        #loc="lower right")

    plt.tight_layout()

    #---- save ----
    if save == True: 
        output_file = (
           f"yearly_evolution_{experiment}_global_abs_change_bar_combi{'_'.join(variables)}.png"
        )
        plt.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()


# #################################
# ###### absolute change BAR Plot SORTED by TAS ###
# #################################
# def plot_yearly_dev_abs_sorted_by_t(
#     data,
#     variables,
#     name_experiment,
#     experiment,
#     variable_name_of_temperature_data,
#     var_meta,
#     save = False,
#     output_directory=".",
#     title=""):
#     '''
#     input: data, = dataset with annual data
#     variables, = variables to plot (are plotted in one plot!)
#     name_experiment, = nicely formatted name of threshold defeinition in tobac
#     experiment, = name of tobac threshold (file name formatted) 
#     var_meta, = dir with meta data for variables
#     save = False,
#     output_directory=".", 
#     title="

#     Output: Barplot with absolute chanegs SORTED by t mean per year
#     '''
    
#     years = data.year
#     years = np.array(years, dtype=int).reshape((-1, 1))

#     plt.figure(figsize=(12, 6))

#     sns.set_context("talk")
#     sns.despine(right=True, top=True)

#     sort_idx = np.argsort(data[variable_name_of_temperature_data].values)
#     data = data.isel(year=sort_idx)
#     tas_sorted = data[variable_name_of_temperature_data].values
    
#     # ---- time series + regression ----
#     for var in variables:
#         meta = var_meta[var]
        
#         # time series
#         plt.bar(
#             tas_sorted,
#             data[var]*meta["factor"],
#             #marker="s",
#             color=meta["color"],
#            # label=meta["label"],
#             width = 1
#         )

#     # ---- layout & styling ----
#     plt.axhline(1, color="gray", linestyle="--", linewidth=1)
#     ymin = (np.min(data[var])-0.01*np.min(data[var]))*meta["factor"]
#     ymax = (np.max(data[var])+0.01*np.max(data[var]))*meta["factor"]
#     ylim = [ymin,ymax]
#     plt.ylim(*ylim)

#     plt.title(title)
#     plt.xlabel(f'{variable_name_of_temperature_data}')

#     # y-label logic
#     plt.ylabel(meta["label_factor"])

#     plt.xticks(rotation=45)

#     #plt.legend(
#         #loc="center left",
#         #bbox_to_anchor=(1.02, 0.5),
#         #frameon=False
#         #loc="lower right")

#     plt.tight_layout()

#     #---- save ----
#     if save == True: 
#         output_file = (
#            f"yearly_evolution_sorted_tas_{experiment}_global_abs_change_bar_combi{'_'.join(variables)}.png"
#         )
#         plt.savefig(
#             os.path.join(output_directory, output_file),
#             dpi=300,
#             bbox_inches="tight"
#         )
#     plt.show()


#################################
###### Plot histogramms of pixel values ###
#################################
def plot_histograms(
    ref_ds,
    comp_ds,
    variables,
    fig_title,
    figsize,
    ylim_left,
    ylim_right,
    output_path,
    VAR_META,
    log_bins=False,
    nbins = 20
):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    """
    Input: 2 dataset (for ref and for comp period) with yearly means per pixel
    meta data as VAR_META

    Output: Histogramms for each variable with 2 histograms in each plot (ref and comp period), colorcoded for each varibale based on meta data
    """
    fig, axes = plt.subplots(len(variables), 1, figsize=figsize)
    fig.suptitle(fig_title)

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    if len(variables) == 1:
        axes = [axes]

    for ax, var in zip(axes, variables):

        meta = VAR_META[var]
        factor = meta["factor"]

        values_ref = ref_ds[var].values.flatten() * factor
        values_comp = comp_ds[var].values.flatten() * factor
        
        values_ref = values_ref[np.isfinite(values_ref) & (values_ref > 0)]
        values_comp = values_comp[np.isfinite(values_comp) & (values_comp > 0)]

        
        year_period_ref=f"{ref_ds.year.min().item()}-{ref_ds.year.max().item()}"
        year_period_comp=f"{comp_ds.year.min().item()}-{comp_ds.year.max().item()}"

        # bins
        if log_bins:
            if (values_ref <= 0).any():
                raise ValueError("Log bins requested but values contain non-positive entries")
            bins = np.logspace(np.log10(values_ref.min()),
                                np.log10(values_ref.max()), nbins)
            ax.set_xscale("log")
        else:
            bins = np.linspace(values_ref.min(),
                               values_ref.max(), nbins)
            ax.set_xscale("linear")

        # if log_bins:
        #     bins = np.logspace(np.log10(values_ref.min()), np.log10(values_ref.max()), 20)
        #     ax.set_xscale("log")
        # else:
        #     # prevent trying log bins if values negative (log true but for dif not)
        #     if (values_ref <= 0).any():
        #         bins = np.linspace(values_ref.min(), values_ref.max(), 20)
        #     else:
        #         bins = np.logspace(np.log10(values_ref.min()), np.log10(values_ref.max()), 20)
        #         ax.set_xscale("log")

        # histogram counts
        ref_counts, bin_edges = np.histogram(values_ref, bins=bins)
        comp_counts, _ = np.histogram(values_comp, bins=bins)

        diff_counts = comp_counts - ref_counts
        bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

        # histograms
        ax.hist(
            values_ref,
            bins=bins,
            alpha=0.5,
            color="grey",
            label=year_period_ref,
        )

        ax.hist(
            values_comp,
            bins=bins,
            alpha=0.5,
            color=meta["color"],
            label=year_period_comp,
        )

        # difference axis
        ax2 = ax.twinx()
        ax2.bar(
            bin_centers,
            diff_counts,
            width=np.diff(bin_edges),
            color="purple",
            alpha=0.7,
            label="Difference (comp - ref)",
        )

        ax2.axhline(0, color="k", linestyle="--", linewidth=0.8)

        # labels
        xlabel = (
            meta.get("label_factor", meta["label"])
            if factor != 1
            else meta["label"]
        )

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Frequency (counts)")
        ax2.set_ylabel("Difference (comp - ref)")

        ax.set_ylim(*ylim_left(var))
        ax2.set_ylim(*ylim_right(var))

        ax.legend(loc="upper right", frameon=False)
        ax2.legend(loc="lower right", frameon=False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.show()

#################################
###### Plot histogramms of pixel values compare LAND and OCEAN ###
#################################
def plot_histograms_ocean_land(
    ref_ds,      # Land
    comp_ds,     # Ocean
    variables,
    fig_title,
    figsize,
    ylim_left,
    output_path,
    VAR_META,
    log_bins=False,
    nbins = 200
):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    """
    Input: 2 datasets (land and ocean) with yearly means per pixel

    Output: Histograms for each variable with 2 histograms in each plot
            (Land vs Ocean), color-coded based on VAR_MET
            cummulative
    """
    fig, axes = plt.subplots(len(variables), 1, figsize=figsize)
    fig.suptitle(fig_title)

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    if len(variables) == 1:
        axes = [axes]

    for ax, var in zip(axes, variables):

        meta = VAR_META[var]
        factor = meta["factor"]

        # Extract values
        values_land = ref_ds[var].values.flatten() * factor
        values_ocean = comp_ds[var].values.flatten() * factor

        # Clean values
        values_land = values_land[np.isfinite(values_land)]
        values_ocean = values_ocean[np.isfinite(values_ocean)]

        label_land = "Land"
        label_ocean = "Ocean"

        # bins
        vmin = min(values_land.min(), values_ocean.min())
        vmax = max(values_land.max(), values_ocean.max())

        if log_bins:
            if vmin <= 0:
                raise ValueError("Log bins requested but values contain non-positive entries")
            bins = np.logspace(np.log10(vmin), np.log10(vmax), nbins)
            ax.set_xscale("log")
        else:
            bins = np.linspace(vmin, vmax,nbins)
            ax.set_xscale("linear")

        # histogram densities (normalized)
        land_counts, bin_edges = np.histogram(values_land, bins=bins, density=True)
        ocean_counts, _ = np.histogram(values_ocean, bins=bins, density=True)

        diff_counts = ocean_counts - land_counts
        bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

        # histograms
        ax.hist(
            values_land,
            bins=bins,
            alpha=0.5,
            color=meta["color"],
            hatch="",
            label=label_land,
            density=True,
        )

        ax.hist(
            values_ocean,
            bins=bins,
            alpha=0.5,
            color=meta["color"],
            hatch="/////",
            label=label_ocean,
            density=True,
        )

        # labels 
        xlabel = (
            meta.get("label_factor", meta["label"])
            if factor != 1
            else meta["label"]
        )

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Probability density")
        

        # --- Y-limits: only set if provided ---
        if ylim_left is not None:
            ax.set_ylim(*ylim_left(var))
            
        ax.legend(loc="upper right", frameon=False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.show()


#################################
###### Plot CUMMULATIVE histogramms of pixel values compare LAND and OCEAN ###
#################################
def plot_cum_histograms_ocean_land(
    ref_ds,      # Land
    comp_ds,     # Ocean
    variables,
    fig_title,
    figsize,
    ylim_left,
    output_path,
    VAR_META,
    log_bins=False,
    nbins = 200
):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    """
    Input: 2 datasets (land and ocean) with yearly means per pixel

    Output: Histograms for each variable with 2 histograms in each plot
            (Land vs Ocean), color-coded based on VAR_META
            cummulative hist
            
    """
    fig, axes = plt.subplots(len(variables), 1, figsize=figsize)
    fig.suptitle(fig_title)

    sns.set_context("talk")
    sns.despine(right=True, top=True)

    if len(variables) == 1:
        axes = [axes]

    for ax, var in zip(axes, variables):

        meta = VAR_META[var]
        factor = meta["factor"]

        # Extract values
        values_land = ref_ds[var].values.flatten() * factor
        values_ocean = comp_ds[var].values.flatten() * factor

        # Clean values
        values_land = values_land[np.isfinite(values_land)]
        values_ocean = values_ocean[np.isfinite(values_ocean)]

        label_land = "Land"
        label_ocean = "Ocean"

        # bins
        vmin = min(values_land.min(), values_ocean.min())
        vmax = max(values_land.max(), values_ocean.max())

        if log_bins:
            if vmin <= 0:
                raise ValueError("Log bins requested but values contain non-positive entries")
            bins = np.logspace(np.log10(vmin), np.log10(vmax), nbins)
            ax.set_xscale("log")
        else:
            bins = np.linspace(vmin, vmax,nbins)
            ax.set_xscale("linear")

        # histogram densities (normalized)
        land_counts, bin_edges = np.histogram(values_land, bins=bins, density=True)
        ocean_counts, _ = np.histogram(values_ocean, bins=bins, density=True)

        diff_counts = ocean_counts - land_counts
        bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

        # histograms
        ax.hist(
            values_land,
            bins=bins,
            alpha=0.5,
            color=meta["color"],
            histtype="step",
            cumulative=True,
            #hatch="",
            label=label_land,
            density=True,
        )

        ax.hist(
            values_ocean,
            bins=bins,
            alpha=0.5,
            color=meta["color"],
            histtype="step",
            cumulative=True,
            linestyle = "--",
            #hatch="/////",
            label=label_ocean,
            density=True,
        )

        # labels 
        xlabel = (
            meta.get("label_factor", meta["label"])
            if factor != 1
            else meta["label"]
        )

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Probability density")
        

        # --- Y-limits: only set if provided ---
        if ylim_left is not None:
            ax.set_ylim(*ylim_left(var))
            
        ax.legend(loc="upper right", frameon=False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.show()


#################################
###### Plot 2 D histogramms of pixel values ###
#################################
def plot_x_y(var_x, var_y, 
             ref_ds, 
             comp_ds, 
             VAR_META,
             output_dir):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, TwoSlopeNorm
    '''
    input: 2 datasets with yearly means per pixel, 2 input variables to plot
    => difference is calculate like 
    H_diff = H_comp - H_ref
    '''
    year_period_ref = f"{ref_ds.year.min().item()}-{ref_ds.year.max().item()}"
    year_period_comp = f"{comp_ds.year.min().item()}-{comp_ds.year.max().item()}"

    # --- mask and flatten, filter non-finite and zeros ---
    mask_ref = (np.isfinite(ref_ds[var_x].values.flatten()) & 
                np.isfinite(ref_ds[var_y].values.flatten()) &
                (ref_ds[var_x].values.flatten() > 0) & 
                (ref_ds[var_y].values.flatten() > 0))
    x_ref = ref_ds[var_x].values.flatten()[mask_ref]
    y_ref = ref_ds[var_y].values.flatten()[mask_ref]

    mask_comp = (np.isfinite(comp_ds[var_x].values.flatten()) & 
                 np.isfinite(comp_ds[var_y].values.flatten()) &
                 (comp_ds[var_x].values.flatten() > 0) & 
                 (comp_ds[var_y].values.flatten() > 0))
    x_comp = comp_ds[var_x].values.flatten()[mask_comp]
    y_comp = comp_ds[var_y].values.flatten()[mask_comp]
    
    # --- bins (log scale) ---
    x_bins = np.logspace(np.log10(x_ref.min()), np.log10(x_ref.max()), 100)
    y_bins = np.logspace(np.log10(y_ref.min()), np.log10(y_ref.max()), 100)

    # --- 2D histograms ---
    H_ref, xedges, yedges = np.histogram2d(x_ref, y_ref, bins=(x_bins, y_bins))
    H_comp, _, _ = np.histogram2d(x_comp, y_comp, bins=(xedges, yedges))

    # Calc dif
    H_diff = H_comp - H_ref

    # --- layout ---
    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    fontsize_labels = 13
    fontsize_title = 14

    # --- REF ---
    im_ref = axs[0].pcolormesh(xedges, yedges, H_ref.T, 
                               cmap='jet', shading='auto', norm=LogNorm(vmin=5, vmax=3000))
    axs[0].set_title(f'ref ({year_period_ref})', fontsize=fontsize_title)
    axs[0].set_xscale('log'); axs[0].set_yscale('log')
    axs[0].set_xlabel(VAR_META[var_x]['label'], fontsize=fontsize_labels)
    axs[0].set_ylabel(VAR_META[var_y]['label'], fontsize=fontsize_labels)
    fig.colorbar(im_ref, ax=axs[0], label="Counts")

    # --- COMP ---
    im_comp = axs[1].pcolormesh(xedges, yedges, H_comp.T, 
                                cmap='jet', shading='auto', norm=LogNorm(vmin=5, vmax=3000))
    axs[1].set_title(f'comp ({year_period_comp})', fontsize=fontsize_title)
    axs[1].set_xscale('log'); axs[1].set_yscale('log')
    axs[1].set_xlabel(VAR_META[var_x]['label'], fontsize=fontsize_labels)
    fig.colorbar(im_comp, ax=axs[1], label="Counts")

    # --- DIFF ---
    norm = TwoSlopeNorm(vcenter=0, vmin=-np.max(np.abs(H_diff)), vmax=np.max(np.abs(H_diff)))
    im_diff = axs[2].pcolormesh(xedges, yedges, H_diff.T, cmap='bwr', norm=norm, shading='auto')
    axs[2].set_title('Difference (comp - ref)', fontsize=fontsize_title)
    axs[2].set_xscale('log'); axs[2].set_yscale('log')
    axs[2].set_xlabel(VAR_META[var_x]['label'], fontsize=fontsize_labels)
    #axs[2].set_ylabel(VAR_META[var_y]['label'], fontsize=fontsize_labels)
    fig.colorbar(im_diff, ax=axs[2], label="Difference counts")
    
    # --- save figure ---
    os.makedirs(output_dir, exist_ok=True)
    filename = f"2D_Hist_{var_x}_{var_y}.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()
#################################
###### slope comparison plots ###
#################################
def plot_slope_comparison(
    ds,
    variable_order,
    variant_order,
    VAR_META,
    T_trend=1.0,
    colors=None,
    hatches=None,
    ylabel='Slope (%/K)',
    ylim=(-5, 5),
    title='',
    figsize=(10,5),
    output_path=None, 
    return_ax = False,
    ax_passed = None
):
   
    """
    Plot slopes with confidence intervals for multiple variants and variables.
    Labels come from VAR_META.

    ds: xarray.Dataset with dims ['variant','variable'] containing 'slope', 'slope_ci_lower', 'slope_ci_upper'
    si_lower and si_upper = represent the absolute value 
    variable_order: list of variable keys in desired plotting order
    variant_order: list of variant names in desired plotting order
    VAR_META: dict containing 'label' for each variable
    T_trend: scaling factor for slopes
    colors: dict mapping variant -> color, or None
    ylabel, ylim, title: plot settings
    output_path: save figure if provided
    """

    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    sns.set_context('talk')
  
    if colors is None:
        colors = plt.cm.Set2.colors
    if hatches is None:
        hatches = {v: '' for v in variant_order}
    
    #x = np.arange(len(variable_order))
    # classify variables dynamically
    is_cell = np.array(['cell' in v for v in variable_order])
    
    base_x = np.arange(len(variable_order), dtype=float)
    gap = 0.8
    
    # shift everything that is NOT "cell"
    x = base_x.copy()
    x[~is_cell] += gap

    
    width = 0.8 / len(variant_order)
    
    if ax_passed is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax_passed.get_figure()
        ax = ax_passed
    
    
    
    
    ax.axhline(7, color='grey', linewidth=1.2, linestyle='--', alpha=0.5,zorder= 0 )#, label='CC',zorder=0) #(~7%/K)
    ax.axhline(14, color='grey', linewidth=1.2, linestyle='--', alpha=0.2,zorder = 0)#, label='2x CC',zorder=0) #(~14%/K)'
    ax.axhline(0, color='grey', linewidth=1.2, linestyle='-', alpha=0.5,zorder=0)

    fontsizelabels_smaller = ax.xaxis.get_ticklabels()[0].get_fontsize() * 0.8 

    # ax.annotate("CC",   xy=(len(variable_order) - 0.05, 7),  xycoords=("data", "data"),
    #             va="bottom", ha="right", fontsize = fontsizelabels_smaller,color="grey", alpha=0.7)
    # ax.annotate("2×CC", xy=(len(variable_order) - 0.05, 14), xycoords=("data", "data"),
    #             va="bottom", ha="right",fontsize = fontsizelabels_smaller,  color="grey", alpha=0.5)
    ax.annotate("CC",   xy=(1.01, 7),  xycoords=("axes fraction", "data"),
            va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.7, clip_on=False)
    ax.annotate("2×CC", xy=(1.01, 14), xycoords=("axes fraction", "data"),
            va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.5, clip_on=False)

    
    for i, v in enumerate(variant_order):
        slopes = ds['slope'].sel(variant=v).sel(variable=variable_order)
        lower = slopes - ds['slope_ci_lower'].sel(variant=v).sel(variable=variable_order)
        upper = ds['slope_ci_upper'].sel(variant=v).sel(variable=variable_order) - slopes
        
        slopes_scaled = slopes / T_trend
        err = np.array([(lower / T_trend).values, (upper / T_trend).values])
        
        ax.bar(
            x + i*width,
            slopes_scaled*100,
            width,
            yerr=err*100,
            capsize=4,
            label=v,
            color=colors[v] if isinstance(colors, dict) else colors[i % len(colors)],
            hatch=hatches.get(v, ''),
            alpha=1,
            edgecolor='black',
            zorder=2
        )
    
    # use VAR_META for x-axis labels
    labels = [VAR_META[var]['label'] for var in variable_order]
    centers = x + (len(variant_order)-1)*width/2
    cell_idx = np.where(is_cell)[0]
    sum_idx  = np.where(~is_cell)[0]
    
    if len(cell_idx) > 0 and len(sum_idx) > 0:
        # position = midpoint between last "cell" and first "non-cell"
        sep_x = (centers[cell_idx].max() + centers[sum_idx].min()) / 2
        
        ax.plot(
            [sep_x, sep_x],
            [0, 1],
            transform=ax.get_xaxis_transform(),  # <- key
            color='white',
            linewidth=15,
            zorder=3,
            clip_on=False
        )
    
    ax.set_xticks(centers)
    #ax.set_xticks(x + (len(variant_order)-1)*width/2)
    ax.set_xticklabels(labels, rotation=45, ha='right')

   
    
    ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim)
    ax.set_title(title,fontweight='bold')

   
    
    ax.legend(
        loc='center left',
        bbox_to_anchor=(1.02, 0.5),
        frameon=False
    )
    sns.despine(right=True, top=True)
    plt.tight_layout()
    
    if output_path is not None and ax_passed is None:
        plt.savefig(output_path)
    if ax_passed is None:
        plt.show()

    if return_ax: 
        return fig,ax
    return fig

#################################
###### annual means with error bars ###
#################################
def plot_yearly_dev_abs_sorted_by_t(
    data,
    variables,
    name_experiment,
    experiment,
    variable_name_of_temperature_data,
    var_meta,
    x_label,
    data_low=None,        #  xarray Dataset with ci_low for y-variables
    data_upper=None,      #  xarray Dataset with ci_high for y-variables
    data_x_low=None,      #  xarray Dataset with ci_low for x (tas)
    data_x_upper=None,    #  xarray Dataset with ci_high for x (tas)
    annual_mean_alpha = 10, # alpha of annual mean CI
    slopes = None, # df from csv with slopes, intercept, ci_low, ci_high columns
    plot_ci_slopes = False,
    slope_alpha = 10,
    all_slopes = None, # if all slopes should be plotted 
    all_intercepts = None, # if all slopes should be plotted 
    save=False,
    output_directory=".",
    output_file = "tmp.png",
    title="",
    connect_dots = False):
    '''
    input: data, = dataset with annual data
    variables, = variables to plot (are plotted in one plot!)
    name_experiment, = nicely formatted name of threshold definition in tobac
    experiment, = name of tobac threshold (file name formatted)
    var_meta, = dir with meta data for variables
    data_low, data_upper = datasets with ci_low / ci_high for y-axis error bars (optional)
    data_x_low, data_x_upper = datasets with ci_low / ci_high for x-axis (tas) error bars (optional)
    save = False,
    output_directory=".",
    title=""

    Output: Scatter plot with absolute changes SORTED by t mean per year,
            with optional CI error bars on both axes.
    '''
    import matplotlib
    
    plt.figure(figsize=(12, 6))

    sns.set_context("talk")
    

    sort_idx = np.argsort(data[variable_name_of_temperature_data].values)
    data = data.isel(year=sort_idx)
    tas_sorted = data[variable_name_of_temperature_data].values

    # Sort CI datasets by the same index
    if data_low is not None:
        data_low = data_low.isel(year=sort_idx)
    if data_upper is not None:
        data_upper = data_upper.isel(year=sort_idx)
    if data_x_low is not None:
        data_x_low = data_x_low.isel(year=sort_idx)
    if data_x_upper is not None:
        data_x_upper = data_x_upper.isel(year=sort_idx)

    # Compute x-axis error bars (tas CI), if available
    if data_x_low is not None and data_x_upper is not None:
        x_err_low  = tas_sorted - data_x_low[variable_name_of_temperature_data].values
        x_err_high = data_x_upper[variable_name_of_temperature_data].values - tas_sorted
        xerr = np.array([x_err_low, x_err_high])
    else:
        xerr = None

    for var in variables:
        meta = var_meta[var]
        y_vals = data[var].values * meta["factor"]

        # Compute y-axis error bars (variable CI), if available
        if data_low is not None and data_upper is not None:
            y_err_low  = y_vals - data_low[var].values  * meta["factor"]
            y_err_high = data_upper[var].values * meta["factor"] - y_vals
            yerr = np.array([y_err_low, y_err_high])
        else:
            yerr = None

        # Line connecting dots
        if connect_dots is True: 
            plt.plot(tas_sorted, y_vals,
                     '-', color="black", linewidth=0.5, zorder=4)

        # Error bars (plotted before scatter so dots sit on top)
        if xerr is not None or yerr is not None:
            plt.errorbar(
                tas_sorted, y_vals,
                xerr=xerr,
                yerr=yerr,
                fmt='none',          # no marker bc scatter draws those below
                ecolor='gray',
                elinewidth=0.8,
                capsize=3,
                capthick=0.8,
                alpha=0.6,
                zorder=4,
            )

        # Dots colored by year
        sc = plt.scatter(tas_sorted, y_vals,
                         c=data.year.values,   # already sorted
                         cmap='viridis_r' ,#'cividis_r',
                         s=80, zorder=5)

        # add main slopes
        if slopes is not None: 
            intercept = slopes.sel(variable = var)["intercept"].item()
            slope = slopes.sel(variable = var)["slope"].item()
            y_vals_slope = (intercept + slope * tas_sorted)*meta["factor"]
            plt.plot(tas_sorted, y_vals_slope, '-',color='black',linewidth=2, zorder=3,  label='Main fit')

        # confidence bands
        if plot_ci_slopes is True and all_slopes is not None and all_intercepts is not None:
            lower_p = slope_alpha/2
            upper_p = 100-lower_p
            # compute all bootstrap lines
            boot_lines = np.array([
                (all_intercepts[var].iloc[i] + all_slopes[var].iloc[i] * tas_sorted) * meta["factor"]
                for i in range(len(all_slopes))
            ])
            # take percentiles at each temperature point
            y_lower = np.percentile(boot_lines, lower_p, axis=0)
            y_upper = np.percentile(boot_lines, upper_p, axis=0)
            
            plt.fill_between(tas_sorted, y_lower, y_upper,
                             color='red', alpha=0.2, zorder=2)

        # if all slopes
        if all_slopes is not None and all_intercepts is not None:
            for i in range(len(all_slopes)):
                slope = all_slopes[var].iloc[i]
                intercept = all_intercepts[var].iloc[i]
                y_boot = (intercept + slope * tas_sorted) * meta["factor"]
                plt.plot(tas_sorted, y_boot, '-', color='grey', alpha=0.2, linewidth=0.5, zorder=1)

    # add colorbar for the dots
    plt.colorbar(sc, label='Year')

    # y lims depending on if errorbars are plotted or not
    if xerr is not None or yerr is not None:
        plt.axhline(1, color="gray", linestyle="--", linewidth=1)
        ymin = (np.min(data_low[var]) - 0.01 * np.min(data_low[var])) * meta["factor"]
        ymax = (np.max(data_upper[var]) + 0.01 * np.max(data_upper[var])) * meta["factor"]
        plt.ylim(ymin, ymax)
    else:
        ymin = (np.min(data[var])-0.01*np.min(data[var]))*meta["factor"]
        ymax = (np.max(data[var])+0.01*np.max(data[var]))*meta["factor"]
        ylim = [ymin,ymax]
        plt.ylim(*ylim)



    # legend of lines
    legend_handles = []
    if slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='black', linewidth=2, linestyle='-', label='Mean slope')
        )
    if plot_ci_slopes and slopes is not None:
        legend_handles.append(
            matplotlib.patches.Patch(facecolor='red', alpha=0.2, label=f'{slope_alpha}% CI band')
        )
    if all_slopes is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0.5, linestyle='-', alpha=0.5, label='All bootstrapped Slopes')
        )
            
    legend_handles.append(
        plt.scatter([], [], c='grey', cmap='viridis_r', s=80, label='Annual means')
    )
    
    if data_low is not None and data_upper is not None:
        legend_handles.append(
            plt.Line2D([0], [0], color='grey', linewidth=0, linestyle='none',
                       marker='|', markersize=10, markeredgewidth=1.5,
                       alpha=0.6, label=f'{annual_mean_alpha}% CI') )
    
    if legend_handles:
        # plt.legend(handles=legend_handles, loc='best', frameon=True)
        plt.subplots_adjust(bottom=0.25)
        plt.legend(handles=legend_handles,
           loc='upper center',
           bbox_to_anchor=(0.5, -0.35),
           ncol=len(legend_handles),
           frameon=True)


    # plots format
    sns.despine(right=True, top=True)
    plt.title(title)
    plt.xlabel(f'{x_label}')
    plt.ylabel(meta["label_factor"])
    plt.xticks(rotation=45)
    plt.tight_layout()
    

    # save
    if save:
        output_file = output_file
        plt.savefig(
            os.path.join(output_directory, output_file),
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()
