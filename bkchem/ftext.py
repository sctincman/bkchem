#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002-2004 Beda Kosata <beda@zirael.org>

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program

#--------------------------------------------------------------------------


"""this module provides extended methods for formating of text items (for canvas)
ftext is XML based. Tags used for formating are:
sub - (sub)script, sup - (sup)erscript, b - bold, i - italic"""

import tkFont
import dom_extensions
import xml.sax
import copy
from sets import Set
import tuning



class ftext:


  def __init__( self, canvas, xy, text, font=None, pos="center-first", fill='#000', big_charges=True):
    self.big_charges = big_charges  # should +- in <sup> be drawn in bigger font (not scaled down)?
    self.canvas = canvas
    self.items = []
    self.tags = ('ftext'),
    if xy:
      self.x, self.y = xy
    if text:
      self.text = str(text)
    if font:
      self.font = font
    else:
      self.font = tkFont.Font( family="Helvetica", size=12)
    self._font_family = self.font.actual('family')
    self._font_size = int( self.font.actual('size'))
    self.pos = pos
    self.fill = fill


    
  def draw( self):
    chs = self.get_chunks()
    if not chs:
      return None

    self.items = []
    self._current_x = self.x

    self.items = chs
    last_attrs = Set()
    last_x = self._current_x
    
    for ch in self.items:
      scale = 1
      if Set(('sub','sup')) & ch.attrs:
        if not (ch.text in "-" and self.big_charges):
          scale = 0.7
        else:
          scale = 1
        # we ignore subscripts and superscript in bbox calculation
        ch.ignore_y = True
        ch.ignore_x = True
        if Set(('sub','sup')) & last_attrs:
          self._current_x = last_x
      last_x = self._current_x
      last_attrs = ch.attrs
      self._draw_chunk( ch, scale=scale)

    #does not work when 1. character is not regular
    if self.pos == 'center-first':
      self.diff = self.font.measure( self.items[0].text[0])/2.0
    elif self.pos == 'center-last':
      x1, y1, x2, y2 = self.bbox()
      self.diff = x2 -x1 -self.font.measure( self.items[0].text[-1])/2.0 -2
    self.move( -self.diff, 0)
    return self.bbox()





  def _draw_chunk( self, chunk, scale=1):
    weight = ''
    canvas = self.canvas
    x = self._current_x
    y = self.y

    if 'b' in chunk.attrs:
      weight = "bold"
    if 'i' in chunk.attrs:
      weight += " italic"
    if not weight:
      weight = "normal"

    if 'sub' in chunk.attrs:
      item = canvas.create_text( x+tuning.Tuning.ftext_supsubscript_x_shift,
                                 y+tuning.Tuning.ftext_subscript_y_shift,
                                 tags=self.tags, text=chunk.text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="nw", justify="right", fill=self.fill)
    elif 'sup' in chunk.attrs:
      item = canvas.create_text( x, y, tags=self.tags, text=chunk.text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="sw", justify="right", fill=self.fill)
    else:
      item = canvas.create_text( x, y, tags=self.tags, text=chunk.text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="w",
                                 justify="right",
                                 fill=self.fill)
    bbox = canvas.bbox( item)
    chunk.item = item
    chunk.dx = abs( bbox[0] - bbox[2])
    self._current_x = bbox[2]



  def get_chunks( self):
    handler = FtextHandler()
    xml.sax.parseString( self.text, handler)
    return handler.chunks


    
  def bbox( self, complete=False):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    xbbox = list( self.canvas.list_bbox( [i.item for i in self.items if complete or not i.ignore_x]))
    ybbox = list( self.canvas.list_bbox( [i.item for i in self.items if complete or not i.ignore_y]))
    bbox = [xbbox[0], ybbox[1], xbbox[2], ybbox[3]]
##     for i in self.items:
##       if i.ignore_y:
##         x1, y1, x2, y2 = self.canvas.bbox( i.item)
##         if not i.ignore_x:
##           bbox[0] = min( (bbox[0], x1))
##           bbox[2] = max( (bbox[2], x2))
##         if y1 < bbox[1]:
##           bbox[1] -= 2 # hack
    return bbox
          


  def move( self, dx, dy):
    for i in self.items:
      self.canvas.move( i.item, dx, dy)

  def move_to( self, x, y):
    dx = self.x - x - self.diff
    dy = self.y - y
    for i in self.items:
      self.canvas.move( i.item, dx, dy)

  def lift( self):
    for i in self.items:
      self.canvas.lift( i.item)

  def delete( self):
    for i in self.items:
      self.canvas.delete( i.item)

      


class text_chunk:

  def __init__( self, text, attrs=None):
    self.text = text
    self.attrs = attrs or Set()
    self.item = None
    self.dx = 0
    self.ignore_y = False
    self.ignore_x = False


class FtextHandler ( xml.sax.ContentHandler):

  def __init__( self):
    xml.sax.ContentHandler.__init__( self)
    self._above = []
    self.chunks = []

  def startElement( self, name, attrs):
    self._above.append( name)


  def endElement( self, name):
    self._above.pop( -1)


  def characters( self, data):
    self.chunks.append( text_chunk( data, attrs = Set( self._above)))




