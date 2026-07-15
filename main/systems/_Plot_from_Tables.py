import pandas as pd
import numpy as np
import functions_for_analyze as ffa
import single_output_parser as sop
import os
import matplotlib.pyplot as pp
from importlib import reload
from matplotlib.colors import TABLEAU_COLORS 
import _daily_reporters as dr
import json
from __visuals__ import matplot
from __visuals__ import _printing_and_display_functions as pad
import _interaction_functions as IF
from matplotlib.lines import Line2D



def get_dfs(sysd, gamma=None):
    """
    Read the combined dimer_and_monomer csv for each core in sysd['cores'].

    If sysd['outer_index'] is set (e.g. 'gammas' for F12-type methods), the
    combined table has one extra index level beyond the plain (dfmp2-like)
    shape, so `gamma` must be given: the returned per-core dataframes are
    sliced to that single gamma value (via `.xs`, which drops the level),
    giving the same 2-level (tag, distances) shape as the plain case.
    """
    dfs = dict()
    cores = sysd['cores']
    outer_index = sysd.get('outer_index')
    index_col = [0, 1, 2] if outer_index is not None else [0, 1]

    for core in cores:
        sysd['core'] = core
        fname = IF.get_combined_outfile_name(sysd)
        meta, df = ffa.MakeTables.read_metacsv(
            fname,
            kwargs2=dict(header=[0,1], index_col=index_col)
        )

        if outer_index is not None:
            if gamma is None:
                raise ValueError(
                    f"sysd['outer_index']={outer_index!r} but no gamma given; "
                    "pass get_dfs(sysd, gamma=...) to select a single-gamma slice"
                )
            df = df.xs(str(gamma), level=outer_index)

        dfs[core] = dict()
        dfs[core]['meta'] = dict(meta.values)
        dfs[core]['df'] = df
    return dfs
    
def plot_single_inter(ax, x, y, *args, convert=1, **kwargs):
    x = np.array(x).astype(np.float16)
    y = convert*y
    lines = ax.plot(x, y, *args, **kwargs)
    
    ax.set_xlim(x[0], x[-2])

    #minval = min(y)
    #ax.set_ylim(minval * 1.1, abs(minval))
    return lines
    
def plot_from_plot_data(plot_data, ax=None, styles=None, convert=1, **default_plot_kwargs):
    """
    Plot lines from plot_data using compounded styles.

    Parameters
    ----------
    plot_data : list[tuple]
        Each item should be:
            (xdata, ydata, label_dict)

        Example:
            (
                xdata,
                ydata,
                {
                    "basis": "aug-cc-pVXZ",
                    "ener_key": ("HF + ", "CorrE(CBS)"),
                    "core": "all electron",
                }
            )

    ax : matplotlib.axes.Axes, optional
        Existing axis. If None, creates a new figure and axis.

    styles : dict
        Nested style dictionary:
            {
                "basis": {
                    "aug-cc-pVXZ": dict(...),
                    ...
                },
                ...
            }

    **default_plot_kwargs
        Base pyplot kwargs applied to every line.

    Returns
    -------
    fig, ax
    """
    

    if styles is None:
        styles = {}

    if ax is None:
        fig, ax = pp.subplots()
    else:
        fig = ax.get_figure()

    for xdata, ydata, labels in plot_data:
        plot_kwargs = dict(default_plot_kwargs)

        for key, value in labels.items():
            if key not in styles:
                continue

            if value not in styles[key]:
                continue

            style = styles[key][value]

            for style_key, style_value in style.items():
                if style_key == "label":
                    continue

                plot_kwargs[style_key] = style_value
        ax.plot(xdata, ydata * convert, **plot_kwargs)

    ax.axhline(0, linestyle=':', color='dimgray')
    return fig, ax

def get_style_legend(styles):
    """
    Build legend handles/labels from a nested style dictionary.

    Returns
    -------
    handles : list
    labels : list[str]
    """
    handles = []
    labels = []

    for style_group, style_map in styles.items():
        for value, style in style_map.items():
            style = dict(style)

            label = style.pop("label", str(value))

            has_marker = "marker" in style
            has_linestyle = "linestyle" in style

            handle_kwargs = {
                "color": style.pop("color", "k"),
                "linewidth": style.pop("linewidth", 2),
            }

            if has_marker:
                handle_kwargs["marker"] = style.pop("marker")
            if has_linestyle:
                handle_kwargs["linestyle"] = style.pop("linestyle")

            # If neither was specified, show a filled circle.
            if not has_marker and not has_linestyle:
                handle_kwargs.update(
                    marker="o",
                    linestyle="None",
                    markersize=7,
                )

            handle_kwargs.update(style)

            handles.append(Line2D([0], [0], **handle_kwargs))
            labels.append(label)

    return handles, labels

def plot_with_external_style_legend(plot_data,styles,
    convert=1.0,
    figsize=(7, 4), width_ratios=(4, 1), legend_kwargs=None,
    **plot_kwargs,
):
    if legend_kwargs is None:
        legend_kwargs = {}

    fig = pp.figure(figsize=figsize, constrained_layout=True)

    gs = fig.add_gridspec(nrows=1, ncols=2,
        width_ratios=width_ratios, wspace=0.05,
    )

    ax = fig.add_subplot(gs[0, 0])
    leg_ax = fig.add_subplot(gs[0, 1])

    _, ax = plot_from_plot_data(plot_data, ax=ax,
        convert=convert,
        styles=styles, **plot_kwargs,
    )

    handles, labels = get_style_legend(styles)

    leg_ax.axis("off")
    leg_ax.legend(handles, labels,
        loc="center left", frameon=False,
        **legend_kwargs,
    )

    
    return fig, ax, leg_ax


    

