#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002, 2003 Beda Kosata <beda@zirael.org>

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
#
# Last edited: $Date: 2003/09/26 10:47:02 $
#
#--------------------------------------------------------------------------

"""this module provides extended methods for formating of text items (for canvas)
ftext is XML based. Tags used for formating are:
sub - (sub)script, sup - (sup)erscript, b - bold, i - italic"""

import tkFont
import dom_extensions
import xml.dom.minidom as dom
import time
import profile

class ftext:
  def __init__( self, canvas, xy = (), text=None, dom=None, font=None, pos="center-first", fill='#000'):
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
      weight = ''
      x, y = self.__current_x, self.y
      canvas = self.canvas
      if 'b' in a:
        weight = "bold"
      if 'i' in a:
        weight += " italic"
      if not weight:
        weight = "normal"
      if 's' in a:
        item = canvas.create_text( x, y, tags=self.tags, text=element.nodeValue,
                                   font=(self._font_family, int( round( self._font_size*0.7)), weight),
                                   anchor="nw", justify="right", fill=self.fill)
      elif 'S' in a:
        item = canvas.create_text( x, y, tags=self.tags, text=element.nodeValue,
                                   font=(self._font_family, int( round( self._font_size*0.7)), weight),
                                   anchor="sw", justify="right", fill=self.fill)
      else:
        item = canvas.create_text( x, y, tags=self.tags, text=element.nodeValue,
                                   font=(self._font_family, self._font_size, weight), anchor="w", justify="right",
                                   fill=self.fill)
      self.items.append( item)
      self.__current_x = canvas.bbox( item)[2]
    
  def bbox( self):
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

      

## TEST PROGRAM

## from Tkinter import *

## def main():
##   root = Tk()
##   root.title('pokus')
##   frame = Frame( root, width=450, height=600, bd=1)
##   frame.pack( fill = X)
##   canvas = Canvas( frame, width=450, height=600)
##   canvas.pack( fill=BOTH)

##   t1 = time.clock()
##   fnt = tkFont.Font( family="Helvetica", size=5)
##   ff = ftext( canvas, xy = (50, 3), text="<ftext>Nazdar<sup>23</sup> vole: a<sup>2</sup>+b<sup>2</sup>=c<sub>A</sub><sup>2</sup></ftext>", font=fnt)
##   for i in range( 29, 30):
##     ff.y += i+3
##     ff.font.configure( size=i)
##     ff.draw()
##   print time.clock()-t1

##   root.mainloop()

## main()
#profile.run('main()')
## text="<ftext>Nazdar<sup>23</sup> vole: a<sup>2</sup>+b<sup>2</sup>=c<sub>A</sub><sup>2</sup></ftext>"
## a = dom.parseString( text)
## b = ftext_dom_to_fstrings_list( a)
## for i in b:
##   print i, i.get_attrs()
## print "ok"
