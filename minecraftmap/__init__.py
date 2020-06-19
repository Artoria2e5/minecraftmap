from nbt import nbt
from nbt.nbt import NBTFile, TAG_Long, TAG_Int, TAG_String, TAG_List, TAG_Compound
from PIL import Image,ImageDraw,ImageFont
from os import path
from functools import partial
import math

from . import constants

fontpath = path.join(path.dirname(__file__), "minecraftia", "Minecraftia.ttf")

def unpack_nbt(tag):
    """                                                                                                                                                                              
    Unpack an NBT tag into a native Python data structure.
    """
    if isinstance(tag, TAG_List):
        return [unpack_nbt(i) for i in tag.tags]
    elif isinstance(tag, TAG_Compound):
        return dict((i.name, unpack_nbt(i)) for i in tag.tags)
    else:
        return tag.value

class ColorError(Exception):
    def __init__(self,color):
        self.color = color
        self.msg = "Could not map color to nbt value: "+str(color)
        super(ColorError,self).__init__(self.msg)

class Map():
    font = ImageFont.truetype(fontpath,8)

    def __init__(self, filename=None, eco=False, alphacolor=constants.alphacolor, uselookupdict=True):
        '''
        Map class containing nbt data and a PIL Image object, with read/write functionality.

        Eco means the Image object is not written to upon initialization.
        Alphacolor allows for treating the blank color as some other color (default is black).
        Uselookupdict adjusts some internals and might affect performance somehow.
        '''
        
        if filename:
            self.file = nbt.NBTFile(filename)
        else:
            self.file = self.gendefaultnbt()

        self.alphacolor = alphacolor
        self.uselookupdict = uselookupdict

        self.dimension = self.file["data"]["dimension"].value
        self.height = 128
        self.width = 128
        self.centerxz = (self.file["data"]["xCenter"].value, self.file["data"]["zCenter"].value)
        self.zoomlevel = self.file["data"]["scale"].value
        self.pixelcenterxy = (self.width/2, self.height/2)
        self.scalemultiplier = self.zoomlevel ** 2
        
        try:
            self.banners = unpack_nbt(self.file["data"]["banners"])
        except:
            self.banners = []    
        
        self.im = Image.new("RGBA",(self.width, self.height))
        self.draw = ImageDraw.Draw(self.im)
        
        try:
            self.tag = self.file["data"]["tag"].value
        except:
            self.tag = {}

        self.estimator = constants.getestimator(self.alphacolor)
        if not eco: self.genimage()

        # Expose some stuff for playing with.
        self.allcolorsinversemap = estimator.allcolorsinversemap
        self.allcolors = estimator.allcolors
        self.basecolors = estimator.basecolors

        try:
            self.unlimitedTracking = bool(self.file["data"]["unlimitedTracking"].value)
        except:
            self.unlimitedTracking = False

    def gendefaultnbt(self):
        '''returns an nbt object'''
        nbtfile = nbt.NBTFile()
        colors = nbt.TAG_Byte_Array(name="colors")
        colors.value = bytearray(16384)
        data = nbt.TAG_Compound()
        data.name = "data"
        data.tags = [
            nbt.TAG_Int(value=0, name="zCenter"),
            nbt.TAG_Byte(value=1, name="trackingPosition"),
            nbt.TAG_Short(value=128, name="width"),
            nbt.TAG_Byte(value=1, name="scale"),
            nbt.TAG_Byte(value=0, name="dimension"),
            nbt.TAG_Int(value=64, name="xCenter"),
            colors,
            nbt.TAG_Short(value=128, name="height")
            ]
        nbtfile.tags.append(data)
        return nbtfile

    def genimage(self):
        '''updates self.im'''
        colordata = self.file["data"]["colors"].value
        rgbdata = [self.allcolors[v] for v in colordata]
        self.im.putdata(rgbdata)

    def imagetonbt(self,approximate=True,optimized=True,lookupindex=10):
        '''
        updates self.file to match self.im, approximations work but take very long,
        optimization with constants.estimationlookup[lookupindex] is fast but imperfect

        :param: lookupindex -- precision (interval) for the optimization. Setting to 1
                is the same as no optimization.
        '''
        rgbdata = self.im.getdata()
        try:
            if approximate:
                if not optimize:
                    lookupindex = 1
                colordata = bytearray([self.approximate(c, lookupindex) for c in rgbdata])
            else:
                colordata = bytearray([self.allcolorsinversemap[c] for c in rgbdata])

        except KeyError as e:
            raise ColorError(e.args[0])
        self.file["data"]["colors"].value = colordata
    
    def saveimagebmp(self,filename):
        '''Saves self.im as a bmp'''
        self.im.save(filename)
    
    def saveimagepng(self,filename):
        '''Saves self.im as png'''
        self.im.save(filename,"PNG")
    
    def saveimagejpg(self,filename):
        '''Saves self.im as jpg'''
        self.im.save(filename,"JPEG",quality=100,subsampling=0)
    
    def savenbt(self,filename=None):
        '''Saves nbt data to original file or to specified filename'''
        if filename or self.file.filename:
            self.file.write_file(filename)

    def rescale(self, num=1):
        self.im = self.im.resize((self.height * num * 2 ** self.zoomlevel , self.width * num * 2 ** self.zoomlevel))
    
    
    def getbyte(self,index):
        '''Gets nbt image byte at index, returns None if out of range'''
        return self.file["data"]["colors"].value[index]
    
    def setbyte(self,index,byte):
        '''Sets nbt image byte at index'''
        self.file["data"]["colors"].value[index] = byte
    
    def getpoint(self,xy):
        '''Gets nbt image byte at specific (x,y)'''
        index = xy[0] + xy[1]*self.width
        try: return self.file["data"]["colors"].value[index]
        except IndexError: return None
    
    def setpoint(self,xy,value):
        '''Sets nbt image byte at specific (x,y)'''
        index = xy[0] + xy[1]*self.width
        self.file["data"]["colors"].value[index] = value
    
    def topixel(self,xz):
        '''converts coords to pixels where x:east and z:south'''
        shiftxz = (xz[0]-self.centerxz[0],xz[1]-self.centerxz[1])
        shiftxy = (shiftxz[0],shiftxz[1])
        pixelshiftxy = (shiftxy[0]//self.scalemultiplier, shiftxy[1]//self.scalemultiplier)
        pixelxy = (self.pixelcenterxy[0]+pixelshiftxy[0], self.pixelcenterxy[1]+pixelshiftxy[1])
        return pixelxy
    
    def tocoord(self,xy):
        '''Converts pixels to coords, returns (x,z)'''
        pixelshiftxy = (xy[0]-self.pixelcenterxy[0], xy[1]-self.pixelcenterxy[1])
        blockshiftxy = (pixelshiftxy[0]*self.scalemultiplier, pixelshiftxy[1]*self.scalemultiplier)
        blockshiftxz = (blockshiftxy[0],blockshiftxy[1])
        blockxz = (blockshiftxz[0]+self.centerxz[0],blockshiftxz[1]+self.centerxz[1])
        return blockxz

    def approximate(self,color,lookupindex=10):
        return self.estimator.approximate(color, usedict=self.uselookupdict, interval=lookupindex)
