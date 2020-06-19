from functools import partial
from typing import Dict, Tuple, Sequence
import math

def multiplyColor(colorTuple, multiplier):
    multiplier = multiplier
    return tuple(a * multiplier // 255 for a in colorTuple)

alphacolor = (0, 0, 0, 0)

# Last updated for Minecraft 1.12.
basecolors = [
    alphacolor,
    (127, 178,  56),
    (247, 233, 163),
    (199, 199, 199),
    (255,   0,   0),
    (160, 160, 255),
    (167, 167, 167),
    (  0, 124,   0),
    (255, 255, 255), 
    (164, 168, 184),
    (151, 109,  77),
    (112, 112, 112),
    ( 64,  64, 255),
    (143, 119,  72),
    (255, 252, 245),
    (216, 127,  51),
    (178,  76, 216), 
    (102, 153, 216), 
    (229, 229,  51),
    (127, 204,  25),
    (242, 127, 165), 
    ( 76,  76,  76), 
    (153, 153, 153),
    ( 76, 127, 153),
    (127,  63, 178), 
    ( 51,  76, 178),
    (102,  76,  51), 
    (102, 127,  51),
    (153,  51,  51), 
    ( 25,  25,  25), 
    (250, 238,  77), 
    ( 92, 219, 213),
    ( 74, 128, 255), 
    (  0, 217,  58), 
    (129,  86,  49), 
    (112,   2,   0),
    (209, 177, 161), 
    (159,  82,  36), 
    (149,  87, 108),
    (112, 108, 138),
    (186, 133,  36),
    (103, 117,  53),
    (160,  77,  78),
    ( 57,  41,  35),
    (135, 107,  98),
    ( 87,  92,  92),
    (122,  73,  88),
    ( 76,  62,  92),
    ( 76,  50,  35), 
    ( 76,  82,  42),
    (142,  60,  46),
    ( 37,  22,  16)]

allcolors = [
    multiplyColor(color, multiplier)
    for color in basecolors for multiplier in multipliers
]

allcolorsinversemap = {color: index for index, color in enumerate(allcolors)}

# Key: interval (integer); Value: three-dimension array for approximate MC color codes
estimationlookup = {}
# Key: color (tuple); Value: three-dimension array for approximate MC color codes
estimationlookupdict = {}

def addestimate(n, todict=False):
    '''adds genestimation(n) to estimationlookup or estimationlookupdict at index n'''
    if todict:
        global estimationlookup
        estimationlookup[n] = genestimation(n)
    else:
        global estimationlookupdict
        estimationlookupdict[n] = genestimationdict(n)


def genestimation(n):
    '''returns a nested list by estimating approximate() on interval n in every axis'''
    rl = []
    for rn in range(n + 1):
        gl = []
        for gn in range(n + 1):
            bl = []
            for bn in range(n + 1):
                r = (rn + .5) * 255 / n
                g = (gn + .5) * 255 / n
                b = (bn + .5) * 255 / n
                i = approximate((r, g, b))
                bl.append(i)
            gl.append(bl)
        rl.append(gl)
    return rl


def genestimationdict(n):
    '''returns a dict with indexes (r,g,b) by estimating approximate() on interval n in every axis'''
    lookup = {}
    for rn in range(n + 1):
        for gn in range(n + 1):
            for bn in range(n + 1):
                r = (rn + .5) * 255 / n
                g = (gn + .5) * 255 / n
                b = (bn + .5) * 255 / n
                i = approximate((r, g, b))
                lookup[(rn, gn, bn)] = i
    return lookup


def colordifference(testcolor, comparecolor):
    '''returns rgb distance squared'''
    d = ((testcolor[0] - comparecolor[0])**2 +
         (testcolor[1] - comparecolor[1])**2 +
         (testcolor[2] - comparecolor[2])**2)
    return d


def approximate(color):
    '''returns best minecraft color code from rgb'''
    try:
        return allcolorsinversemap[color]
    except KeyError:
        color = min(allcolors, key=partial(colordifference, color))
        return allcolorsinversemap[color]

addestimate(10)
