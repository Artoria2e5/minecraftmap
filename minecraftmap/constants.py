#!/usr/bin/env python3
"""
All the color approximation logic go here.
"""
from functools import partial, reduce
from itertools import chain
from typing import List, Dict, Tuple, Union, Set, Iterable, NewType
import math
import copy

Color = Tuple[int, int, int]
ColorID = NewType('ColorID', int)
Interval = NewType('Interval', int)
ColorMap = Dict[Color, ColorID]
# TypedDict is not enough. Oof.
ColorMapWithInterval = Dict[Union[Color, str], Union[ColorID, Set[Interval]]]
ColorLUT = Dict[Interval, List[List[List[ColorID]]]]

def multiplyColor(colorTuple: Color, multiplier: int) -> Color:
    multiplier = multiplier
    return tuple(a * multiplier // 255 for a in colorTuple)

# https://stackoverflow.com/a/6800214
def _factors(n: int) -> Set[int]:
    return set(reduce(list.__add__,
                ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0)))

def colordifference(testcolor, comparecolor) -> int:
    '''returns euclidean rgb distance squared'''
    d = ((testcolor[0] - comparecolor[0])**2 +
         (testcolor[1] - comparecolor[1])**2 +
         (testcolor[2] - comparecolor[2])**2)
    return d

def _crange(*args) -> Iterable[int]:
    """Same as range, but always returns 255 at the end."""
    return chain(range(*args), (255,))

def _round_interval(n: Interval, val: int) -> int:
    """
    Round to the nearest interval of n. Or to 255, because that's how _crange works.
    """
    if 255 - val < n:
        return 255
    return int(val / n + 0.5) * n

def _round_index(n: Interval, val: int) -> int:
    """
    Like _round_interval, but returns an index for nth value.
    """
    if 255 - val < n:
        # Py3 says ceil is int. Great.
        return math.ceil(255 / n)
    return int(val / n + 0.5)

# This can be changed. If you don't want to use alphacolor at all,
# pass in something ridiculous like (-256, -256, -256).
# TODO: Make it not black. An empty map is yellow-ish, not black.
alphacolor: Color = (0, 0, 0)

# Last updated for Minecraft 1.12.
basecolors: List[Color] = [
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

class estimators():
    def __init__(new_alphacolor):
        global basecolors
        self.basecolors: List[Color] = basecolors.copy()
        self.basecolors[0] = new_alphacolor
        self.allcolors: List[Color] = [
            multiplyColor(color, multiplier)
            for color in basecolors for multiplier in multipliers
        ]
        self.allcolorsinversemap: ColorMap = {color: index for index, color in enumerate(allcolors)}
        # Key: interval (integer); Value: three-dimension array for approximate MC color codes
        self.estimationlookup: ColorLUT = {}
        # Key: color (tuple); Value: MC color codes
        # Special key: 'intervals'; Value: set of available intervals.
        self.estimationlookupdict: ColorMapWithInterval = {'intervals': set(1)}

    def addestimate(self, n: Interval, todict=False) -> bool:
        '''Add estimate for interval n, if it's not already there. Returns whether any update was done.'''
        if self.has_interval(n, usedict=todict):
            return False
        if todict:
            self.estimationlookup[n] = self.genestimation(n, invmap)
        else:
            self.estimationlookupdict.update(genestimationdict(n, invmap))
            self.estimationlookupdict['intervals'].add(n)
        return True

    def has_interval(self, n: Interval, usedict=False) -> bool:
        """Do we have this interval of information?"""
        assert n > 1
        if usedict:
            return n in self.estimationlookup
        else:
            factors = _factors(n)
            # With the dict we can accomondate many levels of precision.
            # Precision level 5 and 2 naturally serves precision level 10.
            return any(f in self.estimationlookupdict['intervals'] for f in factors)

    def _genestimation(self, n: Interval) -> ColorMap:
        '''returns a nested list by estimating approximate() on interval n in every axis'''
        rl = []
        for rn in _crange(0, 256, n):
            gl = []
            for gn in _crange(0, 256, n):
                bl = []
                for bn in _crange(0, 256, n):
                    i = self.approximate((r, g, b), interval=1)
                    bl.append(i)
                gl.append(bl)
            rl.append(gl)
        return rl

    def _genestimationdict(self, n: Interval) -> ColorLUT:
        '''returns a dict with indexes (r,g,b) by estimating approximate() on interval n in every axis'''
        lookup = {}
        for rn in _crange(0, 256, n):
            for gn in _crange(0, 256, n):
                for bn in _crange(0, 256, n):
                    i = self.approximate((r, g, b), interval=1)
                    lookup[(r, g, b)] = i
        return lookup

    def approximate(color: Color, usedict=False, interval=10) -> ColorID:
        '''
        Return a minecraft color code for the color given.
        Interval sets the sample grid size for the approximate maps used.
        Setting it to 1 forces exact calculation of closest color.
        '''
        if color in self.allcolorsinversemap:
            return self.allcolorsinversemap[color]
        elif color in self.estimationlookupdict[color]:
            return self.estimationlookupdict[color]
        elif interval > 1:
            # Use the gridded solutions.
            self.addestimate(interval, usedict)
            if self.usedict:
                # Round color to nearest lookupdict-sized blocks.
                return self.estimationlookupdict[tuple(_round_interval(interval, v) for v in color)]
            else:
                return self.estimationlookupdict[tuple(_round_index(interval, v) for v in color)]
        else:
            # Seriously approximate.
            color = min(allcolors, key=partial(colordifference, color))
            self.estimationlookupdict[color] = self.allcolorsinversemap[color]
            return self.estimationlookupdict[color]


estimators = {
    alphacolor: estimators(alphacolor)
}

def getestimator(new_alphacolor):
    if new_alphacolor not in estimators:
        estimators[new_alphacolor] = estimators(new_alphacolor)
    return estimators[new_alphacolor]
