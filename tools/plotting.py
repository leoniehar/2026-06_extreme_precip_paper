import os 
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

#################################
###### slope comparison plots ###
#################################
def plot_slope_comparison(
    ds,
    variable_order,
    variant_order,
    VAR_META,
    colors=None,
    hatches=None,
    ylabel='Slope (%/K)',
    ylim=(-5, 5),
    title='',
    figsize=(10,5),
    output_path=None, 
    return_ax = False,
    ax_passed = None,
    xaxislabelscale = 1.2
):
   
    """
    Plot slopes with confidence intervals for multiple variants and variables.
    Labels come from VAR_META.

    ds: xarray.Dataset with dims ['variant','variable'] containing 'slope', 'slope_ci_lower', 'slope_ci_upper'
    variable_order: list of variable keys in desired plotting order
    variant_order: list of variant names in desired plotting order
    VAR_META: dict containing 'label' for each variable
    colors: dict mapping variant -> color, or None
    ylabel, ylim, title: plot settings
    output_path: save figure if provided
    """

    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    #sns.set_context('talk', font_scale = 1.1)
  
    if colors is None:
        colors = plt.cm.Set2.colors
    if hatches is None:
        hatches = {v: '' for v in variant_order}
    
    #x = np.arange(len(variable_order))
    # classify variables dynamically
    is_cell = np.array(['cell' in v for v in variable_order])
    
    base_x = np.arange(len(variable_order), dtype=float)
    gap = 0.3
    
    # shift everything that is NOT "cell"
    x = base_x.copy()
    x[~is_cell] += gap

    
    width = 0.85 / len(variant_order)
    
    if ax_passed is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax_passed.get_figure()
        ax = ax_passed
    
    
    
    
    ax.axhline(7, color='grey', linewidth=1.2, linestyle='--', alpha=0.5,zorder= 0 )#, label='CC',zorder=0) #(~7%/K)
    ax.axhline(14, color='grey', linewidth=1.2, linestyle='--', alpha=0.2,zorder = 0)#, label='2x CC',zorder=0) #(~14%/K)'
    ax.axhline(0, color='grey', linewidth=1.2, linestyle='-', alpha=0.5,zorder=0)

    fontsizelabels_smaller = ax.xaxis.get_ticklabels()[0].get_fontsize() * 0.8 

    ax.annotate("CC",   xy=(0.95, 7),  xycoords=("axes fraction", "data"),
            va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.7, clip_on=False)
    ax.annotate("2×CC", xy=(0.95, 14), xycoords=("axes fraction", "data"),
            va="bottom", ha="left", fontsize=fontsizelabels_smaller, color="grey", alpha=0.5, clip_on=False)

    
    for i, v in enumerate(variant_order):
        slopes = ds['slope'].sel(variant=v).sel(variable=variable_order)
        lower = slopes - ds['slope_ci_lower'].sel(variant=v).sel(variable=variable_order)
        upper = ds['slope_ci_upper'].sel(variant=v).sel(variable=variable_order) - slopes
        
        slopes_scaled = slopes 
        err = np.array([lower.values, upper.values])
        
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
    ax.set_xticklabels(labels, rotation=45, ha='right',
                      fontsize=ax.xaxis.get_ticklabels()[0].get_fontsize() * xaxislabelscale
                      )

   
    
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
