
import math

import matplotlib.pyplot as plt
from matplotlib import lines
from matplotlib.patheffects import withStroke

# Globals
BLUE = "#076fa2"
RED = "#E3120B"
BLACK = "#202020"
GREY = "#a2a2a2"


def _bar(data,
         title=None,
         nticks=5,
         fig_width=4,
         fontsize=8,
         max_data=None):
    
    # The positions for the bars
    # This allows us to determine exactly where each bar is located
    y = [i * 0.9 for i in range(len(data))]
    
    header_height = 0.65
    fig_height = len(data) / 3 + header_height
    figsize = (fig_width, fig_height)
    fig, ax = plt.subplots(figsize=figsize)
    
    if max_data is None:
        max_data = max(data.values())
    
    pad = max_data * 0.02
    tick = math.ceil(max_data / nticks)
    limit = (max_data // tick) + 1
    
    xlim = (0, tick * limit)
    ylim = (-0.1, len(data) * 0.9 - 0.2)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    bar_height = 0.6
    bars = ax.barh(y,
                   data.values(),
                   height=bar_height,
                   align="edge",
                   color=BLUE)
    
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bar_pixels = [bar.get_window_extent(r).width for bar in bars]
    
    ax.xaxis.set_ticks([i * tick for i in range(0, limit)])
    ax.xaxis.set_ticklabels([i * tick for i in range(0, limit)],
                            size=8,
                            fontfamily="DejaVu Sans",
                            fontweight="bold")
    ax.xaxis.set_tick_params(labelbottom=False, labeltop=True, length=0)
    
    # Set whether axis ticks and gridlines are above or below most artists.
    ax.set_axisbelow(True)
    ax.grid(axis = "x", color="#A8BAC4", lw=1.2)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_lw(1.5)
    ax.spines["left"].set_capstyle("butt")
    
    # Hide y labels
    ax.yaxis.set_visible(False)
    
    text_pixels = _get_text_pixels(figsize, xlim, ylim, data, y, pad)
    
    for name, count, y_pos, bar_pix, text_pix in zip(data.keys(),
                                                     data.values(),
                                                     y,
                                                     bar_pixels,
                                                     text_pixels):
        
        x = 0
        color = "white"
        path_effects = None
        
        if text_pix > 0.95 * bar_pix:
            x = count
            color = BLUE
            path_effects=[withStroke(linewidth=6, foreground="white")]
        
        ax.text(x + pad,
                y_pos + bar_height / 2,
                name,
                color=color,
                fontfamily="DejaVu Sans",
                fontsize=fontsize,
                va="center",
                path_effects=path_effects)
    
    top = 1 - (header_height / fig_height)
    if title is None: top = 0.85
    
    fig.subplots_adjust(left=0.005, right=1, top=top, bottom=0.1)
    
    # Add title
    if title is not None:
        fig.text(0,
                 1 - (header_height / fig_height / 6),
                 title, 
                 fontsize=math.ceil(1.25 * fontsize),
                 fontweight="bold",
                 fontfamily="DejaVu Sans",
                 va="top")
    
    # Add line and rectangle on top.
    fig.add_artist(lines.Line2D([0, 0.95],
                                [1, 1],
                                lw=3,
                                color=RED,
                                solid_capstyle="butt"))
    
    # Set facecolor, useful when saving as .png
    fig.set_facecolor("white")
    
    return fig, ax


def _get_text_pixels(figsize, xlim, ylim, data, y, pad):
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    pix = ax.transData.transform([(0, 0), (pad, 0)])
    pad_pix = pix[1, 0] - pix[0, 0]
    r = fig.canvas.get_renderer()
    
    result = []
    
    for name, y_pos in zip(data.keys(), y):
        t = ax.text(0,
                    y_pos + 0.5 / 2,
                    name,
                    fontfamily="DejaVu Sans",
                    fontsize=8,
                    va="center")
        bb = t.get_window_extent(renderer=r)
        result.append(bb.width + pad_pix)
    
    return result
