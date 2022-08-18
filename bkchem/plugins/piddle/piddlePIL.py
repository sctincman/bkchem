# piddlePIL.py -- a Python Imaging Library backend for PIDDLE
# Copyright (C) 1999  Joseph J. Strout
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""piddlePIL

This module implements a Python Imaging Library PIDDLE canvas.
In other words, this is a PIDDLE backend that renders into a
PIL Image object.  From there, you can save as GIF, plot into
another PIDDLE canvas, etc.

Joe Strout (joe@strout.net), 10/26/99
"""

###  6/22/99: updated drawString to handle non-integer x and y

import Image
import string

import os, sys

from .piddle import *

Log =  sys.stderr

if __name__ == '__main__':
    _fontprefix = os.path.join(os.curdir,'pilfonts')
else:
    _fontprefix = os.path.join(os.path.split(__file__)[0],'pilfonts')

# load font metrics
try:
    import cPickle
    with open(os.path.join(_fontprefix,'metrics.dat'), 'rb') as f:
        _widthmaps = cPickle.load(f)
        _ascents   = cPickle.load(f)
        _descents  = cPickle.load(f)
except:
    Log.write("Warning: unable to load font metrics!\n")
    _widthmaps = {}
    _ascents = {}
    _descents = {}
#finally:
#   pass    # (just here so we can comment out the except clause for debugging)

def _closestSize(size):
    supported = [8,10,12,14,18,24]      # list of supported sizes
    if size in supported: return size
    best = supported[0]
    bestdist = abs(size-best)
    for trial in supported[1:]:
        dist = abs(size - trial)
        if dist < bestdist:
            best = trial
            bestdist = dist
    return best

def _pilFontPath(face,size,bold=0):
    if face == 'monospaced': face = 'courier'
    elif face == 'serif': face = 'times'
    elif face == 'sansserif' or face == 'system': face = 'helvetica'

    if bold and face != 'symbol': fname = "%s-bold-%d.pil" % (face,size)
    else: fname = "%s-%d.pil" % (face,size)
    path = os.path.join(_fontprefix,fname)
    return path

def _matchingFontPath(font):
    # returns a font path which matches info in our font metrics
    if font.face: face = font.face
    else: face = 'times'

    size = _closestSize(font.size)
    if type(face) == StringType:
        path = _pilFontPath(face,size,font.bold)
        path = string.split(path,os.sep)[-1]
        if path in _widthmaps.keys(): return path
    else:
        for item in font.face:
            path = _pilFontPath(item,size,font.bold)
            path = string.split(path,os.sep)[-1]
            if path in _widthmaps.keys(): return path
    # not found?  Try it with courier, which should always be there
    path = _pilFontPath('courier',size,font.bold)
    return string.split(path,os.sep)[-1]

def _pilFont(font):
    import ImageFont
    if font.face: face = font.face
    else: face = 'times'

    size = _closestSize(font.size)
    if type(face) == StringType:
        try:
            pilfont = ImageFont.load_path(_pilFontPath(face,size,font.bold))
        except:
            return 0        # font not found!
    else:
        for item in font.face:
            pilfont = None
            try:
                pilfont = ImageFont.load_path(_pilFontPath(item,size,font.bold))
                break
            except: pass
        if pilfont == None: return 0    # font not found!
    return pilfont


class PILCanvas( Canvas ):

    def __init__(self, size=(300,300), name='piddlePIL'):
        self._image = Image.new('RGB',size, (255,255,255))
        import ImageDraw
        self._pen = ImageDraw.ImageDraw(self._image)
        self._pen.setink(0)
        self._setFont( Font() )
        self._pilversion = map(string.atoi, string.split(Image.VERSION, "."))
        Canvas.__init__(self, size, name)

    def __setattr__(self, attribute, value):
        self.__dict__[attribute] = value
        if attribute == "defaultLineColor":
            self._setColor(self.defaultLineColor)

    # utility functions
    def _setColor(self,c):
        "Set the pen color from a piddle color."
        self._pen.setink( (c.red*255, c.green*255, c.blue*255) )

    def _setFont(self,font):
        self._pen.setfont( _pilFont(font) )

    # public functions

    def getImage(self):
        return self._image

    def save(self, file=None, format=None):
        """format may be a string specifying a file extension corresponding to
                an image file format. Ex: 'png', 'jpg', 'gif', 'tif' etc."""
        file = file or self.name
        if hasattr(file, 'write'):
            self._image.save(file, format)
            return
                # below here, file is guaranteed to be a string
        if format == None:
            if '.' not in file:
                raise TypeError('no file type given to save()')
            filename = file
        else:
            filename = file + '.' + format
        self._image.save(filename)


        def clear(self) :
                # why is edgeColor yellow ???
                self.drawRect( 0,0,self.size[0],self.size[1], edgeColor=yellow,fillColor=white )
                ### FIXME: need to reset canvas as well to defaults ???


    #------------ string/font info ------------
    def stringWidth(self, s, font=None):
        "Return the logical width of the string if it were drawn \
        in the current font (defaults to self.defaultFont)."

        if not font: font = self.defaultFont
        if not _widthmaps:
            Log.write("warning no _widthmaps available\n")
            return font.size * len(s)

        path = _matchingFontPath(font)
        map = _widthmaps[path]
        out = 0
        for c in s:
            out = out + map[c]
        return out

    def fontAscent(self, font=None):
        "Find the ascent (height above base) of the given font."

        if not font: font = self.defaultFont
        if not _ascents: return font.size

        path = _matchingFontPath(font)
        return _ascents[path]

    def fontDescent(self, font=None):
        "Find the descent (extent below base) of the given font."

        if not font: font = self.defaultFont
        if not _descents: return font.size/2

        path = _matchingFontPath(font)
        return _descents[path]

    #------------- drawing methods --------------
    def drawLine(self, x1,y1, x2,y2, color=None, width=None):
        "Draw a straight line between x1,y1 and x2,y2."
        # set color...
        if color:
            if color == transparent: return
            self._setColor(color)
        elif self.defaultLineColor == transparent: return

        if width: w = width
        else: w = self.defaultLineWidth
        if w > 1:
            # thick lines are not supported by PIL,
            # so we'll have to implement them as polygons
            self._pen.setfill(1)
            hw = int((w-1)/2)
            pts = []
            if (x1<=x2 and y1<=y2):     # line down and to the right
                pts.append( (x1-hw+w,y1-hw) )
                pts.append( (x1-hw,  y1-hw) )
                pts.append( (x1-hw,  y1-hw+w) )

                pts.append( (x2-hw,  y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw) )

            elif (x1<=x2):              # line up and to the right
                pts.append( (x1-hw,  y1-hw) )
                pts.append( (x1-hw,  y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw+w) )

                pts.append( (x2-hw+w,y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw) )
                pts.append( (x2-hw,  y2-hw) )

            elif (y1<=y2):              # line down and to the left
                pts.append( (x1-hw+w,y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw) )
                pts.append( (x1-hw,  y1-hw) )

                pts.append( (x2-hw,  y2-hw) )
                pts.append( (x2-hw,  y2-hw+w) )
                pts.append( (x2-hw+w,y2-hw+w) )

            else:                       # line up and to the left
                pts.append( (x1-hw,  y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw+w) )
                pts.append( (x1-hw+w,y1-hw) )

                pts.append( (x2-hw+w,y2-hw) )
                pts.append( (x2-hw,  y2-hw) )
                pts.append( (x2-hw,  y2-hw+w) )

            self._pen.polygon(pts)

        else:
            # for width <= 1, just use fast line method
            # This switch is not good.Must be updated when PIL
            # changes it version. Argh.
            if self._pilversion[0] < 1.0:
                self._pen.line(x1,y1,x2,y2)  # pre 1.0 no tuple
            else:
                self._pen.line( (x1,y1,x2,y2) )


    def drawPolygon(self, pointlist,
                edgeColor=None, edgeWidth=None, fillColor=None, closed=0):
        """drawPolygon(pointlist) -- draws a polygon
        pointlist: a list of (x,y) tuples defining vertices
        """
        # PIL's routine requires a sequence of tuples...
        # the input is not so restricted, so fix it
        pts = list(pointlist)
        for i in range(len(pts)):
            pts[i] = tuple(pts[i])

        # set color for fill...
        filling = 0
        if fillColor:
            if fillColor != transparent:
                self._setColor(fillColor)
                filling = 1
        elif self.defaultFillColor != transparent:
            self._setColor(self.defaultFillColor)
            filling = 1

        # do the fill
        if filling:
            self._pen.setfill(1)
            self._pen.polygon(pts)
        self._pen.setfill(0)

        # set color for edge...
        if edgeColor:
            self._setColor(edgeColor)
        else:
            self._setColor(self.defaultLineColor)

        if edgeColor != transparent:
            # set edge width...
            if edgeWidth == None: edgeWidth = self.defaultLineWidth

            # draw the outline

            if (closed or (pts[0][0]==pts[-1][0] and pts[0][1]==pts[-1][1])) \
                     and edgeWidth <= 1:
                self._pen.polygon(pts)
            else:
                # ...since PIL's polygon routine insists on closing,
                # and does not support thick edges, we'll use our drawLine instead
                # OFI: use default color/width to speed this up!
                oldp = pts[0]
                if closed: pts.append(oldp)
                for p in pts[1:]:
                    self.drawLine(oldp[0],oldp[1], p[0],p[1], edgeColor, edgeWidth)
                    oldp = p

    def drawString(self, s, x,y, font=None, color=None, angle=0):
        "Draw a string starting at location x,y."
        if '\n' in s or '\r' in s:
            self.drawMultiLineString(s, x,y, font, color, angle)
            return
        if not font: font = self.defaultFont

        if not color:
            color = self.defaultLineColor
        if color == transparent: return

        # draw into an offscreen Image
        # tmpsize was originally 1.2* stringWidth, added code to give enough room for single character strings (piddle bug#121995)
        sHeight = (self.fontAscent(font) + self.fontDescent(font))
        sWidth = self.stringWidth(s, font)
        tempsize = max(sWidth*1.2, sHeight*2.0)

        tempimg = Image.new('RGB',(tempsize,tempsize), (0,0,0))
        import ImageDraw
        temppen = ImageDraw.ImageDraw(tempimg)
        temppen.setink( (255,255,255) )
        pilfont = _pilFont(font)
        if not pilfont: raise Exception("bad font!", font)
        temppen.setfont( pilfont )
        pos = [4, int(tempsize/2 - self.fontAscent(font)) - self.fontDescent(font)]
        temppen.text( pos, s )
        pos[1] = int(tempsize/2)

        # underline
        if font.underline:
            ydown = (0.5 * self.fontDescent(font) )
            # thickness = 0.08 * font.size # may need to ceil this
            temppen.line([(pos[0], pos[1]+ydown), (pos[0]+sWidth,pos[1]+ydown)])

        # rotate
        if angle:
            from math import pi, sin, cos
            tempimg = tempimg.rotate( angle, Image.BILINEAR )
            temppen = ImageDraw.ImageDraw(tempimg)
            radians = -angle * pi/180.0
            r = tempsize/2 - pos[0]
            pos[0] = int(tempsize/2 - r * cos(radians))
            pos[1] = int(pos[1] - r * sin(radians))

        ### temppen.rectangle( (pos[0],pos[1],pos[0]+2,pos[1]+2) ) # PATCH for debugging
        # colorize, and copy it in
        mask = tempimg.convert('L').point(lambda c:c)
        temppen.setink( (color.red*255, color.green*255, color.blue*255) )
        temppen.setfill(1)
        temppen.rectangle( (0,0,tempsize,tempsize) )
        self._image.paste( tempimg, (int(x)-pos[0],int(y)-pos[1]), mask )



    def drawImage(self, image, x1,y1, x2=None,y2=None):
        """Draw a PIL Image into the specified rectangle.  If x2 and y2 are
        omitted, they are calculated from the image size."""

        if x2 and y2:
            bbox = image.getbbox()
            if x2-x1 != bbox[2]-bbox[0] or y2-y1 != bbox[3]-bbox[1]:
                image = image.resize( (x2-x1,y2-y1) )
        self._image.paste( image, (x1,y1) )

def test():
#... for testing...
    canvas = PILCanvas()

    canvas.defaultLineColor = Color(0.7,0.7,1.0)    # light blue
    canvas.drawLines( map(lambda i:(i*10,0,i*10,300), range(30)) )
    canvas.drawLines( map(lambda i:(0,i*10,300,i*10), range(30)) )
    canvas.defaultLineColor = black

    canvas.drawLine(10,200, 20,190, color=red)

    canvas.drawEllipse( 130,30, 200,100, fillColor=yellow, edgeWidth=4 )

    canvas.drawArc( 130,30, 200,100, 45,50, fillColor=blue, edgeColor=navy, edgeWidth=4 )

    canvas.defaultLineWidth = 4
    canvas.drawRoundRect( 30,30, 100,100, fillColor=blue, edgeColor=maroon )
    canvas.drawCurve( 20,20, 100,50, 50,100, 160,160 )

    canvas.drawString("This is a test!", 30,130, Font(face="times",size=16,bold=1),
            color=green, angle=-45)

    canvas.drawString("This is a test!", 30,130, color=red, angle=-45)

    polypoints = [ (160,120), (130,190), (210,145), (110,145), (190,190) ]
    canvas.drawPolygon(polypoints, fillColor=lime, edgeColor=red, edgeWidth=3, closed=1)

    canvas.drawRect( 200,200,260,260, edgeColor=yellow, edgeWidth=5 )
    canvas.drawLine( 200,260,260,260, color=green, width=5 )
    canvas.drawLine( 260,200,260,260, color=red, width=5 )

    # now, for testing, save the image as a PNG file
    canvas.flush()
    canvas.getImage().save("test.png")


    return canvas

def testit(canvas, s, x,y, font=None):
    canvas.defaultLineColor = black
    canvas.drawString(s, x,y, font=font)
    canvas.defaultLineColor = blue
    w = canvas.stringWidth(s, font=font)
    canvas.drawLine(x,y, x+w,y)
    canvas.drawLine(x,y-canvas.fontAscent(font=font), x+w,y-canvas.fontAscent(font=font))
    canvas.drawLine(x,y+canvas.fontDescent(font=font), x+w,y+canvas.fontDescent(font=font))

def test2():

    canvas = PILCanvas()
    testit( canvas, "Foogar", 20, 30 )

    testit( canvas, "Foogar", 20, 90, font=Font(size=24) )
    global dammit
    dammit = _pilFont(Font(size=24))

    testit( canvas, "Foogar", 20, 150, font=Font(face='courier',size=24) )

    testit( canvas, "Foogar", 20, 240, font=Font(face='courier') )


    from . import piddleQD
    global qdcanvas
    try:
        qdcanvas.close()
    except: pass
    qdcanvas = piddleQD.QDCanvas()
    qdcanvas.drawImage( canvas.getImage(), 0, 0 );


if __name__ == '__main__': test()

