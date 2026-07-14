import matplotlib as mpl
import matplotlib.pyplot as pp

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