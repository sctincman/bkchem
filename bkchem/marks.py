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

"""set of marks such as charges, radicals etc."""

from __future__ import division
import geometry
import xml.dom.minidom as dom
import dom_extensions
import warnings
from parents import simple_parent

class mark( simple_parent):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'mark'
  standard_size = 4
  # undo related metas
  meta__undo_simple = ('x', 'y', 'auto')

  def __init__( self, paper, x, y, atom=None, size=4, auto=1):
    """size is a diameter of the mark"""
    self.paper = paper
    self.x = x
    self.y = y
    self.atom = atom
    self.size = size
    self.items = []
    self.auto = auto
    #self.draw()

  def draw( self):
    pass

  def delete( self):
    [self.paper.delete( o) for o in self.items]
    self.items = []

  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    [self.paper.move( o, dx, dy) for o in self.items]

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy)

  def lift( self):
    [self.paper.lift( i) for i in self.items]

  def redraw( self):
    self.delete()
    self.draw()

  def get_svg_element( self, doc):
    pass

  def transform( self, tr):
    # do only move, the direction-using marks would need to override it and make real transform
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y)


class radical( mark):

  def draw( self):
    """outline color is used for both outline and fill for radical"""
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s,
                                          fill=self.atom.line_color, outline=self.atom.line_color,
                                          tags='mark')]

  def get_svg_element( self, doc):
    e = doc.createElement( 'ellipse')
    dom_extensions.setAttributes( e,
                                 (( 'cx', str( self.x)),
                                  ( 'cy', str( self.y)),
                                  ( 'rx', str( self.size /2)),
                                  ( 'ry', str( self.size /2)),
                                  ( 'fill', self.atom.line_color),
                                  ( 'stroke', self.atom.line_color),
                                  ( 'stroke-width', '1')))
    return e



class biradical( mark):

  def move( self, dx, dy):
    """marks that have a direction and not only position should be redrawn on move"""
    self.x += dx
    self.y += dy
    self.redraw()

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    s = round( self.size / 2)
    x1, y1, x2, y2 = self.x, self.y, self.atom.x, self.atom.y
    x, y = geometry.find_parallel( x1, y1, x2, y2, s*1.5)[0:2]
    # one circle
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s,
                                          fill=self.atom.line_color, outline=self.atom.line_color,
                                          tags='mark')]
    # and the second on the other side
    x, y = geometry.find_parallel( x1, y1, x2, y2, -s*1.5)[0:2]
    self.items.append( self.paper.create_oval( x-s, y-s, x+s, y+s,
                                               fill=self.atom.line_color, outline=self.atom.line_color,
                                               tags='mark'))
    

  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    for i in self.items:
      x1, y1, x2, y2 = self.paper.coords( i)
      x = (x1 + x2)/2
      y = (y1 + y2)/2
      dom_extensions.elementUnder( e, 'ellipse',
                                   (( 'cx', str( x)),
                                    ( 'cy', str( y)),
                                    ( 'rx', str( self.size /2)),
                                    ( 'ry', str( self.size /2)),
                                    ( 'fill', self.atom.line_color),
                                    ( 'stroke', self.atom.line_color),
                                    ( 'stroke-width', '1')))
    return e


  def transform( self, tr):
    self.x, self.y = tr.transform_xy( self.x, self.y)
    for i in self.items:
      coords = self.paper.coords( i)
      if self.paper.type( i) == 'oval':
        x, y = (coords[0]+coords[2])/2.0, (coords[1]+coords[3])/2.0
        d = abs(coords[2]-coords[0])/2.0
        x, y = tr.transform_xy( x, y)
        tr_coords = [x-d, y-d, x+d, y+d]
      else:
        tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))



