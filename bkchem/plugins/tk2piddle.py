#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2004  Beda Kosata <beda@zirael.org>

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


import piddlePDF
import piddle
import tkFont


class tk2piddle:

  def __init__( self):
    pass


  def export_to_piddle_canvas( self, tk_canvas, piddle_canvas):
    self.canvas = piddle_canvas
    self.paper = tk_canvas
    self.convert = self.paper_to_canvas_coord
    self.draw_document()
    self.canvas.flush()

  def paper_to_canvas_color( self, color):
    if not color:
      return piddle.transparent
    colors = self.paper.winfo_rgb( color)
    return piddle.Color( *map( lambda x: x/65535.0, colors))


  def paper_to_canvas_coord( self, x):
    dpi = self.paper.winfo_fpixels( '254m')/10.0
    return 72*x/dpi


  def draw_document( self):
    # the conversion function for coordinates
    for item in self.paper.find_all():
      method = "_draw_" + self.paper.type( item)
      if not method in self.__class__.__dict__:
        print "method to draw %s is not implemented" % self.paper.type( item)
      else:
        self.__class__.__dict__[ method]( self, item)



  def _draw_line( self, item):
    if self.paper.itemcget( item, 'fill') != '':
      coords = map( self.convert, self.paper.coords( item))
      if len( coords) > 4:
        # polyline
        outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
        fill = piddle.transparent
        width = self.convert( float( self.paper.itemcget( item, 'width')))
        i = 0
        cs = []
        for c in coords:
          if i == 0:
            x = c
            i = 1
          else:
            cs.append( (x, c))
            i = 0
        self.canvas.drawPolygon( cs, edgeColor=outline, edgeWidth=width, fillColor=fill, closed=0)
      else:
        # simple line
        fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
        width = self.convert( float( self.paper.itemcget( item, 'width')))
        x1, y1, x2, y2 = coords
        self.canvas.drawLine( x1, y1, x2, y2, color=fill, width=width)
    else:
      pass #transparent things


  def _draw_text( self, item):
    text = self.paper.itemcget( item, 'text')
    #x, y = map( self.convert, self.paper.coords( item))
    x1, y1, x2, y2 = map( self.convert, self.paper.bbox( item))
    afont = tkFont.Font( font=self.paper.itemcget( item, 'font'))
    conf = afont.config()
    font_family = conf['family']
    font_size = conf[ 'size']
    italic = 'italic' in conf['slant']
    bold = 'bold' in conf['weight']
    y = max(y1,y2)- self.convert( afont.metrics()['descent'])
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    font = piddle.Font( face=font_family, size=font_size, bold=bold, italic=italic)
    self.canvas.drawString( text, x1+self.convert(2), y, font=font, color=fill)  # +2 is a hack


  def _draw_rectangle( self, item):
    coords = map( self.convert, self.paper.coords( item))
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = coords
    self.canvas.drawRect( x1, y1, x2, y2, edgeColor=outline, edgeWidth=width, fillColor=fill)
    
    
  def _draw_polygon( self, item):
    coords = map( self.convert, self.paper.coords( item))
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    i = 0
    cs = []
    for c in coords:
      if i == 0:
        x = c
        i = 1
      else:
        cs.append( (x, c))
        i = 0
    self.canvas.drawPolygon( cs, edgeColor=outline, edgeWidth=width, fillColor=fill, closed=1)
    

  def _draw_oval( self, item):
    coords = map( self.convert, self.paper.coords( item))
    outline = self.paper_to_canvas_color( self.paper.itemcget( item, 'outline'))
    fill = self.paper_to_canvas_color( self.paper.itemcget( item, 'fill'))
    width = self.convert( float( self.paper.itemcget( item, 'width')))
    x1, y1, x2, y2 = coords
    self.canvas.drawEllipse( x1, y1, x2, y2, edgeColor=outline, edgeWidth=width, fillColor=fill)
    


