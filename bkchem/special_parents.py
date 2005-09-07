#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2005  Beda Kosata <beda@zirael.org>

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


import misc
import marks
from sets import Set
import geometry
from math import sin, cos, sqrt, pi
import types
import oasa
from parents import meta_enabled, area_colored, point_drawable, text_like, child_with_paper
from singleton_store import Store, Screen
from ftext import ftext
import xml.dom.minidom as dom
import tkFont




class vertex_common( object):
  """implements some properties and methods common for all vertices
  (children of oasa.chem_vertex), such as numbering and mark support"""

  meta__undo_properties = ('number', 'show_number')
  meta__undo_copy = ('marks',)
  meta__undo_children_to_record = ('marks',)

  meta__allowed_marks = ()   # when empty all marks are allowed


  def __init__( self):
    self.marks = Set()
    # numbering
    self._show_number = True
    self._number = None



  # number
  def _set_number( self, number):
    if number:
      self._number = unicode( number)
    else:
      self._number = number # we do not want to convert None to unicode :)
    if self._number != None and self.show_number:
      numbers = self.get_marks_by_type( "atom_number")
      if not numbers:
        self.create_mark( "atom_number", draw=self.drawn)
      elif self.drawn:
        numbers[0].redraw()


  def _get_number( self):
    if hasattr( self, "_number"):
      return self._number
    else:
      return None

  number = property( _get_number, _set_number, None, "the number associated with the atom")


  # show_number
  def _set_show_number( self, show_number):
    self._show_number = show_number
    if self._show_number and self.number:
      numbers = self.get_marks_by_type( "atom_number")
      if not numbers:
        self.create_mark( "atom_number", draw=self.drawn)
    elif not self._show_number and self.number:
      numbers = self.get_marks_by_type( "atom_number")
      if numbers:
        self.remove_mark( numbers[0])
        

  def _get_show_number( self):
    return self._show_number

  show_number = property( _get_show_number, _set_show_number, None, "should the number (if present) be displayed")



  def set_mark( self, mark='radical', angle='auto', draw=1):
    """sets the mark and takes care of charge and multiplicity changes"""
    if not self.meta__allowed_marks or mark in self.meta__allowed_marks:
      m = self.create_mark( mark=mark, angle=angle)
      self._set_mark_helper( mark, sign=1)
      return m
    else:
      raise ValueError, "not a allowed mark for this type - %s" % mark



  def remove_mark( self, mark):
    """mark is either mark instance of type, in case of instance, the instance is removed,
    in case of type a random mark of this type (if present is removed).
    Returns the removed mark or None"""
    if type( mark) == types.StringType:
      ms = [m for m in self.marks if m.__class__.__name__ == mark]
      if ms:
        m = ms[0]
      else:
        return None
    elif isinstance( mark, marks.mark):
      if mark in self.marks:
        m = mark
      else:
        raise ValueError, "trying to remove a mark that does not belong to this atom"
    else:
      raise TypeError, "mark is on unknown type " + str( mark)

    m.delete()
    self.marks.remove( m)
    self._set_mark_helper( m.__class__.__name__, sign=-1)
    return m



  def _set_mark_helper( self, mark, sign=1):
    pass

    



  def create_mark( self, mark='radical', angle='auto', draw=1):
    """creates the mark, does not care about the chemical meaning of this"""
    # decide where to put the mark
    if angle == 'auto':
      x, y = self.find_place_for_mark( mark)
    else:
      x = self.x + round( cos( angle) *dist)
      y = self.y + round( sin( angle) *dist)
      #ang = angle

    m = marks.__dict__[ mark]( self, x, y, auto=(angle=='auto'))
    if draw:
      m.draw()
    self.marks.add( m)
    return m




  def get_marks_by_type( self, mark_type):
    return [m for m in self.marks if m.__class__.__name__ == mark_type]




  def reposition_marks( self):
    ms = Set( [m for m in self.marks if m.auto])
    self.marks -= ms
    for m in ms:
      x, y = self.find_place_for_mark( m.__class__.__name__)
      m.move_to( x, y)
      self.marks.add( m)




  def find_place_for_mark( self, mark):

    # deal with marks centered
    if marks.__dict__[ mark].meta__mark_positioning == 'atom':
      return self.x, self.y

    # deal with statically positioned marks
    if marks.__dict__[ mark].meta__mark_positioning == 'righttop':
      bbox = self.bbox()
      return bbox[2]+2, bbox[1]
    
    if not self.show:
      dist = 5 + round( marks.__dict__[ mark].standard_size / 2)
    else:
      dist = 0.75*self.font_size + round( marks.__dict__[ mark].standard_size / 2)

    atms = self.get_neighbors()
    x, y = self.get_xy()

    # special cases
    if not atms:
      # single atom molecule
      if self.show_hydrogens and self.pos == "center-first":
        return x -dist, y-3
      else:
        return x +dist, y-3

    # normal case
    coords = [(a.x,a.y) for a in atms]
    # we have to take marks into account
    [coords.append( (m.x, m.y)) for m in self.marks]
    # hydrogen positioning is also important
    if self.show_hydrogens and self.show:
      if self.pos == 'center-last':
        coords.append( (x-10,y))
      else:
        coords.append( (x+10,y))
    # now we can compare the angles
    angles = [geometry.clockwise_angle_from_east( x1-x, y1-y) for x1,y1 in coords]
    angles.append( 2*pi + min( angles))
    angles.sort()
    angles.reverse()
    diffs = misc.list_difference( angles)
    i = diffs.index( max( diffs))
    angle = (angles[i] +angles[i+1]) / 2

    # in visible text x,y are not on the center, therefore we compensate for it
    if self.show:
      y -= 0.166 * self.font_size
    
    return x +dist*cos( angle), y +dist*sin( angle)











