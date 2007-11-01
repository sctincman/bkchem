#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2004-2007  Beda Kosata <beda@zirael.org>

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
# try if there is PSSurface in cairo
_x = cairo.PSSurface


class ps_cairo_exporter( cairo_exporter):
  """Exports PostScript via the Cairo (pycairo) library. This is the preferred PS output plugin
as it supports unicode strings and the output is of very good quality."""

  doc_string = _("Exports Postscript via the Cairo (pycairo) library. This is the preferred PS output plugin as it supports unicode strings and the output is of very good quality.")

  def __init__( self, paper):
    cairo_exporter.__init__( self, paper, converter_class=tk2cairo)
    

  def init_surface( self):
    w, h = map( int, map( round, self.pagesize))
    surf = cairo.PSSurface( self.filename, w, h)
    return surf


  def get_scaling( self, x, y):
    sc = self._get_scaling_ratio()
    return sc, sc

  def _get_scaling_ratio( self):
    from singleton_store import Screen
    return 72.0/Screen.dpi

  def save( self):
    self.surface.finish()
    # here we process the exported PostScript to include PageSize
    import re
    f = file( self.filename, "rb")
    text = f.read()
    f.close()
    f = file( self.filename, "wb")
    for line in text.splitlines():
      f.write( line+"\n")
      m = re.match( "^%%PageBoundingBox: \d+ \d+ (\d+) (\d+)$", line)
      if m:
        f.write( "<</PageSize[%s %s]>>setpagedevice\n" % (m.group(1),m.group(2)))
    f.close()


# PLUGIN INTERFACE SPECIFICATION
name = "PS_Cairo"
extensions = [".eps",".ps"]
exporter = ps_cairo_exporter
local_name = _("Postscript (Cairo)")
