#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002, 2003, 2004 Beda Kosata <beda@zirael.org>

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
from parents import container, top_level, id_enabled
from atom import atom
from bond import bond

class molecule( container, top_level, id_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ
  
  object_type = 'molecule'
  # other meta infos
  meta__is_container = 1
  # undo meta infos
  meta__undo_simple = ('name',)
  meta__undo_properties = ('id',)
  meta__undo_copy = ('atoms', 'bonds')
  meta__undo_2d_copy = ('connect',)
  meta__undo_children_to_record = ('atoms','bonds')
  
  def __init__( self, paper, package = None):
    id_enabled.__init__( self, paper)
    container.__init__( self)

    self.atoms = []  # list of atoms
    self.bonds = []      # list of bonds
    self.connect = []    # matrix that shows conectivity of each atom
    self.sign = 1
    self._last_used_atom = None 
    self.name = ''
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
      return self.atoms[ i]
    except IndexError:
      try:
        return self.bonds[ i - len( self.atoms)]
      except IndexError:
        self._iterator = 0
        raise StopIteration


  ### PROPERTIES

  # shape_defining_points
  def __get_shape_defining_points( self):
    return self.atoms

  shape_defining_points = property( __get_shape_defining_points, None, None,
                                    "returns list of atoms")


  # children
  def __get_children( self):
    return self.atoms + self.bonds

  children = property( __get_children, None, None,
                       "returns list of atoms and bonds")



  ### // PROPERTIES



  def feed_data( self, atoms, bonds, connect):
    "feed data from another molecule"
    self.bonds += bonds
    self.atoms += atoms
    for line in self.connect:
      line.extend( len(connect)*[0])
    l = len( self.connect)
    for i in range( len( connect)):
      self.connect.append( l*[0])
      self.connect[l+i].extend( connect[i])
    for o in self.children:
      o.molecule = self
      

  def eat_molecule( self, mol):
    "transfers everything from mol to self, now only calls feed_data"
    self.feed_data( mol.atoms, mol.bonds, mol.connect)


  def add_atom_to( self, a1, bond_to_use=None, pos=None):
    """adds new atom bound to atom id with bond, the position of new atom can be specified in pos or is
    decided calling find_place(),"""
    if pos != None:
      x, y = pos
    else:
      if bond_to_use:
        x, y = self.find_place( a1, self.paper.any_to_px( self.paper.standard.bond_length), added_order=bond_to_use.order)
      else:
        x, y = self.find_place( a1, self.paper.any_to_px( self.paper.standard.bond_length))
    a2 = self.create_new_atom( x, y)
    b = bond_to_use or bond( self.paper, order=1, type='n')
    b.atom1 = a1
    b.atom2 = a2
    self.insert_bond( b)
    b.draw()
    return a2, b

  def insert_bond( self, b):
    self.connect[ self.atoms.index( b.atom1)][ self.atoms.index( b.atom2)] = b
    self.connect[ self.atoms.index( b.atom2)][ self.atoms.index( b.atom1)] = b
    self.bonds.append( b)
    if not b.molecule:
      b.molecule = self

  def find_place( self, a, distance, added_order=1):
    """tries to find accurate place for next atom around atom 'id',
    returns x,y and list of ids of 'items' found there for overlap, those atoms are not bound to id"""
    ids_bonds = self.atoms_bound_to( a)
    if len( ids_bonds) == 0:
      x = a.x + cos( pi/6) *distance
      y = a.y - sin( pi/6) *distance
    elif len( ids_bonds) == 1:
      neigh = ids_bonds[0]
      if self.atoms_bonds( a)[0].order != 3 and added_order != 3:
        # we add a normal bond to atom with one normal bond
        if a == self._last_used_atom or len( self.atoms_bound_to( neigh)) != 2:
          # the user has either deleted the last added bond and wants it to be on the other side
          # or it is simply impossible to define a transoid configuration
          self.sign = -self.sign
          x = a.x + cos( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance
          y = a.y + sin( self.get_angle( a, ids_bonds[0]) +self.sign*2*pi/3) *distance
        else:
          # we would add the new bond transoid
          neighs2 = self.atoms_bound_to( neigh)
          neigh2 = (neighs2[0] == a) and neighs2[1] or neighs2[0]
          x = a.x + cos( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          y = a.y + sin( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          side = geometry.on_which_side_is_point( (neigh.x,neigh.y,a.x,a.y), (x,y))
          if side == geometry.on_which_side_is_point(  (neigh.x,neigh.y,a.x,a.y), (neigh2.x,neigh2.y)):
            self.sign = -self.sign
            x = a.x + cos( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
            y = a.y + sin( self.get_angle( a, neigh) +self.sign*2*pi/3) *distance
          self._last_used_atom = a
      else:
        x = a.x + cos( self.get_angle( a, ids_bonds[0]) + pi) *distance
        y = a.y + sin( self.get_angle( a, ids_bonds[0]) + pi) *distance
    else:
      x, y = self.find_least_crowded_place_around_atom( a, range=distance)
    return x, y

  def atoms_bonds( self, a):
    return filter( None,  self.connect[ self.atoms.index( a)])

  def atoms_bound_to( self, a):
    "returns list of ids of atoms bound to atom with id = 'id'"
    bonds = self.connect[ self.atoms.index( a)]
    ret = []
    for i in bonds:
      if i:
        ret.append( self.atoms[ bonds.index( i)])
    return ret

  def get_angle( self, a1, a2):
    "what is the angle between horizontal line through i1 and i1-i2 line"
    a = a2.x - a1.x
    b = a2.y - a1.y
    return atan2( b, a)
    
  def delete_items( self, items, redraw=1):
    """deletes items and also makes cleaning of orphan bonds and atoms"""
    if not items:
      return items, []     # quick way to avoid costly evaluation
    deleted = copy.copy( items)
    for o in items:
      if o.object_type == 'atom':
        self.delete_atom( o)
      else:
        self.delete_bond( o)
    if self.connect:
      # delete bonds that are not in connect anymore
      bonds_in_connect = []
      for i in range( len( self.connect)):
        for j in range( i+1, len( self.connect)):
          b = self.connect[i][j]
          if b:
            bonds_in_connect.append( b)
      deleted += [self.delete_bond( o) for o in misc.difference( self.bonds, bonds_in_connect)]
      # delete also orphan atoms
      deleted += [self.delete_atom( o) for o in self.atoms if not self.atoms_bonds( o)]
      # recalculation of second line of double bond position, optimized to do it only when realy
      # necessary, because its pretty expensive
      if redraw:
        bonds_to_redraw = []
        for b in deleted:
          if b.object_type == 'bond':
            for a in b.atoms:
              if a in self.atoms:
                bonds_to_redraw.extend( self.atoms_bonds( a))
        [o.redraw( recalc_side=1) for o in misc.filter_unique( bonds_to_redraw) if o.order == 2 and o.item]
        [o.decide_pos() for o in self.atoms if o.type == "element"]
        [o.redraw() for o in self.atoms]
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
    index = self.atoms.index( item)
    del self.connect[ index]
    for i in range( len( self.connect)):
      del self.connect[i][ index]
    self.atoms.remove( item)
    item.delete()
    if item == self.t_atom:
      t_atom = None
    if item == self.t_bond_first:
      t_bond_first = None
    if item == self.t_bond_second:
      t_bond_second = None
    return item

  def create_new_atom( self, x, y, name=None):
    a = atom( self.paper, xy=(x, y))
    self.insert_atom( a)
    if name:
      a.set_name( name)
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
    self.atoms.append( at)
    at.molecule = self
  

  def get_connected_components( self):
    """returns the connected components of graph in a form o list of lists of vertices"""
    comps = [] # all components
    comp = [] # just processed component 
    con = []  # connectivity matrix copy for fusion
    for line in self.connect:
      con.append( [(e and 1) or 0 for e in line])
    vs = copy.copy( self.atoms)
    while vs:
      if sum( con[0]) == 0:
        comp.append( vs.pop(0))
        comps.append( comp)
        comp = []
        del con[0]
        for line in con:
          del line[0]
        continue
      i = get_index_of_vertex_connected_to_first_vertex( con)
      fuse_vertices( 0, i, con)
      comp.append( vs.pop( i))
    return comps


  def check_integrity( self):
    """after deleting atoms or bonds it is important to see if it's needed to divide molecule to fragments
    and return them in form of list of new molecules"""
    if self.connect == []:
      return []
    old_map = copy.copy( self.atoms)
    # first distribute atoms to new_maps
    new_maps = self.get_connected_components()
    if len( new_maps) == 1:
      return []
    # reorder connectivity matrixes
    ret = []
    for mmap in new_maps:
      con = []
      bonds = []
      for i in range( len( mmap)):
        con.append( len( mmap)*[0])
      ## for bigger molecules it can be about 10x faster to iterate twice over the whole connect
      ## then only over the mmap, because this way we can save the index in many cases, which is pretty expensive
      for i in range( len( self.atoms)):
        for j in range( i+1, len( self.atoms)):
          bond = self.connect[i][j]
          if bond:
            try:
              i2 = mmap.index( self.atoms[i])
              j2 = mmap.index( self.atoms[j])
            except ValueError:
              continue
            con[i2][j2] = bond
            con[j2][i2] = bond
            bonds.append( bond)
      mol = molecule( self.paper)
      mol.feed_data( mmap, bonds, con)
      ret.append( mol)

    return ret

  def is_empty( self):
    return (self.connect == [])


  def read_package( self, package):
    self.name = package.getAttribute( 'name')
    if package.getAttribute( 'id'):
      self.id = package.getAttribute( 'id')
    for a in package.getElementsByTagName( 'atom'):
      self.insert_atom( atom( self.paper, package=a, molecule=self))
    self._id_map = [a.id for a in self.atoms]
    for b in package.getElementsByTagName( 'bond'):
      self.insert_bond( bond( self.paper, package = b, molecule=self))
    temp = package.getElementsByTagName('template')
    if temp:
      temp = temp[0]
      self.t_atom = self.paper.id_manager.get_object_with_id( temp.getAttribute( 'atom'))
      if temp.getAttribute('bond_first') and temp.getAttribute('bond_second'):
        self.t_bond_first = self.paper.id_manager.get_object_with_id( temp.getAttribute( 'bond_first'))
        self.t_bond_second = self.paper.id_manager.get_object_with_id( temp.getAttribute( 'bond_second'))
      self.next_to_t_atom = self.atoms_bound_to( self.t_atom)[0]


  def get_package( self, doc):
    mol = doc.createElement('molecule')
    mol.setAttribute( 'name', self.name)
    mol.setAttribute( 'id', self.id)
    if self.t_atom:
      if self.t_bond_second and self.t_bond_first:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.id)),
                                                        ('bond_first', str( self.t_bond_first.id)),
                                                        ('bond_second', str( self.t_bond_second.id))))
      else:
        dom_extensions.elementUnder( mol, 'template', ( ('atom', str( self.t_atom.id)),))
    for i in self.children:
      mol.appendChild( i.get_package( doc))
    return mol

  def draw( self, no_automatic=0):
    [a.draw( no_automatic=no_automatic) for a in self.bonds]
    [a.draw() for a in self.atoms]
    
  def bond_between( self, a1, a2):
    "returns id of bond between atoms i1 and i2"
    return self.connect[ self.atoms.index( a1)][ self.atoms.index( a2)]

  def handle_overlap( self):
    "deletes one of overlaping atoms and updates the bonds"
    to_delete = []
    bonds_to_check = [] # this can speedup the following for b in bonds_to_check by factor of 10 for big mols
    for i in range( len( self.atoms)):
      for j in range( i+1, len( self.atoms)):
        a = self.atoms[i]
        b = self.atoms[j]
        if (abs( a.x-b.x) < 4) and (abs( a.y-b.y) <4):
          if a not in to_delete:
            for x in self.atoms_bonds( b):
              x.change_atoms( b, a)
              bonds_to_check.append( x)
            to_delete.append( b)
    deleted = misc.filter_unique( to_delete)
    [self.delete_atom( o) for o in deleted]
    # after all is done, find and delete orphan bonds and update the others
    to_redraw = []
    for b in bonds_to_check:
      if not b in self.bonds:
        continue
      i1, i2 = map( self.atoms.index, b.atoms)
      recent_b = self.connect[i1][i2]
      if recent_b and recent_b != b:
        self.delete_bond( b)
        deleted.append( b)
        to_redraw.append( recent_b) # we redraw the once that remained
      elif not recent_b:
        self.connect[i1][i2] = b
        self.connect[i2][i1] = b
        to_redraw.append( b) # we redraw this also
    for b in to_redraw:
      b.redraw()

    return deleted

  def move( self, dx, dy):
    """moves the whole molecule"""
    for o in self.atoms +self.bonds:
      o.move( dx, dy)

  def bbox( self):
    items = []
    for a in self.atoms:
      items.append( a.item)
    return self.paper.list_bbox( items)


  def delete( self):
    [o.delete() for o in self.bonds+self.atoms]

  def redraw( self, reposition_double=0):
    for o in self.bonds:
      if o.order == 2:
        o.redraw( recalc_side=reposition_double)
      else:
        o.redraw()
    [o.redraw() for o in self.atoms]  

    
  def get_atoms_occupied_valency( self, atom):
    val = 0
    for b in self.atoms_bonds( atom):
        val += b.order
    return val

  def get_formula_dict( self):
    comp = PT.formula_dict()
    for a in self.atoms:
      comp += a.get_formula_dict()
    return comp

  def expand_groups( self, atoms=[]):
    """expands all group atoms; optional atoms selects atoms to expand - all used if not present"""
    names = self.paper.app.gm.get_template_names()
    if not atoms:
      map = copy.copy( self.atoms) # need to do that because the self.atoms gets changed during the cycle
    else:
      map = atoms # only selected atoms
    for a in map:
      if a.type == "group":
        if a.name in names:
          a2 = self.atoms_bound_to( a)[0]
          x1, y1 = a2.get_xy()
          x2, y2 = a.get_xy()
          t = self.paper.app.gm.get_transformed_template( names.index( a.name), (x1,y1,x2,y2), type='atom1')
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
    i = self.atoms.index( a1)
    l = self.atoms.index( a2)
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
    [o.lift() for o in self.bonds]
    [o.lift() for o in self.atoms]

  def find_least_crowded_place_around_atom( self, a, range=10):
    atms = self.atoms_bound_to( a)
    x, y = a.get_xy()
    if not atms:
      # single atom molecule
      if a.show_hydrogens and a.pos == "center-first":
        return x -range, y
      else:
        return x +range, y
    angles = [geometry.clockwise_angle_from_east( at.x-a.x, at.y-a.y) for at in atms]
    angles.append( 2*pi + min( angles))
    angles.sort()
    angles.reverse()
    diffs = misc.list_difference( angles)
    i = diffs.index( max( diffs))
    angle = (angles[i] +angles[i+1]) / 2
    return x +range*cos( angle), y +range*sin( angle)
    




  def flush_graph_to_file( self, name="/home/beda/oasa/oasa/mol.graph"):
    f = file( name, 'w')
    for a in self.atoms:
      f.write('%s ' % a.name)
    f.write('\n')
    for b in self.bonds:
      f.write('%d %d %d\n' % (b.order, self.atoms.index( b.atom1), self.atoms.index( b.atom2)))
    f.close()

  def transform( self, tr):
    """applies given transformation to its children"""
    for a in self.atoms:
      a.transform( tr)
    for b in self.bonds:
      b.transform( tr)


  def get_geometry( self):
    """returns a tuple of ((minx, miny, max, maxy), mean_bond_length)"""
    maxx, maxy, minx, miny = 4 * [None]
    for a2 in self.atoms:
      if not maxx or a2.x > maxx:
        maxx = a2.x
      if not minx or a2.x < minx:
        minx = a2.x
      if not miny or a2.y < miny:
        miny = a2.y
      if not maxy or a2.y > maxy:
        maxy = a2.y
    bond_lengths = []
    for b2 in self.bonds:
      bond_lengths.append( sqrt( (b2.atom1.x-b2.atom2.x)**2 + (b2.atom1.y-b2.atom2.y)**2))
    # rescale
    if bond_lengths:
      bl = sum( bond_lengths) / len( bond_lengths)
    else:
      bl = None
    return ((maxx,maxy,minx,miny),bl)




def get_index_of_vertex_connected_to_first_vertex( mat):
  """returns an index of vertex that is connected to the vertex in first line
  of the matrix"""
  for i, x in enumerate( mat[0]):
    if x:
      return i

def fuse_vertices( i1, i2, mat):
  """fuses vertices with indexes i1, i2 to i1, works on the mat"""
  # sum the lines
  for i in range( len( mat)):
    if i != i1:
      mat[i1][i] = mat[i1][i] or mat[i2][i]
  # remove i2
  del mat[i2]
  for line in mat:
    del line[i2]
  # copy row i1 to column i1
  for i, x in enumerate( mat[i1]):
    mat[i][i1] = x