class drawable_chem_vertex( oasa.chem_vertex, meta_enabled, area_colored, point_drawable, text_like, child_with_paper, vertex_common):
  """this is a common ancestor for all children of oasa.chem_vertex in bkchem. It adds some
  basic functionality to the chem_vertex so that it is not needed to add it every child;
  all the methods are tuned for always shown texts; atoms need to override something"""

  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo meta infos
  meta__undo_fake = ('xml_ftext',)
  meta__undo_simple = ()
  meta__undo_properties = area_colored.meta__undo_properties + \
                          point_drawable.meta__undo_properties + \
                          text_like.meta__undo_properties + \
                          vertex_common.meta__undo_properties + \
                          ( 'z', 'molecule', 'pos', 'charge')
  meta__undo_copy = vertex_common.meta__undo_copy + ('_neighbors',)
  meta__undo_children_to_record = vertex_common.meta__undo_children_to_record



  def __init__( self, standard=None, xy=(), molecule=None):
    meta_enabled.__init__( self, standard=standard)
    vertex_common.__init__( self)
    self.molecule = molecule
    point_drawable.__init__( self)
    oasa.chem_vertex.__init__( self)

    if xy:
      self.x, self.y = xy
    self.z = 0

    # hidden
    self._reposition_on_redraw = 0

    # presentation attrs
    self.selector = None
    self._selected = 0 #used to keep track whether this is selected or not
    self.item = None
    self.ftext = None

    self.pos = None
    self.focus_item = None




  ## ---------------------------------------- PROPERTIES ------------------------------



  # molecule
  def _get_molecule( self):
    return self._molecule

  def _set_molecule( self, mol):
    self._molecule = mol

  molecule = property( _get_molecule, _set_molecule)


  # x
  def _get_x( self):
    return self._x

  def _set_x( self, x):
    self._x = Screen.any_to_px( x)

  x = property( _get_x, _set_x)


  # y
  def _get_y( self):
    return self._y

  def _set_y( self, y):
    self._y = Screen.any_to_px( y)

  y = property( _get_y, _set_y)


  # z
  def _get_z( self):
    return self._z or 0

  def _set_z( self, z):
    self._z = z

  z = property( _get_z, _set_z)



  # pos
  def _get_pos( self):
    return self._pos

  def _set_pos( self, pos):
    self._pos = pos
    self.dirty = 1

  pos = property( _get_pos, _set_pos)



  # parent
  def _get_parent( self):
    return self.molecule

  def _set_parent( self, par):
    self.molecule = par

  parent = property( _get_parent, _set_parent, None,
                     "returns self.molecule")



  # drawn
  def _get_drawn( self):
    """is the atoms drawn? on the paper or just virtual"""
    if self.item:
      return 1
    return 0

  drawn = property( _get_drawn, None, None, "tells if the atom is already drawn")



  # font_size (override of text_like.font_size)
  def _get_font_size( self):
    return self._font_size

  def _set_font_size( self, font_size):
    self._font_size = font_size
    self.dirty = 1

  font_size = property( _get_font_size, _set_font_size)




  # xml_ftext (override text_like.xml_ftext)
  def _get_xml_ftext( self):
    return self.symbol

  xml_ftext = property( _get_xml_ftext, None, None, "the text used for rendering using the ftext class")




  ## // -------------------- END OF PROPERTIES --------------------------


  

  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    meta_enabled.copy_settings( self, other)
    area_colored.copy_settings( self, other)
    point_drawable.copy_settings( self, other)
    text_like.copy_settings( self, other)
    child_with_paper.copy_settings( self, other)
    other.pos = self.pos




  def decide_pos( self):
    """decides whether the first or the last letter in the text should be positioned on the
    coords of the vertex"""
    as = self.get_neighbors()
    p = 0
    for a in as:
      if a.x < self.x:
        p -= 1
      elif a.x > self.x:
        p += 1
    if p > 0:
      self.pos = 'center-last'
    else:
      self.pos = 'center-first'




  def draw( self, redraw=False):
    "draws vertex with respect to its properties"
    if self.item:
      warn( "drawing vertex that is probably drawn", UserWarning, 2)
    x, y = self.x, self.y
    self.update_font()

    if not self.pos:
      self.decide_pos()
    # we use self.text to force undo when it is changed (e.g. when atom is added to OH so it changes to O)
    name = '<ftext>%s</ftext>' % self.xml_ftext
    self.ftext = ftext( self.paper, (self.x, self.y), name, font=self.font, pos=self.pos, fill=self.line_color)
    self.ftext.draw()
    x1, y1, x2, y2 = self.ftext.bbox()
    self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('atom'))
    ## shrink the selector to improve appearance (y2-2)
    self.selector = self.paper.create_rectangle( x1, y1, x2, y2-3, fill=self.area_color, outline='',tags='helper_a')
    if not redraw:
      [m.draw() for m in self.marks]

    self.ftext.lift()
    self.paper.lift( self.item)
    self.paper.register_id( self.item, self)
    self._reposition_on_redraw = 0




  def redraw( self, suppress_reposition=0):
    if self._reposition_on_redraw and not suppress_reposition:
      self.reposition_marks()
      self._reposition_on_redraw = 0

    self.update_font()
    # at first we delete everything...
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self. selector)
    if self.ftext:
      self.ftext.delete()
    self.item = None # to ensure that warning in draw() is not triggered when redrawing
    # ...then we draw it again
    self.draw( redraw=True)
    [m.redraw() for m in self.marks]

    if self._selected:
      self.select()
    else:
      self.unselect()
    if not self.dirty:
      pass
      #print "redrawing non-dirty atom"
    self.dirty = 0





  def focus( self):
    self.paper.itemconfig( self.selector, fill='grey')



  def unfocus( self):
    self.paper.itemconfig( self.selector, fill=self.area_color)



  def select( self):
    self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1




  def unselect( self):
    self.paper.itemconfig( self.selector, outline='')
    self._selected = 0



  def move( self, dx, dy, dont_move_marks=False):
    """moves object with his selector (when present)"""
    # saving old dirty value
    # d = self.dirty
    self.x += dx
    self.y += dy
    if self.drawn:
      self.paper.move( self.item, dx, dy)
      if self.selector:
        self.paper.move( self.selector, dx, dy)
      if self.ftext:
        self.ftext.move( dx, dy)
      if not dont_move_marks:
        for m in self.marks:
          m.move( dx, dy)
    # restoring dirty value because move does not dirty the atom
    # self.dirty = d



  def move_to( self, x, y, dont_move_marks=False):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy, dont_move_marks=dont_move_marks)



  def get_xy( self):
    return self.x, self.y




  def get_xyz( self, real=0):
    """returns atoms coordinates, default are screen coordinates, real!=0
    changes it to real coordinates (these two are usually different for imported molecules)"""
    if real:
      x, y = self.paper.screen_to_real_coords( (self.x, self.y))
      z = self.z *self.paper.screen_to_real_ratio()
      return x, y, z
    else:
      return self.x, self.y, self.z





  def delete( self):
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.unselect()
      self.paper.delete( self.selector)
      self.selector = None
      self._selected = 0
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None
    if self.ftext:
      self.ftext.delete()
    [m.delete() for m in self.marks]
    self.marks = Set()
    return self





  def toggle_center( self, mode = 0):
    """toggles the centering of text between 'center-first' and 'center-last'(mode=0)
    or sets it strictly - mode=-1, mode=1"""
    if not mode:
      if self.pos == 'center-last':
        self.pos = 'center-first'
      else:
        self.pos = 'center-last'
    elif mode == -1:
      self.pos = 'center-first'
    else:
      self.pos = 'center-last'
    self.redraw()





  def update_font( self):
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)
        



  def scale_font( self, ratio):
    """scales font of atom. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()




  def lift( self):
    # marks
    [m.lift() for m in self.marks]
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)


  def lift_selector( self):
    if self.selector:
      self.paper.lift( self.selector)



  def transform( self, tr):
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y, dont_move_marks=1)
    for m in self.marks:
      m.transform( tr)




  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    if self.item:
      return self.paper.bbox( self.item)
    else:
      # we have to calculate it, the atoms was not drawn yet
      length = self.font.measure( self.text)
      if self.pos == 'center-first':
        dx = self.font.measure( self.text[0]) / 2
        return (self.x + length - dx, self.y + 0.3*self.font_size, self.x - dx, self.y - 0.7*self.font_size) 
      else:
        dx = self.font.measure( self.text[-1]) / 2
        return (self.x + dx, self.y + 0.3*self.font_size, self.x - length + dx, self.y - 0.7*self.font_size) 
