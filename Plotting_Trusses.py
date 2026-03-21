#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 19:42:31 2022

@author: kendrickshepherd
"""

import matplotlib
from matplotlib import pyplot as plt
from matplotlib import markers
from matplotlib.path import Path

import sys
import numpy as np
import math

def PlotStructure(nodes,bars,marker_size = 100):
    for bar in bars:
        near_node_coord = bar.init_node.location
        far_node_coord = bar.end_node.location
        plt.plot([near_node_coord[0],far_node_coord[0]],
                 [near_node_coord[1],far_node_coord[1]],
                 "k-")
    xlocs=[]
    ylocs=[]
    for node in nodes:
        loc = node.location
        plt.scatter(loc[0], loc[1], marker='o', s=marker_size, color="black")
        if len(node.ConstraintType())==2:
            plt.scatter(loc[0],loc[1], marker=6, s=6*marker_size, color="red")
        elif 1 in node.ConstraintType():
            plt.scatter(loc[0],loc[1], marker=align_marker("o",valign="top"), s=12*marker_size, color="red")
        elif 0 in node.ConstraintType():
            plt.scatter(loc[0],loc[1], marker=align_marker("o",halign="right"), s=12*marker_size, color="red")
        xlocs.append(loc[0])
        ylocs.append(loc[1])
        
        
    maxx = max(xlocs)
    minx = min(xlocs)
    maxy = max(ylocs)
    miny = min(ylocs)
    xdiff = maxx-minx
    ydiff = maxy-miny
    plt.gcf().set_size_inches(xdiff, ydiff,forward=True)
    plt.axis('equal')
    
    return [xdiff,ydiff]

def ComputeBarMidLoc(bar):
    near_node_coord = bar.init_node.location
    far_node_coord = bar.end_node.location
    midloc = [(far_node_coord[0] + near_node_coord[0])/2,
              (far_node_coord[1] + near_node_coord[1])/2]
    return midloc

def ComputeBarDir(bar):
    near_node_coord = bar.init_node.location
    far_node_coord = bar.end_node.location
    bar_dir = np.array([far_node_coord[0]-near_node_coord[0],
               far_node_coord[1]-near_node_coord[1]])
    return bar_dir

def SineBar(bar):
    bar_dir = ComputeBarDir(bar)
    sin = np.cross([1,0],bar_dir)/np.linalg.norm(bar_dir)
    return sin

def ASineBar(bar):
    return math.asin(SineBar(bar))    

def CosineBar(bar):
    bar_dir = ComputeBarDir(bar)
    cos = np.dot([1,0],bar_dir)/np.linalg.norm(bar_dir)
    return cos

def ACosineBar(bar):
    return math.acos(CosineBar(bar))   

def GetRotationAngle(bar):
    cos = CosineBar(bar)
    sin = SineBar(bar)
    if cos < 0:
        if sin < 0:
            quad = 3
        else:
            quad = 2
    else:
        if sin < 0:
            quad = 4
        else:
            quad = 1
    if quad == 1 or quad == 4:
        return ASineBar(bar)
    elif quad == 2:
        return ACosineBar(bar) + math.pi
    else:
        return -ASineBar(bar)
    
        


def ComputeBarOrthogonal(bar):
    bar_dir = ComputeBarDir(bar)
    ortho = np.array([bar_dir[1],-bar_dir[0]])
    if ortho[1] < 0:
        ortho = np.array([-ortho[0],-ortho[1]])
    ortho = ortho/np.linalg.norm(ortho)
    return ortho

def PlotStructureData(nodes,bars,plot_type):
    plt.figure(figsize=(8, 6), dpi=200)
    if plot_type=="index":

        [xdiff,ydiff]=PlotStructure(nodes,bars)
        for bar in bars:
            midloc = ComputeBarMidLoc(bar)
            label = "b{:d}".format(bar.idx)
            offset_array = xdiff/2*ComputeBarOrthogonal(bar)
            offset = (offset_array[0],offset_array[1])
            rotate = GetRotationAngle(bar)*180/math.pi
            plt.annotate(label, # this is the text
                 (midloc[0],midloc[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center', # horizontal alignment can be left, right or center
                 rotation=rotate,
                 size=xdiff)
        for node in nodes:
            label = "n{:d}".format(node.idx)
            offset = (0,7)
            plt.annotate(label, # this is the text
                 (node.location[0],node.location[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center',
                 size=xdiff) # horizontal alignment can be left, right or center

    elif plot_type=="axial":
        [xdiff,ydiff]=PlotStructure(nodes,bars)
        for bar in bars:
            midloc = ComputeBarMidLoc(bar)
            label = "{:.3f} (T)".format(bar.axial_load) if bar.axial_load > 0 else "{:.3f} (C)".format(-bar.axial_load)
            offset_array = xdiff/2*ComputeBarOrthogonal(bar)
            offset = (offset_array[0],offset_array[1])
            rotate = GetRotationAngle(bar)*180/math.pi
            plt.annotate(label, # this is the text
                 (midloc[0],midloc[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center', # horizontal alignment can be left, right or center
                 rotation=rotate,
                 size=xdiff)
            
    elif plot_type=="stress":
        [xdiff,ydiff]=PlotStructure(nodes,bars)
        for bar in bars:
            midloc = ComputeBarMidLoc(bar)
            label = "{:.3f} (T)".format(bar.normal_stress) if bar.normal_stress > 0 else "{:.3f} (C)".format(-bar.normal_stress)
            offset_array = xdiff/2*ComputeBarOrthogonal(bar)
            offset = (offset_array[0],offset_array[1])
            rotate = GetRotationAngle(bar)*180/math.pi
            plt.annotate(label, # this is the text
                 (midloc[0],midloc[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center', # horizontal alignment can be left, right or center
                 rotation=rotate,
                 size=xdiff)


    elif plot_type=="buckling":
        [xdiff,ydiff]=PlotStructure(nodes,bars)
        for bar in bars:
            midloc = ComputeBarMidLoc(bar)
            label = "{:.3f} (C)".format(bar.buckling_load)
            offset_array = xdiff/2*ComputeBarOrthogonal(bar)
            offset = (offset_array[0],offset_array[1])
            rotate = GetRotationAngle(bar)*180/math.pi
            plt.annotate(label, # this is the text
                 (midloc[0],midloc[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center', # horizontal alignment can be left, right or center
                 rotation=rotate,
                 size=xdiff)


    elif "disp" in plot_type:
        if "in" in plot_type:
            multiplier = 12
        elif "ft" in plot_type:
            multiplier = 1
        else:
            sys.exit("Error in units specified for plotting displacements")
        [xdiff,ydiff]=PlotStructure(nodes,bars)
        for node in nodes:
            midloc = node.location
            label = "({:.3f},{:.3f})".format(node.xdisp*multiplier,node.ydisp*multiplier)
            offset_array = 7*np.array([0.2,1])
            offset = (offset_array[0],offset_array[1])
            plt.annotate(label, # this is the text
                 (midloc[0],midloc[1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=offset, # distance from text to points (x,y)
                 ha='center',
                 size=xdiff)

    plt.box(False)
    plt.autoscale(enable=True, axis='y', tight=True)
    plt.axis("off")
    plt.gca().set_aspect('equal')
    plt.show()


def align_marker(marker, halign='center', valign='middle',):
    """
    create markers with specified alignment.

    Parameters
    ----------

    marker : a valid marker specification.
      See mpl.markers

    halign : string, float {'left', 'center', 'right'}
      Specifies the horizontal alignment of the marker. *float* values
      specify the alignment in units of the markersize/2 (0 is 'center',
      -1 is 'right', 1 is 'left').

    valign : string, float {'top', 'middle', 'bottom'}
      Specifies the vertical alignment of the marker. *float* values
      specify the alignment in units of the markersize/2 (0 is 'middle',
      -1 is 'top', 1 is 'bottom').

    Returns
    -------

    marker_array : numpy.ndarray
      A Nx2 array that specifies the marker path relative to the
      plot target point at (0, 0).

    Notes
    -----
    The mark_array can be passed directly to ax.plot and ax.scatter, e.g.::

        ax.plot(1, 1, marker=align_marker('>', 'left'))

    """

    if isinstance(halign, str):
        halign = {'right': -1.,
                  'middle': 0.,
                  'center': 0.,
                  'left': 1.,
                  }[halign]

    if isinstance(valign, str):
        valign = {'top': -1.,
                  'middle': 0.,
                  'center': 0.,
                  'bottom': 1.,
                  }[valign]

    # Define the base marker
    bm = markers.MarkerStyle(marker)

    # Get the marker path and apply the marker transform to get the
    # actual marker vertices (they should all be in a unit-square
    # centered at (0, 0))
    m_arr = bm.get_path().transformed(bm.get_transform()).vertices

    # Shift the marker vertices for the specified alignment.
    m_arr[:, 0] += halign / 2
    m_arr[:, 1] += valign / 2

    return Path(m_arr, bm.get_path().codes)