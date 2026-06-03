VAR_META = {
    "month_mean_daily_dens": dict(
        unit=r'${n\,10^{-3}\,{km}^{-2}\,day^{-1}}$',
        label="Daily cell density",
        factor=1000,
    ),
    "month_mean_max": dict(
        unit=r"$\,mm\,day^{-1}$",
        label="Max. precip./cell",
        factor=1,
    ),
    "month_mean_area": dict(
        unit=r"$\,km^{2}$",
        label="Area/cell",
        factor=1,
    ),
     "month_mean_tot": dict(
        unit=r"$\,mm\,day^{-1}$",
        label="Precip./cell",
        factor=1,
    ),
}

VAR_META_ANNUAL = {
    "mean_daily_dens": {
        "color": "darkorange",
        "label": "Cell density",# (${N\,{km}^{-2}\,day^{-1}}$)",
        "label_factor": "Cell density (${N\,10^{-3}\,{km}^{-2}\,day^{-1}}$)",
        "factor":1000,
    },
    "area_cell": {
        "color": "green",
        "label": r"$A_\mathrm{cell}$",#"Area per cell",# (${km}^{2}/cell$)",
        "label_factor": "Area (${{km}^{2}/cell}$)",
        "factor":1e-6,
    },
    "tot_cell": {
        "color": "blue",
        "label": r"$R_\mathrm{cell}$",#"Total precipitation per cell",# ($mm\,day^{-1}/cell$)",
        "label_factor": "Total precipitation ($mm\,day^{-1}/cell$)",
        "factor":1,
    },
    "max_cell": {
        "color": "red",
        "label": r"$R_\mathrm{max,cell}$",#"Max. rain rate per cell",# ($mm\,day^{-1}/cell$)",
        "label_factor": "Max. rain rate ($mm\,day^{-1}/cell$)",
        "factor":1,
    },
    "sum_counts": {
        "color": "orange",
        "label": r"$N_\mathrm{tot}$",#"Total cell counts",# ($N$)",
        "label_factor": "Total cell counts (${10^{3}\,N}$)",
        "factor":1e-3,
    },
    "sum_area": {
        "color": "lightgreen",
       "label": r"$A_\mathrm{tot}$",#"Total area",# ($km{^2}$)",
        "label_factor": "Total area (${10^{6}\,{km}^{2}}$)",
        "factor":1e-12,
    },
    "sum_tot": {
        "color": "lightblue",
         "label": r"$R_\mathrm{tot}$",#"Total precipitation",# ($mm\,day^{-1}$)",
        "label_factor": "Total precipitation (${10^{6}\,mm\,day^{-1}}$)",
        "factor":1e-6,}
}
