from functools import partial, reduce
from itertools import chain
import math

def multiplyColor(colorTuple, multiplier):
    multiplier = multiplier
    return tuple(a * multiplier // 255 for a in colorTuple)

# https://stackoverflow.com/a/6800214
def _factors(n):
    return set(reduce(list.__add__,
                ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0)))

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
# Key: color (tuple); Value: MC color codes
# Special key: 'intervals'; Value: set of available intervals.
estimationlookupdict = {'intervals': set()}
# Key: color (tuple); Value: MC color codes
# Cached results of approximate().
colorcache = {}

def addestimate(n, todict=False):
    '''adds genestimation(n) to estimationlookup or estimationlookupdict at index n'''
    if todict:
        global estimationlookup
        estimationlookup[n] = genestimation(n)
    else:
        global estimationlookupdict
        estimationlookupdict.update(genestimationdict(n))
        estimationlookupdict['intervals'].add(n)

def hasInterval(n, todict=False):
    """Do we have this interval of information?"""
    assert n > 1
    if todict:
        global estimationlookup
        return n in estimationlookup
    else:
        global estimationlookupdict
        factors = _factors(n)
        # With the dict we can accomondate many levels of precision.
        # Precision level 5 and 2 naturally serves precision level 10.
        return any(f in estimationlookupdict['intervals'] for f in factors)

def _crange(*args):
    """Same as args, but always returns 255 at the end."""
    return chain(range(*args), (255,))

def genestimation(n):
    '''returns a nested list by estimating approximate() on interval n in every axis'''
    rl = []
    for rn in _crange(0, 256, n):
        gl = []
        for gn in _crange(0, 256, n):
            bl = []
            for bn in _crange(0, 256, n):
                i = approximate((r, g, b))
                bl.append(i)
            gl.append(bl)
        rl.append(gl)
    return rl


def genestimationdict(n):
    '''returns a dict with indexes (r,g,b) by estimating approximate() on interval n in every axis'''
    lookup = {}
    for rn in _crange(0, 256, n):
        for gn in _crange(0, 256, n):
            for bn in _crange(0, 256, n):
                i = approximate((r, g, b))
                lookup[(r, g, b)] = i
    return lookup


def colordifference(testcolor, comparecolor):
    '''returns euclidean rgb distance squared'''
    d = ((testcolor[0] - comparecolor[0])**2 +
         (testcolor[1] - comparecolor[1])**2 +
         (testcolor[2] - comparecolor[2])**2)
    return d


# DO NOT CACHE THIS ONE UNLESS YOU CHECK THE INVMAP!
# Better to handle cache in __init__.py.
def approximate(color, invmap=allcolorsinversemap):
    '''returns best minecraft color code from rgb'''
    try:
        return invmap[color]
    except KeyError:
        color = min(allcolors, key=partial(colordifference, color))
        return invmap[color]

