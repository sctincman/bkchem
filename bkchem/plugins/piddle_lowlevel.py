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


import plugin
from tk2piddle import tk2piddle
import transform



class piddle_exporter( plugin.exporter):

  def __init__( self, paper):
    self.paper = paper


  def init_canvas( self, pagesize=None):
    pass



  def on_begin( self):
    self.paper.unselect_all()
    scale = 720.0/self.paper.winfo_fpixels( '254m')
    if self.paper.get_paper_property( 'crop_svg'):
      margin = self.paper.get_paper_property('crop_margin')
      items = list( self.paper.find_all())
      items.remove( self.paper.background)
      x1, y1, x2, y2 = self.paper.list_bbox( items)
      self.transformer = transform.transform()
      self.transformer.set_move( -x1+margin, -y1+margin)
      self.transformer.set_scaling( scale)
      dx = x2-x1 +2*margin
      dy = y2-y1 +2*margin
    else:
      self.transformer = transform.transform()
      self.transformer.set_scaling( scale)
      dx = self.paper.mm_to_px( self.paper._paper_properties['size_x'])
      dy = self.paper.mm_to_px( self.paper._paper_properties['size_y'])

    self.canvas = self.init_canvas( pagesize=(scale*dx, scale*dy))
    self.converter = tk2piddle()
    return 1

  def write_to_file( self, name):
    self.converter.export_to_piddle_canvas( self.paper, self.canvas, transformer=self.transformer)
    self.canvas.save( name)

