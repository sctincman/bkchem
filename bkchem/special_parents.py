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




class vertex_common( object):
  """implements some properties and methods common for all vertices
  (atoms, groups and textatoms), such as numbering and mark support"""

  meta__undo_properties = ('number', 'show_number')
  meta__undo_copy = ('marks',)
  meta__undo_children_to_record = ('marks',)


  def __init__( self):
    self.marks = Set()
    # numbering
    self.show_number = True
    self.number = None



  # number
  def _set_number( self, number):
    self._number = number
    if self._number != None and self.show_number:
      numbers = self.get_marks_by_type( "atom_number")
      if not numbers:
        self.create_mark( "atom_number", draw=self.drawn)


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



  def set_mark( self, mark='radical', angle='auto'):
    """sets the mark and takes care of charge and multiplicity changes"""
    m = self.create_mark( mark=mark, angle=angle)
    self._set_mark_helper( mark, sign=1)
    return m



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
    return [m for m in self.marks in m.__class__.__name__ == mark_type]




  def reposition_marks( self):
    ms = Set( [m for m in self.marks if m.auto])
    self.marks -= ms
    for m in ms:
      x, y = self.find_place_for_mark( m.__class__.__name__)
      m.move_to( x, y)
      self.marks.add( m)




  def find_place_for_mark( self, mark):
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

