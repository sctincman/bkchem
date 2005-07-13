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


from cairo_lowlevel import cairo_exporter
from tk2cairo import tk2cairo
import cairo


class png_cairo_exporter( cairo_exporter):

  def __init__( self, paper):
    cairo_exporter.__init__( self, paper, converter_class=tk2cairo)
    

  def init_surface( self):
    w, h = map( int, map( round, self.pagesize))
    surface = cairo.ImageSurface( cairo.FORMAT_ARGB32, w, h)
    return surface


  def init_context( self):
    """to be overriden; should be called after init_surface"""
    context = cairo.Context( self.surface)
    context.set_source_rgb( 1, 1, 1)
    context.rectangle( 0, 0, self.pagesize[0], self.pagesize[1])
    context.fill()
    return context


  def save( self):
    self.surface.write_to_png( self.filename)
    self.surface.finish()



# PLUGIN INTERFACE SPECIFICATION
name = "PNG (Cairo)"
extensions = [".png"]
exporter = png_cairo_exporter
