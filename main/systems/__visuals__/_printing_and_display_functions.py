from IPython.core.display import display, HTML

level2colors = {
    1 : "red",
    2 : "orange",
    3 : "yellow",
    4 : "lightgreen",
    5 : "cyan"
}

def header(level: int, text: str, *args, **kwargs):
    color = level2colors[level]
    display(
        HTML(f'<h{level} style="color:{color}">{text}</h{level}>'), *args, **kwargs
    )

