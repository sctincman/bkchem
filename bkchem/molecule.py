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
#
#
#
#--------------------------------------------------------------------------

"""home of the molecule class"""

from __future__ import division
from __future__ import generators

from math import atan2, sin, cos, pi, sqrt
import misc
import time
import geometry
from warnings import warn
import dom_extensions
import xml.dom.minidom as dom
import periodic_table as PT
import groups_table as GT
import copy
import helper_graphics as hg
from parents import simple_parent
from atom import atom
from bond import bond

class molecule( simple_parent):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ
  
  object_type = 'molecule'
  # other meta infos
  meta__is_container = 1
  # undo meta infos
  meta__undo_simple = ('name','id')
  meta__undo_copy = ('atoms_map', 'bonds')
  meta__undo_2d_copy = ('connect',)
  meta__undo_children_to_record = ('atoms_map','bonds')
  
  def __init__( self, paper, package = None):
    self.paper = paper
    self.atoms_map = []  # list of atoms
    self.bonds = []      # list of bonds
    self.connect = []    # matrix that shows conectivity of each atom
    self.sign = -1
    self.name = ''
    self.id = ''
    self._iterator = 0
    self.t_bond_first = None  # template
    self.t_bond_second = None
    self.t_atom = None
    self.focus_item = None
    if package:
      self.read_package( package) 
    
  def __iter__( self):
    return self

  def next( self):
    i = self._iterator
    self._iterator += 1
    try:
      return self.atoms_map[ i]
    except IndexError:
      try:
        return self.bonds[ i - len( self.atoms_map)]
      except IndexError:
        self._iterator = 0
        raise StopIteration

  def feed_data( self, atoms_map, bonds, connect):
    "feed data from another molecule"
    self.bonds += bonds
    self.atoms_map += atoms_map
    for line in self.connect:
      line.extend( len(connect)*[0])
    l = len( self.connect)
    for i in range( len( connect)):
      self.connect.append( l*[0])
      self.connect[l+i].extend( connect[i])
    map( lambda o: o.set_molecule( self), self)
      
  def eat_molecule( self, mol):
    "transfers everything from mol to self, now only calls feed_data"
    self.feed_data( mol.atoms_map, mol.bonds, mol.connect)

  def add_atom_to( self, a1, bond_to_use=None, pos=None):
    """adds new atom bound to atom id with bond, the position of new atom can be specified in pos or is
    decided calling find_place(),"""
    if pos != None:
      x, y = pos
    else:
      x, y = self.find_place( a1, self.paper.any_to_px( self.paper.standard.bond_length))
    a2 = self.create_new_atom( x, y)
    b = bond_to_use or bond( self.paper, order=1, type='n')
    b.set_atoms( a1, a2)
    self.insert_bond( b)
    b.draw()
    return a2, b

  def insert_bond( self, b):
    self.connect[ self.atoms_map.index( b.atom1)][ self.atoms_map.index( b.atom2)] = b
    self.connect[ self.atoms_map.index( b.atom2)][ self.atoms_map.index( b.atom1)] = b
    self.bonds.append( b)
    if not b.molecule:
      b.set_molecule( self)

  def find_place( self, a, distance):
    """tries to find accurate place for next atom around atom 'id',
    returns x,y and list of ids of 'items' found there for overlap, those atoms are not bound to id"""
    ids_bonds = self.atoms_bound_to( a)
    if len( ids_bonds) == 0:
      x = a.get_x() + round( cos( pi/6) *distance)
      y = a.get_y() - round( sin( pi/6) *distance)
    elif len( ids_bonds) == 1:
      x = a.get_x() + round( cos( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance)
      y = a.get_y() + round( sin( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance)
      self.sign = -self.sign
    else:
      x, y = self.find_least_crowded_place_around_atom( a, range=distance)
    return x, y

  def atoms_bonds( self, a):
    return filter( lambda o: o,  self.connect[ self.atoms_map.index( a)])

  def atoms_bound_to( self, a):
    "returns list of ids of atoms bound to atom with id = 'id'"
    bonds = self.connect[ self.atoms_map.index( a)]
    ret = []
    for i in bonds:
      if i:
        ret.append( self.atoms_map[ bonds.index( i)])
    return ret

  def get_angle( self, a1, a2):
    "what is the angle between horizontal line through i1 and i1-i2 line"
    a = a2.get_x() - a1.get_x()
    b = a2.get_y() - a1.get_y()
    return atan2( b, a)
    
  def delete_items( self, items):
    """deletes items and also makes cleaning of orphan bonds and atoms"""
    if not items:
      return items, []     # quick way to avoid costly evaluation
    deleted = []+items
    map( self.delete_bond, filter( lambda o: o.object_type == 'bond', items))
    map( self.delete_atom, filter( lambda o: o.object_type == 'atom', items))
    if self.connect:
      # delete bonds that are not in connect anymore
      bonds_in_connect = misc.filter_unique( reduce( lambda a,b: a+b, self.connect))
      deleted += map( self.delete_bond, filter( lambda o: o not in bonds_in_connect, self.bonds))
      # delete also orphan atoms
      deleted += map( self.delete_atom, filter( lambda o: not self.atoms_bonds( o), self.atoms_map))
      # recalculation of second line of double bond position
      [o.redraw( recalc_side=1) for o in self.bonds if o.order == 2 and o.item]
      # recalculate marks positions
      [o.reposition_marks() for o in self.atoms_map]
    else:
      deleted += map( self.delete_bond, self.bonds)
    return deleted, self.check_integrity()

  def delete_bond( self, item):
    for i in range( len( self.connect)):
      if item in self.connect[i]:
        j = self.connect[i].index( item)
        self.connect[i][j] = 0
        self.connect[j][i] = 0
        break
    item.delete()
    self.bonds.remove( item)
    return item
      
  def delete_atom( self, item):
    "remove links to atom from molecule records"
    del self.connect[ self.atoms_map.index( item)]
    for i in range( len( self.connect)):
      del self.connect[i][ self.atoms_map.index( item)]
    self.atoms_map.remove( item)
    item.delete()
    if item == self.t_atom:
      t_atom = None
    if item == self.t_bond_first:
      t_bond_first = None
    if item == self.t_bond_second:
      t_bond_second = None
    return item

  def create_new_atom( self, x, y):
    a = atom( self.paper, xy=(x, y))
    self.insert_atom( a)
    a.draw()
    return a

  def insert_atom( self, at):
    "inserts atom to molecule without any connections"
    if len( self.connect):
      for i in range( len( self.connect)):
        self.connect[i].append( 0)
      self.connect.append( (len( self.connect)+1) *[0])
    else:
      self.connect = [[0]]
    self.atoms_map.append( at)
    at.set_molecule( self)
  
  def check_integrity( self):
    """after deleting atoms or bonds it is important to see if it's needed to divide molecule to fragments
    and return them in form of list of new molecules"""
    if self.connect == []:
      return []
    old_map = self.atoms_map[:]
    # first distribute atoms to new_maps
    def walker( a):
      mmap.append( a)
      for i in self.atoms_bound_to( a):
        if i not in mmap:
          walker( i)
    new_maps = []
    while old_map:
      mmap = []
      walker( old_map[0])
      new_maps.append( mmap)
      old_map = misc.difference( old_map, mmap)
    if len( new_maps) == 1:
      return []
    # reorder connectivity matrixes
    new_cons = []
    for mmap in new_maps:
      con = []
      for i in range( len( mmap)):
        con.append( len( mmap)*[0])
      for i in range( len( mmap)):
        for j in range( i+1, len( mmap)):
          con[i][j] = self.connect[ self.atoms_map.index( mmap[i])][ self.atoms_map.index( mmap[j])]
          con[j][i] = con[i][j]
      new_cons.append( con)
    # 
    new_bonds = []
    for mol in new_cons:
      new_bonds.append( misc.filter_unique( filter( lambda o: o, reduce( lambda a,b: a+b, mol))))
    ret = []
    for i in range( len( new_cons)):
      ret.append( molecule( self.paper))
      ret[i].feed_data( new_maps[i], new_bonds[i], new_cons[i])
    return ret

  def is_empty( self):
    return (self.connect == [])

  def get_atoms( self):
    return self.atoms_map

  def get_bonds( self):
    return self.bonds

  def read_package( self, package):
    self.name = package.getAttribute( 'name')
    self.id = package.getAttribute( 'id')
    for a in package.getElementsByTagName( 'atom'):
      self.insert_atom( atom( self.paper, package=a, molecule=self))
    self._id_map = map( lambda a: a.get_cdml_id(), self.atoms_map)
    for b in package.getElementsByTagName( 'bond'):
      self.insert_bond( bond( self.paper, package = b, molecule=self))
    temp = package.getElementsByTagName('template')
    if temp:
      temp = temp[0]
      self.t_atom = self.get_atom_with_cdml_id( temp.getAttribute( 'atom'))
      if temp.getAttribute('bond_first') and temp.getAttribute('bond_second'):
        self.t_bond_first = self.get_atom_with_cdml_id( temp.getAttribute( 'bond_first'))
        self.t_bond_second = self.get_atom_with_cdml_id( temp.getAttribute( 'bond_second'))
      self.next_to_t_atom = self.atoms_bound_to( self.t_atom)[0]
    # we need to analyze the positioning of the double bond in order to be able
    # to use the initial values later
    [b.post_read_analysis() for b in self.bonds]

  def get_package( self, doc):
    mol = doc.createElement('molecule')
    mol.setAttribute( 'name', self.name)
    mol.setAttribute( 'id', self.id)
    if self.t_atom:
      if self.t_bond_second and self.t_bond_first:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.get_cdml_id())),
                                                        ('bond_first', str( self.t_bond_first.get_cdml_id())),
                                                        ('bond_second', str( self.t_bond_second.get_cdml_id()))))
      else:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.get_cdml_id())),))
    for i in self:
      mol.appendChild( i.get_package( doc))
    return mol

  def draw( self):
    # the molecule is an iterator
    [a.draw() for a in self]

  def bond_between( self, a1, a2):
    "returns id of bond between atoms i1 and i2"
    return self.connect[ self.atoms_map.index( a1)][ self.atoms_map.index( a2)]

  def handle_overlap( self):
    "deletes one of overlaping atoms and updates the bonds"
    to_delete = []
    for a in self.atoms_map:
      for b in self.atoms_map:
        if a != b:
          x1, y1 = a.get_xy()
          x2, y2 = b.get_xy()
          if (abs( x1-x2) < 4) and (abs( y1-y2) <4):
            if a not in to_delete:
              map( lambda x: x.change_atoms( b, a), self.atoms_bonds( b))
              to_delete.append( b)
    deleted = misc.filter_unique( to_delete)
    map( self.delete_atom, deleted)
    # after all is done, find and delete orphan bonds and update the others
    for b in self.bonds[:]:
      i1, i2 = map( self.atoms_map.index, b.get_atoms())
      if self.connect[i1][i2] and self.connect[i1][i2] != b:
        self.delete_bond( b)
        deleted.append( b)
        #self.bonds.remove( b)
      elif not self.connect[i1][i2]:
        self.connect[i1][i2] = b
        self.connect[i2][i1] = b
    for b in self.bonds:
      b.redraw()
    return deleted

  def move( self, dx, dy):
    """moves the whole molecule"""
    for o in self.atoms_map +self.bonds:
      o.move( dx, dy)

  def bbox( self):
    items = []
    for a in self.atoms_map:
      items.append( a.item)
    return self.paper.list_bbox( items)

  def get_atom_with_cdml_id( self, id):
    return self.atoms_map[ self._id_map.index( id)]
    
  def set_atom_cdml_id( self, id, atom):
    pass

  def delete( self):
    [o.delete() for o in self.bonds+self.atoms_map]

  def redraw( self, reposition_double=0):
    for o in self.bonds:
      if o.order == 2:
        o.redraw( recalc_side=reposition_double)
      else:
        o.redraw()
    [o.redraw() for o in self.atoms_map]  

    
  def get_atoms_valency( self, atom):
    val = 0
    for b in self.atoms_bonds( atom):
        val += b.order
    return val

  def get_formula_dict( self):
    comp = PT.formula_dict()
    for a in self.atoms_map:
      comp += a.get_formula_dict()
    return comp

  def expand_groups( self, atoms=[]):
    """expands all group atoms; optional atoms selects atoms to expand - all used if not present"""
    names = self.paper.gm.get_template_names()
    if not atoms:
      map = copy.copy( self.atoms_map) # need to do that because the self.atoms_map gets changed during the cycle
    else:
      map = atoms # only selected atoms
    for a in map:
      if a.type == "group":
        if a.name in names:
          a2 = self.atoms_bound_to( a)[0]
          x1, y1 = a2.get_xy()
          x2, y2 = a.get_xy()
          t = self.paper.gm.get_transformed_template( names.index( a.name), (x1,y1,x2,y2), type='atom1')
          t.draw()
          self.eat_molecule( t)
          self.move_bonds_between_atoms( a, t.next_to_t_atom)
          self.delete_items( [a])
        else:
          print "unknown group %s" % a.name
      elif a.type == "chain":
        p = PT.formula_dict( a.name)
        n = p['C']
        a.set_name( 'C')
        a.redraw()
        for i in range( n-1):
          a,b = self.add_atom_to( a)

  def move_bonds_between_atoms( self, a1, a2):
    """transfers all bonds from one atom to the other; both atoms must be in self"""
    for b in self.atoms_bonds( a1):
      b.change_atoms( a1, a2)
    i = self.atoms_map.index( a1)
    l = self.atoms_map.index( a2)
    for j in range( len( self.connect)):
      for k in range( len( self.connect)):
        if self.connect[j][k]:
          if j == i:
            self.connect[l][k] = self.connect[j][k]
            self.connect[j][k] = 0
          elif k == i:
            self.connect[j][l] = self.connect[j][k]
            self.connect[j][k] = 0

  def lift( self):
    [o.lift() for o in self.bonds + self.atoms_map]

  def find_least_crowded_place_around_atom( self, a, range=10):
    atms = self.atoms_bound_to( a)
    x, y = a.get_xy()
    angles = [geometry.clockwise_angle_from_east( at.x-a.x, at.y-a.y) for at in atms]
    angles.append( 2*pi + min( angles))
    angles.sort()
    angles.reverse()
    diffs = misc.list_difference( angles)
    i = diffs.index( max( diffs))
    angle = (angles[i] +angles[i+1]) / 2
    return x +range*cos( angle), y +range*sin( angle)
    

  def get_shape_defining_children( self):
    for i in self.atoms_map:
      yield i

  def flush_graph_to_file( self, name="/home/beda/oasa/oasa/mol.graph"):
    f = file( name, 'w')
    for a in self.atoms_map:
      f.write('%s ' % a.name)
    f.write('\n')
    for b in self.bonds:
      f.write('%d %d %d\n' % (b.order, self.atoms_map.index( b.atom1), self.atoms_map.index( b.atom2)))
    f.close()

  def transform( self, tr):
    """applies given transformation to its children"""
    for a in self.atoms_map:
      a.transform( tr)
    for b in self.bonds:
      b.transform( tr)

