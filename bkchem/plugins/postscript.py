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
#
#
#
#--------------------------------------------------------------------------

"""PostScript Export plugin"""

import plugin

class PS_exporter( plugin.exporter):

  def __init__( self, paper):
    #plugin.exporter.__init__( self, paper)
    self.paper = paper

  def on_begin( self):
    return 1

  def write_to_file( self, name):
    self.paper.unselect_all()
    width = self.paper.get_paper_property( 'size_x')
    height = self.paper.get_paper_property( 'size_y')
    self.paper.postscript( file=name, rotate=0, height='%dm'%height, width='%dm'%width, x=0, y=0)


name = "Encapsulated PostScript"
extensions = ['.eps']
exporter = PS_exporter
