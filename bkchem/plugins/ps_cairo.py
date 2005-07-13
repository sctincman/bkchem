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


class ps_cairo_exporter( cairo_exporter):

  def __init__( self, paper):
    cairo_exporter.__init__( self, paper, converter_class=tk2cairo)
    

  def init_surface( self):
    w, h = self.pagesize
    surface = cairo.PSSurface( self.filename, w, h)
    #surface.set_dpi( 300, 300)
    return surface


  def save( self):
    self.surface.finish()


# PLUGIN INTERFACE SPECIFICATION
name = "PostScript (Cairo)"
extensions = [".eps",".ps"]
exporter = ps_cairo_exporter


## ! DOES NOT WORK YET - IT SEEMS AS THERE IS VERY BAD PIXEL GRAPHICS EMBEDDED INTO THE PS !
