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
import xml.dom.minidom as dom


class ftext:


  def __init__( self, canvas, xy = (), text=None, dom=None, font=None, pos="center-first", fill='#000', big_charges=True):
    self.big_charges = big_charges  # should +- in <sup> be drawn in bigger font (not scaled down)?
    self.canvas = canvas
    self.items = []
    self.tags = ('ftext'),
    if xy:
      self.x, self.y = xy
    if text:
      #self.text = text
      self.doc = dom.parseString( text)
    if dom:
      self.doc = dom
      #self.text = self.dom.toxml()
    if font:
      self.font = font
    else:
      self.font = tkFont.Font( family="Helvetica", size=12)
    self._font_family = self.font.actual('family')
    self._font_size = int( self.font.actual('size'))
    self.pos = pos
    self.fill = fill


    
  def draw( self):
    plain_text = dom_extensions.getAllTextFromElement( self.doc)
    if not plain_text:
      return None
    self.items = []
    self.__current_x = self.x
    self.__draw_elements( self.doc)
    self._last_attrs = ''
    self._last_x = self.x
    #does not work when 1. character is not regular
    if self.pos == 'center-first':
      self.diff = self.font.measure( plain_text[0])/2.0
    elif self.pos == 'center-last':
      x1, y1, x2, y2 = self.bbox()
      self.diff = x2 -x1 -self.font.measure( plain_text[-1])/2.0 -2
    self.move( -self.diff, 0)
    return self.bbox()



  def __draw_elements( self, element, attrs=''):
    i = []
    a = attrs
    if not element.nodeValue:
      name = element.nodeName
      if name == 'b':
        a += 'b'
      elif name == 'i':
        a += 'i'
      elif name == 'sub':
        a += 's'
      elif name == 'sup':
        a += 'S'
      for el in element.childNodes:
        self.__draw_elements( el, attrs=a)
    else:
      scale = 1
      if 's' in attrs or 'S' in attrs:
        if not (element.nodeValue == "-" and self.big_charges):
          scale = 0.7
        if 's' in self._last_attrs or 'S' in self._last_attrs:
          self.__current_x = self._last_x

      self._draw_text( element.nodeValue, attrs, scale=scale)




  def _draw_text( self, text, attributes, scale=1):
    weight = ''
    canvas = self.canvas
    x = self.__current_x
    y = self.y

    if 'b' in attributes:
      weight = "bold"
    if 'i' in attributes:
      weight += " italic"
    if not weight:
      weight = "normal"


    if 's' in attributes:
      item = canvas.create_text( x, y, tags=self.tags, text=text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="nw", justify="right", fill=self.fill)
    elif 'S' in attributes:
      item = canvas.create_text( x, y, tags=self.tags, text=text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="sw", justify="right", fill=self.fill)
    else:
      item = canvas.create_text( x, y, tags=self.tags, text=text,
                                 font=(self._font_family, int( round( self._font_size*scale)), weight),
                                 anchor="w",
                                 justify="right",
                                 fill=self.fill)
    self.items.append( item)
    self._last_attrs = attributes
    self._last_x = self.__current_x
    self.__current_x = canvas.bbox( item)[2]



    
  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.canvas.list_bbox( self.items)

  def move( self, dx, dy):
    for i in self.items:
      self.canvas.move( i, dx, dy)

  def move_to( self, x, y):
    dx = self.x - x - self.diff
    dy = self.y - y
    for i in self.items:
      self.canvas.move( i, dx, dy)

  def lift( self):
    for i in self.items:
      self.canvas.lift( i)

  def delete( self):
    for i in self.items:
      self.canvas.delete( i)

      


