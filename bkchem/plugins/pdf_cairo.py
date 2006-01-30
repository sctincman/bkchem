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
# try if there is PDFSurface in cairo
_x = cairo.PDFSurface


class pdf_cairo_exporter( cairo_exporter):
  """Exports PDF via the Cairo (pycairo) library. This is the preferred PDF output plugin
as it supports unicode strings and the output is of very good quality."""

  def __init__( self, paper):
    cairo_exporter.__init__( self, paper, converter_class=tk2cairo)
    

  def init_surface( self):
    w, h = self.pagesize
    return cairo.PDFSurface( self.filename, w, h)


  def save( self):
    self.surface.finish()


# PLUGIN INTERFACE SPECIFICATION
name = "PDF (Cairo)"
extensions = [".pdf"]
exporter = pdf_cairo_exporter
