#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002-2007 Beda Kosata <beda@zirael.org>

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

"""the arrow class resides here"""

from __future__ import division
from __future__ import generators

from classes import point
from warnings import warn
import dom_extensions
import xml.dom.minidom as dom
import operator
from parents import meta_enabled, container, with_line, line_colored
from parents import point_drawable, interactive, drawable, top_level
from reaction import reaction
from singleton_store import Screen

import debug

##-------------------- ARROW CLASS ------------------------------

class arrow( meta_enabled, drawable, with_line, line_colored, container, interactive, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  _pins = ['none', 'last', 'first', 'both']
  object_type = 'arrow'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color']
  # other meta infos
  meta__is_container = 1
  # undo related metas
  meta__undo_simple = ('pin', 'spline')
  meta__undo_properties = with_line.meta__undo_properties + \
                          line_colored.meta__undo_properties
  meta__undo_copy = ('points',)
  meta__undo_children_to_record = ('points',)



  def __init__( self, paper, type="normal", points=[], shape=(8,10,3), pin=1, spline=0, package=None, fill="#000"):
    meta_enabled.__init__( self, standard=paper.standard)
    drawable.__init__( self)
    with_line.__init__( self)
    line_colored.__init__( self)

    self.paper = paper

    self.type = type
    self.points = []
    self.spline = spline
    self.paper = paper
    self.shape = shape
    self.item = None
    self.items = []
    self.pin = 1
    if points:
      for p in points:
        pnt = point( self.paper, xy=p, arrow=self)
        self.points.append( pnt)
    self.reaction = reaction()
    self.reaction.arrows.append( self)
    if package:
      self.read_package( package)


  # just a hack
  def _get_item(self):
    debug.log( "calling GET item", levels=[2])
    return self.items[0]

  def _set_item(self,i):
    debug.log( "calling SET item", levels=[2])
    self.items = [i]

  item = property( _get_item, _set_item)

  # PROPERTIES

  # shape_defining_points
  def _get_shape_defining_points( self):
    return self.points

  shape_defining_points = property( _get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")


  def _get_reaction( self):
    return self.__reaction

  def _set_reaction( self, reaction):
    self.__reaction = reaction

  reaction = property( _get_reaction, _set_reaction, None, "the reaction associated with this arrow")


  # // PROPERTIES


  def read_standard_values( self, standard, old_standard=None):
    meta_enabled.read_standard_values( self, standard, old_standard=old_standard)
    if not old_standard or (standard.line_width != old_standard.line_width):
      self.line_width = Screen.any_to_px( standard.line_width)    
    


  def draw( self):
    if len( self.points) > 1:
      #type = self.spline and 'circle' or 'invisible'
      type = 'invisible'
      for p in self.points:
        p.type = type
      [pnt.draw() for pnt in self.points]
      # here we call a private draw method corresponding to the current type
      self.items = getattr(self,'_draw_'+self.type)()
      [self.paper.register_id( i, self) for i in self.items]
    
  def redraw( self):
    if self.items:
      map( self.paper.unregister_id, self.items)
      map( self.paper.delete, self.items)
    self.draw()

  def focus( self):
    [self.paper.itemconfig( i, width=self.line_width+2) for i in self.items]

  def unfocus( self):
    [self.paper.itemconfig( i, width=self.line_width) for i in self.items]

#  def get_id( self):
#    return self.id

  def select( self):
    #self.selector = hg.selection_rect( self.paper, self, coords=self.bbox())
    [pnt.select() for pnt in self.points]

  def unselect( self):
    #self.selector.delete()
    [pnt.unselect() for pnt in self.points]

  def create_new_point( self, x, y, position=-1):
    "creates new point, position specifies relative position of point in points, usualy -1 or 0"
    pnt = point( self.paper, xy=(x,y), arrow=self)
    if position < 0:
      self.points.append( pnt)
    else:
      try:
        self.points.insert( position, pnt)
      except IndexError:
        self.points.append( pnt)
        warn( "bad position for adding point in arrow", UserWarning, 2)
    return pnt

  def delete_point( self, pnt):
    try:
      self.points.remove( pnt)
    except IndexError:
      warn( "trying to remove nonexisting point from arrow")
    pnt.delete()

  def delete( self):
    [p.delete() for p in self.points]
    self.points = []
    map( self.paper.unregister_id, self.items)
    map( self.paper.delete, self.items)
    self.items = []

  def is_empty_or_single_point( self):
    return len( self.points) < 2 

  def move( self, dx, dy):
    [p.move( dx, dy) for p in self.points]
    self.redraw()

  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    if package.getAttribute( 'id'):
      self.id = package.getAttribute( 'id')
    a = ['no', 'yes']
    self.type = package.getAttribute( 'type') or 'normal'
    start = a.index( package.getAttribute( 'start'))
    end = a.index( package.getAttribute( 'end'))
    if start and end:
      self.pin = 3
    elif start:
      self.pin = 2
    elif end:
      self.pin = 1
    else:
      self.pin = 0
    self.spline = a.index( package.getAttribute( 'spline'))
    self.line_width = float( package.getAttribute( 'width'))
    #self.shape = package.getAttribute( 'shape')
    self.line_color = package.getAttribute( 'color')
    for p in package.getElementsByTagName( 'point'):
      self.points.append( point( self.paper, arrow=self, package=p))
  
  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    a = ['no', 'yes']
    arr = doc.createElement('arrow')
    arr.setAttribute( 'id', self.id)
    start, end = 0, 0
    if self.pin == 2 or self.pin == 3:
      start = 1
    if self.pin == 1 or self.pin ==3:
      end = 1
    dom_extensions.setAttributes( arr, (('shape', str( self.shape)),
                                       ('spline', a[self.spline]),
                                        ('width', str( self.line_width)),
                                        ('start', a[start]),
                                        ('end', a[end]),
                                        ('color', str( self.line_color)),
                                        ('type', self.type)))
    for p in self.points:
      arr.appendChild( p.get_package( doc))
    return arr

  def change_direction( self):
    self.pin += 1
    if self.pin > 3:
      self.pin = 0
    self.redraw()

  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.paper.list_bbox( self.items)

  def set_pins( self, start=None, end=None):
    st, en = self.get_pins()      
    if start != None:
      st = start
    if end != None:
      en = end
    self.pin = en + 2*st

  def get_pins( self):
    """returns tuple of boolean values (start, end)"""
    return divmod( self.pin, 2)

  def lift( self):
    if self.items:
      map( self.paper.lift, self.items)
    [o.lift() for o in self.points]


  # -- private drawing methods for different arrow types --
  
  def _draw_normal( self):
    ps = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
    item = self.paper.create_line( ps, tags='arrow', arrow=self._pins[ self.pin], arrowshape=self.shape,\
                                   width=self.line_width, smooth=self.spline, fill=self.line_color)
    return [item]
  

