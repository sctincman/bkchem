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


"""home of the bond class"""

from __future__ import division

from math import sqrt
import misc
import geometry
from warnings import warn
from ftext import ftext
import dom_extensions
import xml.dom.minidom as dom
import operator
import copy
from parents import meta_enabled, line_colored, drawable, with_line, interactive, child
import debug

import oasa

### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


# class BOND--------------------------------------------------
class bond( meta_enabled, line_colored, drawable, with_line, interactive, child, oasa.bond):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'bond'
  # these values will be automaticaly read from paper.standard on __init__
  # bond_width couldn't be because it has sign that is important
  # widths need to be calculated therefore are also not here (to be fixed)
  meta__used_standard_values = ['line_color','double_length_ratio']
  # undo related metas
  meta__undo_properties = line_colored.meta__undo_properties + \
                          with_line.meta__undo_properties + \
                          ('molecule', 'type', 'order', 'atom1', 'atom2',
                           'center', 'bond_width','double_length_ratio', 'wedge_width',
                           'simple_double','auto_bond_sign')




  def __init__( self, paper, atoms=(), package=None, molecule=None, type='n', order=1,
                simple_double=1):
    # initiation
    oasa.bond.__init__( self, order=order, vs=atoms, type=type)
    meta_enabled.__init__( self, paper)
    line_colored.__init__( self)
    drawable.__init__( self)
    with_line.__init__( self)
    # 
    self.type = type
    self.order = order
    self.item = None
    self.second = []
    self.third = []
    self.items = []
    self.molecule = molecule
    if atoms:
      self.atom1, self.atom2 = atoms
    self.selector = None

    # implicit values
    self.center = 0
    self.auto_bond_sign = 1
    self.simple_double = simple_double
    self.equithick = 1

    if package:
      self.read_package( package)



  ## ------------------------------ PROPERTIES ------------------------------


  # dirty
  # override of drawable.dirty
  def __get_dirty( self):
    return self.__dirty # or self.atom1.dirty or self.atom2.dirty

  def __set_dirty( self, dirty):
    self.__dirty = dirty

  dirty = property( __get_dirty, __set_dirty)


  # molecule
  def __get_molecule( self):
    return self.__molecule

  def __set_molecule( self, mol):
    self.__molecule = mol

  molecule = property( __get_molecule, __set_molecule)


  # type
  def __get_type( self):
    return self.__type

  def __set_type( self, mol):
    self.__type = mol
    self.__dirty = 1

  type = property( __get_type, __set_type)


  # order
  def __get_order( self):
    return self.__order

  def __set_order( self, mol):
    self.__order = mol
    self.__dirty = 1

  order = property( __get_order, __set_order)


  # atom1
  def __get_atom1( self):
    try:
      return self._vertices[0]
    except IndexError:
      return None

  def __set_atom1( self, mol):
    try:
      self._vertices[0] = mol
    except IndexError:
      self._vertices = [mol, None]
    self.__dirty = 1

  atom1 = property( __get_atom1, __set_atom1)


  # atom2
  def __get_atom2( self):
    try:
      return self._vertices[1]
    except IndexError:
      return None

  def __set_atom2( self, mol):
    try:
      self._vertices[1] = mol
    except IndexError:
      self._vertices = [None, mol]
    self.__dirty = 1

  atom2 = property( __get_atom2, __set_atom2)


  # atoms
  def __get_atoms( self):
    return self._vertices

  def __set_atoms( self, mol):
    self._vertices = mol
    self.__dirty = 1

  atoms = property( __get_atoms, __set_atoms)


  # center
  def __get_center( self):
    return self.__center

  def __set_center( self, mol):
    self.__center = mol
    self.__dirty = 1

  center = property( __get_center, __set_center)


  # bond_width
  def __get_bond_width( self):
    return self.__bond_width

  def __set_bond_width( self, mol):
    self.__bond_width = mol
    self.__dirty = 1

  bond_width = property( __get_bond_width, __set_bond_width)


  # wedge_width
  def __get_wedge_width( self):
    return self.__wedge_width

  def __set_wedge_width( self, mol):
    self.__wedge_width = mol
    self.__dirty = 1

  wedge_width = property( __get_wedge_width, __set_wedge_width)


  # simple_double
  def __get_simple_double( self):
    return self.__simple_double

  def __set_simple_double( self, mol):
    self.__simple_double = mol
    self.__dirty = 1

  simple_double = property( __get_simple_double, __set_simple_double)


  # double_length_ratio
  def __get_double_length_ratio( self):
    return self.__double_length_ratio

  def __set_double_length_ratio( self, mol):
    self.__double_length_ratio = mol
    self.__dirty = 1

  double_length_ratio = property( __get_double_length_ratio, __set_double_length_ratio)


  # auto_bond_sign
  def __get_auto_bond_sign( self):
    return self.__auto_bond_sign

  def __set_auto_bond_sign( self, mol):
    self.__auto_bond_sign = mol
    self.__dirty = 1

  auto_bond_sign = property( __get_auto_bond_sign, __set_auto_bond_sign)



  # parent
  def __get_parent( self):
    return self.molecule

  parent = property( __get_parent, None, None,
                     "returns self.molecule")




  ## // ------------------------------ END OF PROPERTIES --------------------





  def read_standard_values( self, old_standard=None):
    meta_enabled.read_standard_values( self, old_standard=old_standard)
    # wedge width
    if not old_standard or (self.paper.standard.wedge_width != old_standard.wedge_width):
      self.wedge_width = self.paper.any_to_px( self.paper.standard.wedge_width)
    # line width
    if not old_standard or (self.paper.standard.line_width != old_standard.line_width):
      self.line_width = self.paper.any_to_px( self.paper.standard.line_width)
    # bond width
    if not old_standard or (self.paper.standard.bond_width != old_standard.bond_width):
      if 'bond_width' in self.__dict__:
        self.bond_width = misc.signum( self.bond_width) * self.paper.any_to_px( self.paper.standard.bond_width)
      else:
        self.bond_width = self.paper.any_to_px( self.paper.standard.bond_width)




  def draw( self, no_automatic=0):
    """call the appropriate draw method, no_automatic is used on file read when no automatic decisions are needed"""
    if self.item:
      warn( "drawing bond that is probably drawn already", UserWarning, 2)
    method = "_draw_%s%d" % (self.type, self.order or 1)
    if not no_automatic and self.order == 2 and self.auto_bond_sign == 1:
      self._decide_distance_and_center()
    self.__class__.__dict__[ method]( self)



  # THE DRAW HELPER METHODS


  # normal bond

  def _draw_n1( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    # main item
    self.item = self.paper.create_line( (x1, y1, x2, y2), tags=('bond',), width=self.line_width, fill=self.line_color, capstyle="round")
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_n2( self):
    x1,y1,x2,y2 = self._draw_n1()
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      self.paper.itemconfig( self.item, fill='')
      # d = int( round( d/3)) #MB#
      d = round(d*.4) #MB#+
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    self.second = [self.paper.create_line( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy, width=self.line_width, fill=self.line_color)]
    if self.center:
      self.third = [self.paper.create_line( 2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0, width=self.line_width, fill=self.line_color)]

  def _draw_n3( self):
    x1,y1,x2,y2 = self._draw_n1()
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    _k = (1-self.double_length_ratio)/2
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    dx = x-x0
    dy = y-y0
    self.second = [self.paper.create_line( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy, width=self.line_width, fill=self.line_color)]
    self.third = [self.paper.create_line( 2*x1-x-_k*dx, 2*y1-y-_k*dy, 2*x2-x0+_k*dx, 2*y2-y0+_k*dy, width=self.line_width, fill=self.line_color)]
    



  def _draw_h1( self):
    x1,y1,x2,y2 = self._draw_n1()    
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    self.items = self._draw_hatch( (x1,y1,x2,y2))
    return x1,y1,x2,y2    

  def _draw_h2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      x1,y1,x2,y2 = self._draw_n1()
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      x1,y1,x2,y2 = self._draw_h1()
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_hatch
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_h3( self):
    x1,y1,x2,y2 = self._draw_h1()
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_hatch
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_hatch( self, coords):
    """returns list items"""
    if not hasattr( self, 'equithick'): 
      self.equithick = 0                
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    xa, ya, xb, yb = geometry.find_parallel( x1, y1, x2, y2, self.line_width/2.0) 
    d = sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    dx1 = (x0 - xa)/d 
    dy1 = (y0 - ya)/d 
    dx2 = (2*x2 -x0 -2*x1 +xa)/d 
    dy2 = (2*y2 -y0 -2*y1 +ya)/d 
    # params for equithick	
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 
    ddx = x - x1 
    ddy = y - y1 

    # we have to decide if the first line should be at the position of the first atom
    draw_start = 0
    if self.atom1.get_occupied_valency() > 1:
      draw_start = 1
    draw_end = 1
    if self.atom2.get_occupied_valency() > 1:
      draw_end = 0
    # now we finally draw
    step_size = 2*(self.line_width+1)
    items = []
    for i in range( draw_start, int( round( d/ step_size)) +draw_end):
      if self.equithick: 
        coords = [x1 + i*step_size*dx + ddx, y1 + i*step_size*dy + ddy, x1 + i*step_size*dx - ddx, y1 + i*step_size*dy - ddy]
        if coords[0] == coords[2] and coords[1] == coords[3]: 
          if (dx1+dx2) > (dy1+dy2):  
            coords[0] += 1 
          else: 
            coords[1] += 1 
      else: # real wedge, not "equithick" 
        coords = [xa+dx1*i*step_size, ya+dy1*i*step_size, 2*x1-xa+dx2*i*step_size, 2*y1-ya+dy2*i*step_size] 
        if coords[0] == coords[2] and coords[1] == coords[3]:
          if (dx1+dx2) > (dy1+dy2): 
            coords[0] += 1
          else:
            coords[1] += 1
      items.append( self.paper.create_line( coords, width=self.line_width, fill=self.line_color))

    return items


  # dashed bond

  def _draw_d1( self):
    x1,y1,x2,y2 = self._draw_n1()    
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    self.items = self._draw_dash( (x1,y1,x2,y2))
    return x1,y1,x2,y2    

  def _draw_d2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      x1,y1,x2,y2 = self._draw_n1()
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      if self.simple_double:
        x1,y1,x2,y2 = self._draw_n1()
      else:
        x1,y1,x2,y2 = self._draw_d1()
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    self.second = self._draw_dash(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    if self.center:
      self.third = self._draw_dash(( 2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_d3( self):
    if self.simple_double:
      x1,y1,x2,y2 = self._draw_n1()
    else:
      x1,y1,x2,y2 = self._draw_d1()
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # we don't want to shorten the bonds (yet)
    _k = (1-self.double_length_ratio)/2
    _k = 0
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    dx = x-x0
    dy = y-y0
    self.second = self._draw_dash(( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy))
    self.third = self._draw_dash(( 2*x1-x-_k*dx, 2*y1-y-_k*dy, 2*x2-x0+_k*dx, 2*y2-y0+_k*dy))


  def _draw_dash( self, coords):
    """returns list items"""
    x1, y1, x2, y2 = coords
    # main item
    dashing = (5, 5) # pixels full, pixels empty
    d = sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    # we adjust the dashing lengths
    _d = dashing[0]
    while not _d > d:
      _d += sum( dashing)
    dashing = map( lambda x: x * d/_d, dashing)
    # //
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 

    # now we finally draw
    items = []
    x = x1
    y = y1
    while min(x1,x2) <= x <= max(x1, x2) and min(y1,y2) <= y <= max(y1,y2):
      xn = x + dx*dashing[0]
      yn = y + dy*dashing[0]
      coords = (x, y, xn, yn)
      items.append( self.paper.create_line( coords, width=self.line_width, fill=self.line_color))
      x = xn + dx*dashing[1]
      y = yn + dy*dashing[1]
    return items





  def _draw_second_line( self, coords):
    x, y, x0, y0 = coords
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    return [self.paper.create_line( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy, width=self.line_width, fill=self.line_color)]


  # wedge bonds

  def _draw_w1( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    #x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    # main item
    # we check if there is a bold bond attached to the wider end of wedge

##     bbonds = [b for b in self.molecule.atoms_bonds( self.atom2) if b.type == 'b']
##     if len( bbonds):
##       # we draw the wedge so that it fits the bold bond
##       b = bbonds[0]
##       xx1, yy1 = self.atom2.x, self.atom2.y
##       aa2 = (b.atom1 == self.atom2) and b.atom2 or b.atom1
##       xx2, yy2 = aa2.x, aa2.y
##       x, y, x0, y0 = geometry.find_parallel( xx1, yy1, xx2, yy2, b.wedge_width/2.0)
##       coords = [self.atom1.x, self.atom1.y, x, y]
##       x, y, x0, y0 = geometry.find_parallel( xx1, yy1, xx2, yy2, -b.wedge_width/2.0)
##       coords.extend( [x,y])
##       self.item = self.paper.create_polygon( tuple( coords), outline=self.line_color, fill=self.line_color, joinstyle="miter")
##     else:

    self.item = self._draw_wedge( (x1,y1,x2,y2))[0]
    self.paper.addtag_withtag( "bond", self.item)
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_w2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      x1,y1,x2,y2 = self._draw_n1()
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      x1,y1,x2,y2 = self._draw_w1()
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_wedge
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))

  def _draw_w3( self):
    x1,y1,x2,y2 = self._draw_w1()
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_wedge
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))
    
    
  def _draw_wedge( self, coords):
    """returns the polygon item"""
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    xa, ya, xb, yb = geometry.find_parallel( x1, y1, x2, y2, self.line_width/2.0) 
    return [self.paper.create_polygon( (xa, ya, x0, y0, 2*x2-x0, 2*y2-y0, 2*x1-xa, 2*y1-ya), width=0, fill=self.line_color, joinstyle="miter")] 


  def _draw_a1( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    #x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    # main item
    self.item = self._draw_adder( (x1,y1,x2,y2))[0]
    self.paper.addtag_withtag( "bond", self.item)
    # draw helper items
    self.second = self.third = []
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_a2( self):
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      x1,y1,x2,y2 = self._draw_n1()
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    else:
      x1,y1,x2,y2 = self._draw_a1()
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_adder
    self.second = _second_draw_method( (x,y,x0,y0))
    if self.center:
      self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))


  def _draw_a3( self):
    x1,y1,x2,y2 = self._draw_a1()
    if self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # gray magic (not black, but not so white :)
    _second_draw_method = (self.simple_double and not self.center) and self._draw_second_line or self._draw_adder
    self.second = _second_draw_method( (x,y,x0,y0))
    self.third = _second_draw_method( (2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0))


  def _draw_adder( self, coords):
    """returns list items"""
    if not hasattr( self, 'equithick'): 
      self.equithick = 0                
    x1, y1, x2, y2 = coords
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.wedge_width/2.0)
    d = sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    if self.equithick:
      step_size = 1.8*self.line_width
    else:
      step_size = self.line_width+1

    dx1 = (x0 - x1)/d 
    dy1 = (y0 - y1)/d 
    dx2 = (2*x2 -x0 -x1)/d 
    dy2 = (2*y2 -y0 -y1)/d 
    # params for equithick	
    dx = (x2 - x1)/d 
    dy = (y2 - y1)/d 
    ddx = x - x1 
    ddy = y - y1 

    coords2 = []
    coords2.extend((x1, y1))
    for i in range( 0, int( round( d/ step_size))+1):
      if self.equithick: 
        coords = [x1+dx*i*step_size+ddx, y1+dy*i*step_size+ddy, x1+dx*i*step_size-ddx, y1+dy*i*step_size-ddy] 
      else:
        coords = [x1+dx1*i*step_size, y1+dy1*i*step_size, x1+dx2*i*step_size, y1+dy2*i*step_size]
      if (coords[0] == coords[2] and coords[1] == coords[3]) and not self.equithick:
        if (dx1+dx2) > (dy1+dy2): 
          coords[0] += 1
        else:
          coords[1] += 1
      if i % 2:
        coords2.extend((coords[0], coords[1]))
      else:
        coords2.extend((coords[2], coords[3]))
    coords2.extend((x2, y2)) 
    if self.equithick:
      return [self.paper.create_line( coords2, width=self.line_width, fill=self.line_color, smooth=1)]
    else:
      return [self.paper.create_line( coords2, width=self.line_width, fill=self.line_color)]

  def _draw_b1( self):
    self._draw_n1()
    self.paper.itemconfigure( self.item, width = self.wedge_width)

  def _draw_b2( self):
    self._draw_n2()
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third
    [self.paper.itemconfigure( item, width = self.wedge_width) for item in items]

  def _draw_b3( self):
    self._draw_n3()
    if self.simple_double:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third
    [self.paper.itemconfigure( item, width = self.wedge_width) for item in items]


  ## // DRAW HELPER METHODS



  def redraw( self, recalc_side=0):
    if not self.__dirty:
      pass
      #print "redrawing non-dirty bond"
    if recalc_side:
      self._decide_distance_and_center()
    sel = self.selector
    if self.item:
      self.delete()
    self.draw( no_automatic=not recalc_side)
    # reselect
    if sel:
      self.select()
    self.__dirty = 0




  def simple_redraw( self):
    """very fast redraw that draws only a simple line instead of the bond,
    used in 3d rotation only (as for bkchem 0.5.0)"""
    [self.paper.delete( i) for i in self.second]
    self.second = []
    [self.paper.delete( i) for i in self.third]
    self.third = []
    if self.items:
      map( self.paper.delete, self.items)
      self.items = []
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    self.paper.coords( self.item, x1, y1, x2, y2)
    self.paper.itemconfig( self.item, width = self.line_width, fill=self.line_color)
    




  def focus( self):
    # all the items of the bond
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third

    if self.type in 'na':
      [self.paper.itemconfig( item, width = self.line_width+2) for item in items]
    elif self.type == 'b':
      [self.paper.itemconfig( item, width = self.wedge_width+2) for item in items]
    elif self.type == 'h':
      self.paper.itemconfig( self.item, fill="black")
    elif self.type == 'd':
      if self.simple_double and not self.center and not self.order == 1:
        [self.paper.itemconfig( item, width = self.line_width+2) for item in items]
      else:
        [self.paper.itemconfig( item, width = self.line_width + 2) for item in self.items+self.second+self.third]
    elif self.type == 'w':
      if self.center:
        items.remove( self.item)
      [self.paper.itemconfigure( item, fill='white', outline='black', width=1) for item in items]
      




  def unfocus( self):
    # all the items of the bond
    if self.simple_double and not self.center:
      items = [self.item]
    else:
      items = [self.item] + self.second + self.third

    if self.type in 'na':
      if not self.item:
        return
      [self.paper.itemconfig( item, width = self.line_width) for item in items]
    elif self.type == 'b':
      [self.paper.itemconfig( item, width = self.wedge_width) for item in items]
    elif self.type in 'h':
      self.paper.itemconfig( self.item, fill = "")
    elif self.type == 'd':
      if self.simple_double and not self.center and not self.order == 1:
        [self.paper.itemconfig( item, width = self.line_width) for item in items]
      else:
        [self.paper.itemconfig( item, width = self.line_width) for item in self.items+self.second+self.third]
    elif self.type == 'w':
      if self.center:
        items.remove( self.item)
      [self.paper.itemconfigure( item, fill=self.line_color, width=0) for item in items]




  def select( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x = ( x1 + x2) / 2
    y = ( y1 + y2) / 2
    if self.selector:
      self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
    else:
      self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2)
    self.paper.lower( self.selector)




  def unselect( self):
    self.paper.delete( self.selector)
    self.selector = None




  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    items = filter( None, [self.item] + self.second + self.third + self.items)
    if self.selector:
      items.append( self.selector)
    [self.paper.move( o, dx, dy) for o in items]
      



  def delete( self):
    self.unselect()
    items = [self.item] + self.second + self.third + self.items
    if self.item:
      self.paper.unregister_id( self.item)
    self.item = None
    self.second = []
    self.third = []
    self.items = []
    map( self.paper.delete, items)
    return self





  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    b = ['no', 'yes']
    type = package.getAttribute( 'type')
    if type:
      self.type = type[0]
      self.order = int( type[1])
    else:
      self.type = 'n'
      self.order = 1
    # implied
    if package.getAttribute( 'bond_width'):
      self.bond_width = float( package.getAttribute( 'bond_width')) * self.paper.real_to_screen_ratio()
    #else:
    #  self.bond_width = None
    if package.getAttribute( 'line_width'):
      self.line_width = float( package.getAttribute( 'line_width'))
    if package.getAttribute( 'wedge_width'):
      self.wedge_width = float( package.getAttribute( 'wedge_width'))
    if package.getAttribute( 'center'):
      self.center = b.index( package.getAttribute( 'center'))
    else:
      self.center = None
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'double_ratio'):
      self.double_length_ratio = float( package.getAttribute( 'double_ratio'))
    if package.getAttribute( 'simple_double'):
      self.simple_double = int( package.getAttribute( 'simple_double'))
    if package.getAttribute( 'auto_sign'):
      self.auto_bond_sign = int( package.getAttribute( 'auto_sign'))
    if package.getAttribute( 'equithick'):
      self.equithick = int( package.getAttribute( 'equithick'))
    else:
      self.equithick = 0
    # end of implied
    self.atom1 = self.paper.id_manager.get_object_with_id( package.getAttribute( 'start'))
    self.atom2 = self.paper.id_manager.get_object_with_id( package.getAttribute( 'end'))




  def post_read_analysis( self):
    """this method is called by molecule after the *whole* molecule is
    read to perform a post-load analysis of double bond positioning"""
    # after read analysis
    if self.order == 2:
      sign, center = self._compute_sign_and_center()
      if self.bond_width and self.bond_width * sign < 0:
        self.auto_bond_sign = -1
      
  



  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    b = ['no', 'yes']
    bnd = doc.createElement('bond')
    dom_extensions.setAttributes( bnd, (('type', "%s%d" % (self.type, self.order)),
                                        ('line_width', str( self.line_width)),
                                        ('start', self.atom1.id),
                                        ('end', self.atom2.id),
                                        ('double_ratio', str( self.double_length_ratio))))
    if hasattr( self, 'equithick') and self.equithick:
      bnd.setAttribute( 'equithick', str(1))
    if self.order != 1:
      bnd.setAttribute( 'bond_width', str( self.bond_width * self.paper.screen_to_real_ratio()))
      if self.order == 2:
        bnd.setAttribute( 'center', b[ self.center])
        if self.auto_bond_sign != 1:
          bnd.setAttribute( 'auto_sign', str( self.auto_bond_sign))
    if self.type != 'n':
      bnd.setAttribute( 'wedge_width', str( self.wedge_width * self.paper.screen_to_real_ratio())) 
    if self.line_color != '#000':
      bnd.setAttribute( 'color', self.line_color)
    if self.type != 'n' and self.order != 1:
      bnd.setAttribute( 'simple_double', str( int( self.simple_double)))
    return bnd





  def toggle_type( self, only_shift = 0, to_type='n', to_order=1, simple_double=1):
    # just simply use the simple_double value
    self.simple_double = simple_double
    if not only_shift:
      if to_type != self.type:
        # if type was changed simply apply the change
        self.switch_to_type( to_type)
        self.switch_to_order( to_order)
      elif to_order == 1 and to_type in 'nd':
        # we want to treat order=1, type='n' as special in order to support the s=>d d=>t t=>s behaviour
        # but only in case the type is 'n'
        v1 = self.atom1.get_free_valency()
        v2 = self.atom2.get_free_valency()
        if not v1 or not v2:
          # it is not possible to increase the order
          self.switch_to_order( 1)
        else:
          self.switch_to_order( (self.order % 3) + 1)
      elif to_order != self.order:
        # if order was changed we do the same
        self.switch_to_order( to_order)
      else:
        # here comes the interesting stuff, type and order are the same
        if to_type in "ha":
          # the types for which side matters
          if self.equithick:
            self.equithick = 0
            self.atom1, self.atom2 = self.atom2, self.atom1
          else:
            self.equithick = 1

        if to_type in "w":
          self.atom1, self.atom2 = self.atom2, self.atom1
          # if the side is switched for double bond we need to change the sing of the bond_width
          if not self.center:
            self.bond_width = -self.bond_width
        elif to_order == 2:
          # we will shift the position of the second bond
          if self.center:
            self.bond_width = -self.bond_width
            self.auto_bond_sign = -self.auto_bond_sign
            self.center = 0
          elif self.bond_width > 0:
            self.bond_width = -self.bond_width
            self.auto_bond_sign = -self.auto_bond_sign
          else:
            self.center = 1
        else:
          # we do just nothing
          pass
    elif self.order == 2:
      # we will shift the position of the second bond
      if self.center:
        self.bond_width = -self.bond_width
        self.auto_bond_sign = -self.auto_bond_sign
        self.center = 0
      elif self.bond_width > 0:
        self.bond_width = -self.bond_width
        self.auto_bond_sign = -self.auto_bond_sign
      else:
        self.center = 1
    else:
      # we ignore it when shift only appears for non-double bonds
      pass
    self.redraw()





  def switch_to_type( self, type):
    if type in "wha" and self.type not in "wha":
      # get the standard width only if the changes is not within the "wha" group
      self.wedge_width = self.paper.any_to_px( self.paper.standard.wedge_width)
    elif type not in "wha" and self.type in "wha":
      # when both are outside the 'wha' do the similar
      self.bond_width = self.paper.any_to_px( self.paper.standard.bond_width)
    self.type = type





  def switch_to_order( self, order):
    self.order = order
    if self.order == 3:
      self.center = 0
    if self.order > 1:
      self._decide_distance_and_center()
    





  def _decide_distance_and_center( self):
    """according to molecular geometry decide what bond.center and bond.bond_width should be"""
    line = self.atom1.get_xy() + self.atom2.get_xy()
    if not self.bond_width:
      self.bond_width = self.standard.bond_width
      #length = sqrt((line[0]-line[2])**2  + (line[1]-line[3])**2)
      #self.bond_width = round( length / 5, 1)
    # does not need to go further if the bond is not double
    if self.order != 2:
      return 
    sign, center = self._compute_sign_and_center()
    self.bond_width = self.auto_bond_sign * sign * abs( self.bond_width)
    self.center = center





  def _compute_sign_and_center( self):
    """returns tuple of (sign, center) where sign is the default sign of the self.bond_width"""
    line = self.atom1.get_xy() + self.atom2.get_xy()
    atms = self.atom1.get_neighbors() + self.atom2.get_neighbors()
    atms = misc.difference( atms, [self.atom1, self.atom2])
    coords = [a.get_xy() for a in atms]

    # searching for circles

    circles = 0

    for ring in self.molecule.get_smallest_independent_cycles():
      if self.atom1 in ring and self.atom2 in ring:
        on_which_side = lambda xy: geometry.on_which_side_is_point( line, xy)
        circles += reduce( operator.add, map( on_which_side, [a.get_xy() for a in ring if a not in self.atoms]))

    if circles:
      side = circles
    else:
      sides = [geometry.on_which_side_is_point( line, xy) for xy in coords]
      side = reduce( operator.add, sides, 0)
    # on which side to put the second line
    if side == 0 and (len( self.atom1.get_neighbors()) == 1 or
                      len( self.atom2.get_neighbors()) == 1):
      # maybe we should center, but this is usefull only when one of the atoms has no other substitution
      return (1 ,1)
    else:
      if not circles:
        # recompute side with weighting of atom types
        for i in range( len( sides)):
          if sides[i] and atms[i].name == 'H':
            sides[i] *= 0.1 # this discriminates H
          elif sides[i] and atms[i].name != 'C':
            sides[i] *= 0.2 # this makes "non C" less then C but more then H
          side = reduce( operator.add, sides, 0)
      if side < 0:
        return (-1, 0)
      else:
        return (1, 0)
    




  def get_atoms( self):
    return self.get_vertices()




  def change_atoms( self, a1, a2):
    """used in overlap situations, it replaces reference to atom a1 with
    reference to atom a2"""
    if self.atom1 == a1:
      self.atom1 = a2
    elif self.atom2 == a1:
      self.atom2 = a2
    else:
      warn("not bonds' atom in bond.change_atoms()", UserWarning, 2)




  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    return self.paper.bbox( self.item)





  def lift( self):
    [self.paper.lift( i) for i in self.items]
    if self.selector:
      self.paper.lift( self.selector)
    if self.second:
      [self.paper.lift( o) for o in self.second]
    if self.third:
      [self.paper.lift( o) for o in self.third]
    if self.item:
      self.paper.lift( self.item)





  def transform( self, tr):
    if not self.item:
      return 
    for i in [self.item] + self.second + self.third + self.items:
      coords = self.paper.coords( i)
      tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))
    # we need to check if the sing of double bond width has not changed
    # this happens during 3d rotation
    if self.order == 2 and not self.center:
      line = list( self.atom1.get_xy())
      line += self.atom2.get_xy()
      x, y = self.paper.coords( self.second[0])[0:2]
      sign = geometry.on_which_side_is_point( line, (x,y))
      if sign * self.bond_width < 0:
        self.bond_width *= -1

