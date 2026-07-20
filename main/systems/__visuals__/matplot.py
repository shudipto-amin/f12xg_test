import matplotlib as mpl
import matplotlib.pyplot as pp
from matplotlib.lines import Line2D

def convert_units(ax, fac=10**(3), old='(H)', new='(mH)', which='y'):
    if which == 'y':
        get_labels = [ax.get_ylabel]
        set_labels = [ax.set_ylabel]
        
    elif which == 'x':
        get_labels = [ax.get_xlabel]
        set_labels = [ax.set_xlabel]
        
    elif which == 'both':
        get_labels = [ax.get_xlabel, ax.get_ylabel]
        

    
    for n, get_label in enumerate(get_labels):
        set_label = set_labels[n]
        oldlabel = get_label()
        newlabel = oldlabel.replace(old, new)
        set_label(newlabel)

    for line in ax.lines:
        if which == 'x':
            get_datas = [line.get_xdata]
            set_datas = [line.set_xdata]
        elif which == 'y':
            get_datas = [line.get_ydata]
            set_datas = [line.set_ydata]
        elif which == '=both':
            get_datas = [line.get_xdata, line.get_ydata]
            set_datas = [line.set_xdata, line.set_ydata]
        for n, get_data in enumerate(get_datas):
            set_data = set_datas[n]
            set_data(get_data() * fac)
        #print(newlabel)


def make_cross_legend(style_specs, color_spec):
    """
    Construct legend handles and labels from explicit style and color
    specifications.

    Parameters
    ----------
    style_specs : list[dict]
        Explicit legend entries for non-color style categories.

        Each dict must contain a "label" key. All other keys are passed
        directly to matplotlib as Line2D keyword arguments.

        Example
        -------
        style_specs = [
            {"label": "HF", "marker": "o", "color": "k"},
            {"label": "HF+CBS(CorrE)", "marker": "+", "color": "k"},
        ]

    color_spec : dict
        Specification for color-based legend entries.

        Required keys:
            "labels" : iterable
                Labels for the color entries.

            "colors" : iterable
                Colors corresponding one-to-one with "labels".

        Optional keys:
            Any additional keys are passed directly to matplotlib as
            Line2D keyword arguments for every color entry.

        Example
        -------
        color_spec = {
            "labels": cores,
            "colors": col_names,
            "ls": "-",
            "lw": 2,
        }

        or, for marker-only entries:

        color_spec = {
            "labels": cores,
            "colors": col_names,
            "marker": "s",
            "ls": "none",
        }

    Returns
    -------
    handles : list
        Matplotlib legend handles.

    labels : list
        Legend labels corresponding to the handles.
    """

    def make_handle(**kwargs):
        kwargs.setdefault("ls", "none")
        return pp.plot([], [], **kwargs)[0]

    common_kwargs = {
        k: v
        for k, v in color_spec.items()
        if k not in {"labels", "colors"}
    }

    color_entries = [
        {
            "label": label,
            "color": color,
            **common_kwargs,
        }
        for label, color in zip(color_spec["labels"], color_spec["colors"])
    ]

    legend_entries = color_entries + style_specs

    handles = [
        make_handle(**{k: v for k, v in entry.items() if k != "label"})
        for entry in legend_entries
    ]
    labels = [entry["label"] for entry in legend_entries]

    return handles, labels


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


def plot_with_external_style_legend(plot_data, styles,
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