class electronpair( mark):

  def __init__( self, paper, x, y, atom=None, size=10, auto=1):
    mark.__init__( self, paper, x, y, atom=atom, size=size, auto=auto)

  def move( self, dx, dy):
    """marks that have a direction and not only position should be redrawn on move"""
    self.x += dx
    self.y += dy
    self.redraw()

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    s = round( self.size / 2)
    x1, y1, x2, y2 = self.x, self.y, self.atom.x, self.atom.y
    # one end
    x, y = geometry.find_parallel( x1, y1, x2, y2, s)[0:2]
    # and the other
    x0, y0 = geometry.find_parallel( x1, y1, x2, y2, -s)[0:2]
    self.items = [self.paper.create_line( x, y, x0, y0, fill=self.atom.line_color,
                                          width=round(s/2), tags='mark')]
    

  def get_svg_element( self, doc):
    e = doc.createElement( 'line')
    x1, y1, x2, y2 = self.paper.coords( self.items[0])
    dom_extensions.setAttributes( e,
                                 (( 'x1', str( x1)),
                                  ( 'y1', str( y1)),
                                  ( 'x2', str( x2)),
                                  ( 'y2', str( y2)),
                                  ( 'stroke-width', str( round( round( self.size /2)/2))),
                                  ( 'fill', self.atom.line_color),
                                  ( 'stroke', self.atom.line_color)))
    return e

  def transform( self, tr):
    self.x, self.y = tr.transform_xy( self.x, self.y)
    for i in self.items:
      coords = self.paper.coords( i)
      tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))


class plus( mark):

  standard_size = 10

  def __init__( self, paper, x, y, atom=None, size=10, auto=1):
    mark.__init__( self, paper, x, y, atom=atom, size=size, auto=auto)

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s, fill='',
                                          outline=self.atom.line_color, tags='mark')]
    self.items.append( self.paper.create_line( x-s+2, y, x+s-2, y,
                                               fill=self.atom.line_color, tags='mark'))
    self.items.append( self.paper.create_line( x, y-s+2, x, y+s-2,
                                               fill=self.atom.line_color, tags='mark'))


  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    x, y = self.x, self.y
    s = round( self.size / 2)
    dom_extensions.elementUnder( e, 'ellipse',
                                 (( 'cx', str( x)),
                                  ( 'cy', str( y)),
                                  ( 'rx', str( s)),
                                  ( 'ry', str( s)),
                                  ( 'fill', 'none'),
                                  ( 'stroke', self.atom.line_color),
                                  ( 'stroke-width', '1')))
    for x1, y1, x2, y2 in [(x-s+2, y, x+s-2, y), (x, y-s+2, x, y+s-2)]:
      dom_extensions.elementUnder( e, 'line',
                                    (( 'x1', str( x1)),
                                     ( 'y1', str( y1)),
                                     ( 'x2', str( x2)),
                                     ( 'y2', str( y2)),
                                     ( 'stroke-width', '1'),
                                     ( 'fill', self.atom.line_color),
                                     ( 'stroke', self.atom.line_color)))

    return e




class minus( mark):

  standard_size = 10

  def __init__( self, paper, x, y, atom=None, size=10, auto=1):
    mark.__init__( self, paper, x, y, atom=atom, size=size, auto=auto)

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s, fill='',
                                          outline=self.atom.line_color, tags='mark')]
    self.items.append( self.paper.create_line( x-s+2, y, x+s-2, y,
                                               fill=self.atom.line_color, tags='mark'))


  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    x, y = self.x, self.y
    s = round( self.size / 2)
    dom_extensions.elementUnder( e, 'ellipse',
                                 (( 'cx', str( x)),
                                  ( 'cy', str( y)),
                                  ( 'rx', str( s)),
                                  ( 'ry', str( s)),
                                  ( 'fill', 'none'),
                                  ( 'stroke', self.atom.line_color),
                                  ( 'stroke-width', '1')))
    for x1, y1, x2, y2 in [(x-s+2, y, x+s-2, y)]:
      dom_extensions.elementUnder( e, 'line',
                                    (( 'x1', str( x1)),
                                     ( 'y1', str( y1)),
                                     ( 'x2', str( x2)),
                                     ( 'y2', str( y2)),
                                     ( 'stroke-width', '1'),
                                     ( 'fill', self.atom.line_color),
                                     ( 'stroke', self.atom.line_color)))

    return e


