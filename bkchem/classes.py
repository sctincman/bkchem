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

"""set of basic classes such as atom, bond, molecule, text etc."""

from __future__ import division
from __future__ import generators

from math import atan2, sin, cos, pi, sqrt
import misc
import time
import geometry
from warnings import warn
from ftext import ftext
import dom_extensions
import xml.dom.minidom as dom
import operator
import tkFont
import data
import periodic_table as PT
import groups_table as GT
import copy
import helper_graphics as hg
import marks
from parents import meta_enabled, simple_parent


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


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

  def add_atom_to( self, a1, pos = None, bond_type=1):
    """adds new atom bound to atom id with bond, the position of new atom can be specified in pos or is
    decided calling find_place(),"""
    if pos != None:
      x, y = pos
    else:
      x, y = self.find_place( a1, self.paper.any_to_px( self.paper.standard.bond_length))
    a2 = self.create_new_atom( x, y)
    b = self.create_new_bond( a1, a2, bond_type=bond_type)
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
      [o.redraw( recalc_side=1) for o in self.bonds if o.type == 2 and o.item]
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
  
  def create_new_bond( self, a1, a2, bond_type=1):
    b = bond( self.paper, atoms=(a1, a2), type=bond_type)
    self.insert_bond( b)
    b.draw()
    return b

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
    map( lambda a: a.draw(), self)

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

  def redraw( self):
    [o.redraw() for o in self.bonds+self.atoms_map]
    
  def get_atoms_valency( self, atom):
    val = 0
    for b in self.atoms_bonds( atom):
      if b.type == 1 or b.type == 4 or b.type == 5:
        val += 1
      else:
        val += b.type
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
          a,b = self.add_atom_to( a) #, bond_type=self.__mode_to_bond_type())[0]]

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

  def flush_graph_to_file( self, name="/home/beda/oasa/graph/mol.graph"):
    f = file( name, 'w')
    for a in self.atoms_map:
      f.write('v')
    f.write('\n')
    for b in self.bonds:
      f.write('%d %d\n' % (self.atoms_map.index( b.atom1), self.atoms_map.index( b.atom2)))
    f.close()



### Class ATOM --------------------------------------------------
class atom( meta_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'atom'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo meta infos
  meta__undo_simple = ('x', 'y', 'z', 'pos', 'show', 'name', 'molecule', 'font_family',
                       'font_size', 'charge', 'show_hydrogens', 'type', 'line_color', 'area_color')
  meta__undo_copy = ('marks',)
  meta__undo_children_to_record = ('marks',)

  def __init__( self, paper, xy = (), package = None, molecule = None):
    meta_enabled.__init__( self, paper)
    # basic attrs
    self.molecule = molecule

    # presentation attrs
    self.selector = None
    self._selected = 0 #with ftext self.selector can no longer be used to determine if atom is selected
    self.item = None
    self.ftext = None
    if xy:
      self.set_xy( xy[0], xy[1])
    self.z = 0
    self.pos = None
    self.focus_item = None

    # chemistry attrs
    #   self.number = 0
    #   self.show_number = 0
    self.show_hydrogens = 0
    self.show = 0
    self.charge = 0
    self.marks = {'radical': None, 'biradical': None, 'electronpair': None,
                  'plus': None, 'minus': None}

    if package:
      self.read_package( package)
    else:
      self.set_name( 'C')

  def set_name( self, name, interpret=1, check_valency=1):
    # every time name is set the charge should be set to zero
    self.charge = 0
    # name should not be interpreted
    if not interpret:
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'
      return
    # try to interpret name
    if name.lower() != 'c':
      self.show = 1
    else:
      self.show = 0
    if name.capitalize() in PT.periodic_table:
      # name is element symbol
      self.name = name.capitalize()
      self.show_hydrogens = 0
      self.type = 'element'
    elif (name.lower() in GT.groups_table) and ( not check_valency or self.molecule.get_atoms_valency( self) == 1):
      # name is a known group
      self.name = GT.groups_table[ name.lower()]['name']
      self.show_hydrogens = 0
      self.type = 'group'
    else:
      # try other possibilities such as alkyl chain or atom with hydrogens
      # try if name is hydrogenated form of an element
      form = PT.text_to_hydrogenated_atom( name)
      if form:
        # it is!
        a = form.keys()
        a.remove( 'H')
        valency = self.molecule.get_atoms_valency( self)
        if form['H'] in [i-valency+self.charge for i in PT.periodic_table[a[0]]['valency']]:
          self.name = a[0]
          self.show_hydrogens = 1
          self.type = 'element'
          return
      # try if the name is an alkyl chain such as c6h13
      form = PT.formula_dict( name.upper())
      if form.is_saturated_alkyl_chain():
        self.name = str( form)
        self.show_hydrogens = 1
        self.type = 'chain'
        return
      # its nothing interesting - just text
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'

  def get_text( self):
    if self.type in ('text', 'group'):
      return self.name
    elif self.type == 'element' and not self.show:
      return self.name
    elif self.type == 'element' and self.show:
      ret = self.name
      # hydrogens
      if self.show_hydrogens:
        v = self.get_free_valency()
        if v:
          h = 'H'
        else:
          h = ''
        if v > 1:
          h += '%d' % v
        if self.pos == 'center-last':
          ret = h + ret
        else:
          ret = ret + h
      # charge
      if self.charge:
        ch = ''
        if abs( self.charge) > 1:
          ch += str( abs( self.charge))
        if self.charge > 0:
          ch += '+'
        else:
          ch += '-'
      else:
        ch = ''
      if self.pos == 'center-last':
        return ch + ret
      else:
        return ret + ch
    elif self.type == 'chain':
      return PT.formula_dict( self.name).__str__( reverse=(self.pos=='center-last'))

  def get_ftext( self):
    if self.type == 'text':
      return self.name
    elif self.type == 'group':
      if self.pos == 'center-first':
        return GT.groups_table[ self.name.lower()]['textf']
      else:
        return GT.groups_table[ self.name.lower()]['textb']
    elif self.type == 'element':
      ret = self.name
      # hydrogens
      if self.show_hydrogens:
        v = self.get_free_valency()
        if v:
          h = 'H'
        else:
          h = ''
        if v > 1:
          h += '<sub>%d</sub>' % v
        if self.pos == 'center-last':
          ret = h + ret
        else:
          ret = ret + h
      # charge
      if self.charge:
        ch = ''
        if abs( self.charge) > 1:
          ch += str( abs( self.charge))
        if self.charge > 0:
          ch = '<sup>%s+</sup>' % ch
        else:
          ch = '<sup>%s-</sup>' % ch
      else:
        ch = ''
      if self.pos == 'center-last':
        return ch + ret
      else:
        return ret + ch
    elif self.type == 'chain':
      return PT.formula_dict( self.name).get_html_repr_as_string( reverse=(self.pos=='center-last'))

  # properties
  #name = property( get_name, set_name)

  def set_molecule( self, molecule):
    self.molecule = molecule

  def set_xy( self, x, y):
    self.x = x #round( x, 2)
    self.y = y #round( y, 2)

  def decide_pos( self):
    as = self.molecule.atoms_bound_to( self)
    p = 0
    for a in as:
      if a.get_x() < self.x:
        p -= 1
      elif a.get_x() > self.x:
        p += 1
    if p > 0:
      self.pos = 'center-last'
    else:
      self.pos = 'center-first'

  def draw( self):
    "draws atom with respect to its properties"
    if self.item:
      warn( "drawing atom that is probably drawn", UserWarning, 2)
    x, y = self.x, self.y
    if self.show:
      self.update_font()
      if not self.pos:
        self.decide_pos()
      parsed_name = dom.parseString( '<ftext>%s</ftext>' % self.get_ftext()).childNodes[0]
      self.ftext = ftext( self.paper, xy=(self.x, self.y), dom=parsed_name, font=self.font, pos=self.pos, fill=self.line_color)
      self.ftext.draw()
      x1, y1, x2, y2 = self.ftext.bbox()
      self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('atom'))
      ## shrink the selector to improve appearance (y2-(y2-y1)//4+1)
      self.selector = self.paper.create_rectangle( x1, y1, x2, y2-(y2-y1)//4+1, fill=self.area_color, outline='',tags='helper_a')
      self.ftext.lift()
      self.paper.lift( self.item)
    else:
      self.item = self.paper.create_line( x, y, x, y, tags=("atom", 'nonSVG'))
      self.selector = None
    [m.draw() for m in self.marks.itervalues() if m]
    self.paper.register_id( self.item, self)

  def redraw( self):
    self.update_font()
    # at first we delete everything...
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self. selector)
    if self.ftext:
      self.ftext.delete()
    self.item = None # to ensure that warning in draw() is not triggered when redrawing
    [m.delete() for m in self.marks.itervalues() if m]
    # ...then we draw it again
    self.draw()
    if self._selected:
      self.select()
    else:
      self.unselect()
      
  def focus( self):
    if self.show:
      self.paper.itemconfig( self.selector, fill='grey')
    else:
      x, y = self.x, self.y
      self.focus_item = self.paper.create_oval( x-4, y-4, x+4, y+4, tags='helper_f')
      self.paper.lift( self.item)

  def unfocus( self):
    if self.show:
      self.paper.itemconfig( self.selector, fill=self.area_color)
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None

  def select( self):
    if self.show:
      self.paper.itemconfig( self.selector, outline='black')
    else:
      x, y = self.x, self.y
      if self.selector:
        self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
      else:
        self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2)
      self.paper.lower( self.selector)
    self._selected = 1

  def unselect( self):
    if self.show:
      self.paper.itemconfig( self.selector, outline='')
      #self.paper.lower( self.selector)
    else:
      self.paper.delete( self.selector)
      self.selector = None
    self._selected = 0

  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move( dx, dy)
    for m in self.marks:
      if self.marks[m]:
        self.marks[m].move( dx, dy)

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    #self.set_xy( x, y)
    self.move( dx, dy)

  def get_x( self):
    return self.x

  def get_y( self):
    return self.y

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

  def round_coords( self, precision=0):
    self.x = round( self.x, precision)
    self.y = round( self.y, precision)

  def delete( self):
    for m in self.marks:
      if self.marks[m]:
        self.marks[m].delete()
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.unselect()
      if self.show:
        self.paper.delete( self.selector)
        self.selector = None
        self._selected = 0
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None
    if self.ftext:
      self.ftext.delete()
    return self

  def read_package( self, package):
    a = ['no','yes']
    on_off = ['off','on']
    self._cdml_id = package.getAttribute( 'id')
    #self.show_number = a.index( package.getAttribute( 'show_number'))
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = self.paper.read_xml_point( position)
    if z != None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.set_xy( x, y)
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name( reduce( operator.add, [e.toxml() for e in ft[0].childNodes], ''), check_valency=0, interpret=0)
    else:
      self.set_name( package.getAttribute( 'name'), check_valency=0)
    if package.getAttribute( 'hydrogens'):
      self.show_hydrogens = on_off.index( package.getAttribute('hydrogens'))
    else:
      self.show_hydrogens = 0
    # font and fill color
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    # show
    if package.getAttribute( 'show'):
      self.show = a.index( package.getAttribute( 'show'))
    else:
      self.show = (self.name!='C')
    # background color
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # marks
    for m in package.getElementsByTagName( 'mark'):
      auto = (m.getAttribute( 'auto') != None and m.getAttribute( 'auto')) or 0
      type = m.getAttribute( 'type')
      x, y, z = self.paper.read_xml_point( m)
      self.marks[ type] = marks.__dict__[ type]( self.paper,
                                                 x, y,
                                                 atom=self,
                                                 auto= int(auto))
                          


  def get_package( self, doc):
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('atom')
    a.setAttribute( 'id', str( self.get_cdml_id()))
    #show attribute is set only when non default
    if (self.show and self.name=='C') or (not self.show and self.name!='C'): 
      a.setAttribute('show', y[ self.show])
    if self.show:
      a.setAttribute( 'pos', self.pos)
    if self.font_size != 12 or self.font_family != 'helvetica' or self.line_color != '#000':
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != '#000':
        font.setAttribute( 'color', self.line_color)
    if self.type == 'text':
      a.appendChild( dom.parseString( '<ftext>%s</ftext>' % self.name).childNodes[0])
    else:
      a.setAttribute( 'name', self.name)
      if self.show_hydrogens:
        a.setAttribute('hydrogens', on_off[self.show_hydrogens])
    if self.area_color != "#ffffff":
      a.setAttribute( 'background-color', self.area_color)
    # needed to support transparent handling of molecular size
    x, y, z = map( self.paper.px_to_text_with_unit, self.get_xyz( real=1))
    if self.z:
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y), ('z', z)))
    else: 
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y)))
    for m, o in self.marks.items():
      if self.marks[m]:
        x ,y = map( self.paper.px_to_text_with_unit, (o.x, o.y))
        dom_extensions.elementUnder( a, 'mark', attributes=(('type', m),
                                                            ('x', x),
                                                            ('y', y),
                                                            ('auto', str( o.auto))))
    return a

  def get_cdml_id( self):
    if self.item:
      self._cdml_id = 'a'+str( self.item)
    return self._cdml_id

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

  def get_free_valency( self):
    """returns free valency of atom."""
    if self.type != 'element':
      return 0
    valency = self.molecule.get_atoms_valency( self)
    if self.name in PT.periodic_table:
      vals = PT.periodic_table[ self.name]['valency']
      for v in vals:
        # should we increase or decrease valency with charge ?
        if self.charge:
          if abs( self.charge) > 1:
            # charges higher than one should always decrease valency
            charge = abs( self.charge)
          elif (self.name in PT.accept_cation) and (self.charge == 1) and (valency-1 <= PT.accept_cation[self.name]):
            # elements that can accept cations to increase their valency (NH4+)
            charge = -1
          elif (self.name in PT.accept_anion) and (self.charge == -1) and (valency-1 <= PT.accept_anion[self.name]):
            # elements that can accept anions to increase their valency (BH4-)
            charge = -1
          else:
            # otherwise charge reduces valency 
            charge = abs( self.charge)
        else:
          charge = 0
        if valency+charge <= v:
          return v-valency-charge
      # if valency is exceeded return lowest possible negative value
      return max( PT.periodic_table[ self.name]['valency']) - valency - charge
    # if unsuccessful return 0
    return 0
    
  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    if self.type == 'text':
      return PT.formula_dict()
    elif self.type == 'group':
      return PT.formula_dict( GT.groups_table[ self.name.lower()]['composition'])
    elif self.type == 'element':
      ret = PT.formula_dict( self.name)
      free_val = self.get_free_valency()
      if free_val > 0:
        ret['H'] = free_val
      return ret
    elif self.type == 'chain':
      return PT.formula_dict( self.name)

  def atoms_bound_to( self):
    """just link to molecule.atoms_bound_to()"""
    return self.molecule.atoms_bound_to( self)

  def lift( self):
    for m in self.marks.itervalues():
      if m:
        m.lift()
    if self.selector:
      self.paper.lift( self.selector)
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)

  def set_mark( self, mark='radical', toggle=1, angle='auto'):
    if mark in self.marks:
      if toggle:
        if self.marks[ mark]:
          self.marks[ mark].delete()
          self.marks[ mark] = None
        else:
          self.create_mark( mark=mark, angle=angle)
      else:
        if not self.marks[ mark]:
          self.create_mark( mark=mark, angle=angle)

  def create_mark( self, mark='radical', angle='auto'):
    if self.show:
      dist = self.font_size/2 + round( marks.__dict__[ mark].standard_size/2) + 2
    else:
      dist = 5 + round( marks.__dict__[ mark].standard_size / 2)
    if angle == 'auto':
      x, y = self.molecule.find_least_crowded_place_around_atom( self, range=dist)
      #ang = round( geometry.clockwise_angle_from_east( x -self.x, y -self.y))
    else:
      x = self.x + round( cos( angle) *dist)
      y = self.y + round( sin( angle) *dist)
      #ang = angle

    self.marks[ mark] = marks.__dict__[ mark]( self.paper, x, y,
                                               atom = self,
                                               auto=(angle=='auto'))
    self.marks[ mark].draw()

  def reposition_marks( self):
    for m in self.marks.itervalues():
      if m and m.auto:
        if self.show:
          dist = self.font_size/2 + round( m.size/2) + 2
        else:
          dist = 5 + round( m.size / 2)
        x, y = self.molecule.find_least_crowded_place_around_atom( self, range=dist)
        m.move_to( x, y)
        

# class BOND--------------------------------------------------
class bond( meta_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'bond'
  # these values will be automaticaly read from paper.standard on __init__
  # bond_width couldn't be because it has sign that is important
  # widths need to be calculated therefore are also not here (to be fixed)
  meta__used_standard_values = ['line_color','double_length_ratio']
  # undo related metas
  meta__undo_simple = ('atom1', 'atom2', 'type', 'line_width', 'center', 'bond_width',
                       'molecule', 'line_color','double_length_ratio')


  def __init__( self, paper, atoms=(), package=None, molecule=None, type=1):
    self.type = type
    meta_enabled.__init__( self, paper)
    self.item = None
    self.second = None
    self.third = None
    self.items = []
    self.molecule = molecule
    if atoms:
      self.atom1, self.atom2 = atoms
    self.selector = None

    # implicit values
    self.center = 0

    if package:
      self.read_package( package)

  def read_standard_values( self, old_standard=None):
    meta_enabled.read_standard_values( self, old_standard=old_standard)
    # wedge width or ...
    if self.type in (4,5):
      if not old_standard or (self.paper.standard.wedge_width != old_standard.wedge_width):
        self.bond_width = self.paper.any_to_px( self.paper.standard.wedge_width)
    # ... bond width
    else:
      if not old_standard or (self.paper.standard.bond_width != old_standard.bond_width):
        if 'bond_width' in self.__dict__:
          self.bond_width = misc.signum( self.bond_width) *self.paper.any_to_px( self.paper.standard.bond_width)
        else:
          self.bond_width = self.paper.any_to_px( self.paper.standard.bond_width)
    # line width
    if not old_standard or (self.paper.standard.line_width != old_standard.line_width):
      self.line_width = self.paper.any_to_px( self.paper.standard.line_width)

  def set_molecule( self, molecule):
    self.molecule = molecule

  def draw( self):
    """call the appropriate draw method"""
    if self.item:
      warn( "drawing bond that is probably drawn already", UserWarning, 2)
    type = data.bond_type_remap[ self.type]
    self.__class__.__dict__[ '_draw_'+type]( self)

  def _draw_1s( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    #MB# x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    # main item
    self.item = self.paper.create_line( (x1, y1, x2, y2), tags=('bond',), width=self.line_width, fill=self.line_color, capstyle="round")
    # draw helper items
    self.second = self.third = None
    self.paper.register_id( self.item, self)
    return x1,y1,x2,y2

  def _draw_2s( self):
    x1,y1,x2,y2 = self._draw_1s()
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    # double
    if self.center:
      self.paper.itemconfig( self.item, fill='')
      d = int( round( d/3))
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d)
    # shortening of the second bond
    dx = x-x0
    dy = y-y0
    if self.center:
      _k = 0
    else:
      _k = (1-self.double_length_ratio)/2
    self.second = self.paper.create_line( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy, width=self.line_width, fill=self.line_color)
    if self.center:
      self.third = self.paper.create_line( 2*x1-x, 2*y1-y, 2*x2-x0, 2*y2-y0, width=self.line_width, fill=self.line_color)

  def _draw_3s( self):
    x1,y1,x2,y2 = self._draw_1s()
    if self.center == None or self.bond_width == None:
      self._decide_distance_and_center()
    d = self.bond_width
    _k = (1-self.double_length_ratio)/2
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, d*3/4)
    dx = x-x0
    dy = y-y0
    self.second = self.paper.create_line( x-_k*dx, y-_k*dy, x0+_k*dx, y0+_k*dy, width=self.line_width, fill=self.line_color)
    self.third = self.paper.create_line( 2*x1-x-_k*dx, 2*y1-y-_k*dy, 2*x2-x0+_k*dx, 2*y2-y0+_k*dy, width=self.line_width, fill=self.line_color)
    

  def _draw_1h( self):
    x1,y1,x2,y2 = self._draw_1s()    
    # main item
    self.paper.itemconfig( self.item, fill='')
    # the small lines
    step_size = 5
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.bond_width)
    d = sqrt( (x1-x2)**2 + (y1-y2)**2) # length of the bond
    dx1 = -(x1 - x0)/d
    dy1 = -(y1 - y0)/d
    dx2 = -(x1 -2*x2 +x0)/d
    dy2 = -(y1 -2*y2 +y0)/d
    for i in range( 1, int( round( d/ step_size))+1):
      coords = [x1+dx1*i*step_size, y1+dy1*i*step_size, x1+dx2*i*step_size, y1+dy2*i*step_size]
      coords = map( round, coords)
      if coords[0] == coords[2] and coords[1] == coords[3]:
        if (dx1+dx2) > (dy1+dy2): 
          coords[0] += 1
        else:
          coords[1] += 1
      self.items.append( self.paper.create_line( coords, width=self.line_width, fill=self.line_color))

  def _draw_1w( self):
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    # main item
    x, y, x0, y0 = geometry.find_parallel( x1, y1, x2, y2, self.bond_width)
    self.item = self.paper.create_polygon( (x1, y1, x0, y0, 2*x2-x0, 2*y2-y0), tags=('bond',), outline=self.line_color, fill=self.line_color, joinstyle="miter")
    # draw helper items
    self.second = self.third = None
    self.paper.register_id( self.item, self)
    
  def redraw( self, recalc_side=0):
    if recalc_side:
      self._decide_distance_and_center()
    sel = self.selector
    if self.item:
      self.delete()
    self.draw()
    # reselect
    if sel:
      self.select()

  def simple_redraw( self):
    """very fast redraw that draws only a simple line instead of the bond,
    used in 3d rotation only (as for bkchem 0.5.0)"""
    if self.second:
      self.paper.delete( self.second)
      self.second = None
    if self.third:
      self.paper.delete( self.third)
      self.third = None
    if self.items:
      map( self.paper.delete, self.items)
      self.items = []
    x1, y1 = self.atom1.get_xy()
    x2, y2 = self.atom2.get_xy()
    x1, y1, x2, y2 = map( round, [x1, y1, x2, y2])
    self.paper.coords( self.item, x1, y1, x2, y2)
    self.paper.itemconfig( self.item, width = self.line_width, fill=self.line_color)
    

  def focus( self):
    if self.type in (1,2,3):
      items = [self.item]
      if self.second:
        items += [self.second]
      if self.third:
        items += [self.third]
      [self.paper.itemconfig( item, width = self.line_width+2) for item in items]
    elif self.type == 5:
      [self.paper.itemconfig( item, width = self.line_width+2) for item in self.items]
    elif self.type == 4:
      self.paper.itemconfigure( self.item, fill='white')

  def unfocus( self):
    if self.type in (1,2,3):
      if not self.item:
        return
      items = [self.item]
      if self.second:
        items += [self.second]
      if self.third:
        items += [self.third]
      [self.paper.itemconfig( item, width = self.line_width) for item in items]
    elif self.type == 5:
      [self.paper.itemconfig( item, width = self.line_width) for item in self.items]
    elif self.type == 4:
      self.paper.itemconfigure( self.item, fill=self.line_color)

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
    #self.redraw()  # changed for speed, reduces time needed to move objects to 1/2 
    b = [self.item]
    if self.second:
      b.append( self.second)
    if self.third:
      b.append( self.third)
    if self.selector:
      b.append( self.selector)
    if self.items:
      b.extend( self.items)
    [self.paper.move( o, dx, dy) for o in b]
      
  def delete( self):
    self.unselect()
    items = []
    if self.item:
      items += [self.item]
      self.paper.unregister_id( self.item)
      self.item = None
    if self.second:
      items += [self.second]
      self.second = None
    if self.third:
      items += [self.third]
      self.third = None
    if self.items:
      items.extend( self.items)
      self.items = []
    map( self.paper.delete, items)
    self.item = None
    return self

  def read_package( self, package):
    b = ['no', 'yes']
    type = package.getAttribute( 'type')
    if type:
      if type == 'forth':
        self.type = 4
      else:
        for type_set in ('bond_types', 'alternative_bond_types', 'numbered_bond_types'):
          if type in data.__dict__[type_set]:
            self.type = data.__dict__[type_set].index( type)
    else:
      self.type = 1
    # implied
    if package.getAttribute( 'distance'):
      self.bond_width = float( package.getAttribute( 'distance')) * self.paper.real_to_screen_ratio()
    else:
      self.bond_width = None
    if package.getAttribute( 'width'):
      self.line_width = float( package.getAttribute( 'width'))
    if package.getAttribute( 'center'):
      self.center = b.index( package.getAttribute( 'center'))
    else:
      self.center = None
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'double_ratio'):
      self.double_length_ratio = float( package.getAttribute( 'double_ratio'))
    # end of implied
    self.atom1 = self.molecule.get_atom_with_cdml_id( package.getAttribute( 'start'))
    self.atom2 = self.molecule.get_atom_with_cdml_id( package.getAttribute( 'end'))      
  
  def get_package( self, doc):
    a = data.alternative_bond_types
    b = ['no', 'yes']
    bnd = doc.createElement('bond')
    dom_extensions.setAttributes( bnd, (('type', a[self.type]),
                                        ('width', str( self.line_width)),
                                        ('start', self.atom1.get_cdml_id()),
                                        ('end', self.atom2.get_cdml_id()),
                                        ('double_ratio', str( self.double_length_ratio))))
    if self.type != 1:
      bnd.setAttribute( 'distance', str( self.bond_width  * self.paper.screen_to_real_ratio()))
      if self.type == 2:
        bnd.setAttribute( 'center', b[ self.center])
    if self.line_color != '#000':
      bnd.setAttribute( 'color', self.line_color)
    return bnd

  def toggle_type( self, only_shift = 0, to_type='normal'):
    if to_type == 'wedge':
      if self.type == 4:
        # if already wedge - change the start and end
        self.atom1, self.atom2 = self.atom2, self.atom1
      else:
        # toggle to up
        if self.type != 5:
          self.bond_width = self.paper.any_to_px( self.paper.standard.wedge_width)
        self.type = 4
    elif to_type == 'hatch':
      if self.type == 5:
        # if already hatch - change the start and end
        self.atom1, self.atom2 = self.atom2, self.atom1
      else:
        # toggle to back
        if self.type != 4:
          self.bond_width = self.paper.any_to_px( self.paper.standard.wedge_width)
        self.type = 5
    else:
      if self.type not in (1,2,3):
        self.type = 1
        self.bond_width = self.paper.any_to_px( self.paper.standard.bond_width)
      else:
        if only_shift:
          if self.center:
            self.bond_width = -self.bond_width
            self.center = 0
          elif self.bond_width > 0:
            self.bond_width = -self.bond_width
          else:
            self.center = 1
        else:
          if self.type == 3:
            # was type 3
            self.type = 1
          elif self.type == 1:
            # was type 1
            self.type += 1
            self._decide_distance_and_center()
          else:
            # was type 2
            self.type = self.type +1
    self.redraw()

  def _decide_distance_and_center( self):
    """according to molecular geometry decide what bond.center and bond.bond_width should be"""
    atms = self.molecule.atoms_bound_to( self.atom1) + self.molecule.atoms_bound_to( self.atom2)
    atms = misc.difference( atms, [self.atom1, self.atom2])
    coords = [a.get_xy() for a in atms]
    line = self.atom1.get_xy() + self.atom2.get_xy()
    if not self.bond_width:
      length = sqrt((line[0]-line[2])**2  + (line[1]-line[3])**2)
      self.bond_width = round( length / 5, 1)
    # does not need to go further if the bond is not double
    # the str is to support the future notation for bond types
    if not '2' in str( self.type):
      return 

    # searching for circles

    plus_side1 = [a for a in self.atom1.atoms_bound_to() if geometry.on_which_side_is_point( line, a.get_xy()) == 1 and a!=self.atom2]
    plus_side2 = [a for a in self.atom2.atoms_bound_to() if geometry.on_which_side_is_point( line, a.get_xy()) == 1 and a!=self.atom1]
    minus_side1 = [a for a in self.atom1.atoms_bound_to() if geometry.on_which_side_is_point( line, a.get_xy()) == -1 and a!=self.atom2]
    minus_side2 = [a for a in self.atom2.atoms_bound_to() if geometry.on_which_side_is_point( line, a.get_xy()) == -1 and a!=self.atom1]
    plus_side = ( plus_side1, plus_side2)
    minus_side = ( minus_side1, minus_side2)

    circles = 0

    if ( len( plus_side1) and len( plus_side2)) or ( len( minus_side1) and len( minus_side2)):
      # only when there are enough atoms in neighborhood we need to search for circles
      import copy
      
      def accessible( a1, a2, d):
        """is a2 accessible from a1 through d?"""
        if a1 == a2:
          return 1
        d.remove( a1)
        if a2 in a1.molecule.atoms_bound_to( a1):
          return 1
        else:
          for a in a1.molecule.atoms_bound_to( a1):
            if a in d and accessible( a, a2, d):
              return 1
        return 0

      def get_circles_for_side( side):
        res = 0
        side1, side2 = side
        while len( side1):
          a1 = side1.pop(0)
          for a2 in side2:
            atoms = copy.copy( self.molecule.atoms_map)
            atoms.remove( self.atom1)
            atoms.remove( self.atom2)
            if accessible( a1, a2, atoms):
              res += 1
        return res

      circles = get_circles_for_side( plus_side) - get_circles_for_side( minus_side)
    # end of circles search

    if circles:
      side = circles
    else:
      sides = [geometry.on_which_side_is_point( line, xy) for xy in coords]
      side = reduce( operator.add, sides, 0)
    # on which side to put the second line
    if side == 0 and (len( self.molecule.atoms_bound_to( self.atom1)) == 1 or len( self.molecule.atoms_bound_to( self.atom2)) == 1):
      # maybe we should center, but this is usefull only when one of the atoms has no other substitution
      self.center = 1
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
        self.center = 0
        self.bond_width = -abs( self.bond_width)
      else:
        self.center = 0
        self.bond_width = abs( self.bond_width)
    

  def get_atoms( self):
    return self.atom1, self.atom2

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
    return self.paper.bbox( self.item)

  def lift( self):
    [self.paper.lift( i) for i in self.items]
    if self.selector:
      self.paper.lift( self.selector)
    if self.second:
      self.paper.lift( self.second)
    if self.third:
      self.paper.lift( self.third)
    if self.item:
      self.paper.lift( self.item)


##-------------------- STANDARD CLASS ------------------------------

class standard:

  def __init__( self):
    # common
    self.line_width = '1px'
    self.font_size = 12
    self.font_family = 'helvetica'
    self.line_color = "#000"
    self.area_color = '#ffffff'
    # bond
    self.bond_length = '1cm'
    self.bond_width = '6px'
    self.wedge_width = '3px'
    self.double_length_ratio = 0.75
    # arrow
    self.arrow_length = '1.6cm'
    # paper
    self.paper_type = 'A4'
    self.paper_orientation = 'portrait'
    self.paper_crop_svg = 0


  def __eq__( self, other):
    for (k,v) in self.__dict__.iteritems():
      if str( v) != str( other.__dict__[ k]):
        return 0
    return 1

  def __ne__( self, other):
    return not self.__eq__( other)


  def get_package( self, doc):
    ret = doc.createElement( 'standard')
    dom_extensions.setAttributes( ret, (('line_width', str( self.line_width)),
                                        ('font_size', str( self.font_size)),
                                        ('font_family', str( self.font_family)),
                                        ('line_color', self.line_color),
                                        ('area_color', self.area_color),
                                        ('paper_type', self.paper_type),
                                        ('paper_orientation', self.paper_orientation),
                                        ('paper_crop_svg', str( self.paper_crop_svg))))
    dom_extensions.elementUnder( ret, 'bond', (('length', str( self.bond_length)),
                                               ('width', str( self.bond_width)),
                                               ('wedge-width', str( self.wedge_width)),
                                               ('double-ratio', str( self.double_length_ratio))))
    dom_extensions.elementUnder( ret, 'arrow', (('length', str( self.arrow_length)),))
    return ret

  def read_package( self, p):
    for attr in ('line_width', 'font_size', 'font_family', 'line_color','area_color',
                 'paper_crop_svg','paper_orientation','paper_type'):
      if p.getAttribute( attr):
        self.__dict__[ attr] = p.getAttribute( attr)
    self.font_size = int( self.font_size)
    self.paper_crop_svg = int( self.paper_crop_svg)
    b = dom_extensions.getFirstChildNamed( p, 'bond')
    if b:
      self.bond_length = b.getAttribute( 'length') or self.bond_length
      self.bond_width = b.getAttribute( 'width') or self.bond_width
      self.double_length_ratio = b.getAttribute( 'double-ratio') or self.double_length_ratio
      self.double_length_ratio = float( self.double_length_ratio)
      self.wedge_width = b.getAttribute( 'wedge-width') or self.wedge_width
    a = dom_extensions.getFirstChildNamed( p, 'arrow')
    if a:
      self.arrow_length = a.getAttribute( 'length')
      
    

##-------------------- ARROW CLASS ------------------------------

class arrow( meta_enabled):
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
  meta__undo_simple = ('pin', 'spline', 'line_width', 'line_color')
  meta__undo_copy = ('points',)
  meta__undo_children_to_record = ('points',)

  def __init__( self, paper, points=[], shape=(8,10,3), pin=1, spline=0, package=None, fill="#000"):
    meta_enabled.__init__( self, paper)
    self.points = []
    self.spline = spline
    self.paper = paper
    self.shape = shape
    self.item = None
    self.pin = 1
    if points:
      for p in points:
        pnt = point( self.paper, p[0], p[1], arrow=self)
        self.points.append( pnt)
    if package:
      self.read_package( package)

  def read_standard_values( self, old_standard=None):
    meta_enabled.read_standard_values( self, old_standard=old_standard)
    if not old_standard or (self.paper.standard.line_width != old_standard.line_width):
      self.line_width = self.paper.any_to_px( self.paper.standard.line_width)    
    
  def draw( self):
    if len( self.points) > 1:
      #type = self.spline and 'circle' or 'invisible'
      type = 'invisible'
      for p in self.points:
        p.type = type
      [pnt.draw() for pnt in self.points]
      ps = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
      self.item = self.paper.create_line( ps, tags='arrow', arrow=self._pins[ self.pin], arrowshape=self.shape,\
                                          width=self.line_width, smooth=self.spline, fill=self.line_color)
      self.paper.register_id( self.item, self)
    
  def redraw( self):
    if not self.item:
      self.draw()
    else:
      if len( self.points) > 1:
        #type = self.spline and 'circle' or 'invisible'
        type = 'invisible'
        [pnt.change_type( type) for pnt in self.points]
        ps = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
        self.paper.coords( self.item, ps)
        self.paper.itemconfig( self.item, arrow=self._pins[ self.pin], arrowshape=self.shape,\
                               width=self.line_width, smooth=self.spline, fill=self.line_color)

  def focus( self):
    self.paper.itemconfig( self.item, width = self.line_width+2)

  def unfocus( self):
    self.paper.itemconfig( self.item, width = self.line_width)

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
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    self.item = None

  def is_empty_or_single_point( self):
    return len( self.points) < 2 

  def move( self, dx, dy):
    [p.move( dx, dy) for p in self.points]
    self.redraw()

  def read_package( self, package):
    a = ['no', 'yes']
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
    a = ['no', 'yes']
    arr = doc.createElement('arrow')
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
                                        ('color', str( self.line_color))))
    for p in self.points:
      arr.appendChild( p.get_package( doc))
    return arr

  def change_direction( self):
    self.pin += 1
    if self.pin > 3:
      self.pin = 0
    self.redraw()

  def bbox( self):
    return self.paper.bbox( self.item)

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
    if self.item:
      self.paper.lift( self.item)
    [o.lift() for o in self.points]

  def get_shape_defining_children( self):
    for i in self.points:
      yield i


## -------------------- POINT CLASS ------------------------------

class point( simple_parent):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'point'

  # undo related metas
  meta__undo_simple = ('x','y')

  def __init__( self, paper, xy=(), arrow=None, package=None, type='invisible'):
    if xy:
      self.x, self.y = xy
    self.paper = paper
    self.item = None
    self.focus_item = None
    self.selector = None
    self.type = type
    if arrow:
      self.arrow = arrow
    if package:
      self.read_package( package)

  def set_arrow( self, arrow):
    self.arrow = arrow

  def draw( self):
    if self.item:
      self.redraw()
    else:
      if self.type == 'invisible':
        self.item = self.paper.create_line( self.x, self.y, self.x, self.y, tags='point')
      elif self.type == 'circle':
        self.item = self.paper.create_oval( self.x-2, self.y-2, self.x+2, self.y+2, fill='grey', outline='grey', tags='point')
      else:
        warn( 'unknown point type')
        return 
      self.paper.register_id( self.item, self)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      self.paper.delete( self.item)
      self.item = None
      self.draw()
      if self.selector:
        self.paper.coords( self.selector, self.x-2, self.y-2, self.x+2, self.y+2)

  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    if not self.item:
      self.x = x
      self.y = y
      self.draw()
    else:
      dx = x -self.x
      dy = y -self.y
      self.move( dx, dy)

  def focus( self):
    self.focus_item = self.paper.create_oval( self.x-4, self.y-4, self.x+4, self.y+4)
    if self.item:
      self.paper.lift( self.item)

  def unfocus( self):
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None

  def select( self):
    if not self.selector:
      self.selector = self.paper.create_rectangle( self.x-2, self.y-2, self.x+2, self.y+2)
      self.paper.lower( self.selector)

  def unselect( self):
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    
  def get_xy( self):
    return self.x, self.y

  def delete( self):
    self.unselect()
    self.unfocus()
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None

  def read_package( self, package):
    x, y, z = self.paper.read_xml_point( package)
    self.x, self.y = self.paper.real_to_screen_coords( (x,y))
    #self.z = int( package.getAttribute( 'z') )
  
  def get_package( self, doc):
    pnt = doc.createElement('point')
    x, y = map( self.paper.px_to_text_with_unit, self.paper.screen_to_real_coords( (self.x, self.y)))
    dom_extensions.setAttributes( pnt, (('x', x),
                                        ('y', y)))
    return pnt

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

  def change_type( self, type):
    self.type = type
    self.redraw()


##-------------------- PLUS CLASS ------------------------------

class plus( meta_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'plus'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_family']
  # undo related metas
  meta__undo_simple = ('x', 'y', 'font_size', 'font_family', 'line_color','area_color')

  def __init__( self, paper, xy=(), package=None):
    meta_enabled.__init__( self, paper)
    self.x = self.y = None
    self.focus_item = None
    self.selector = None
    self._selected = 0
    if package:
      self.read_package( package)
    if xy:
      self.x, self.y = xy
    # standard values
    self.font_size = 20
    self.update_font()
    
  def draw( self):
    self.update_font()
    self.item = self.paper.create_text( self.x, self.y, text='+', tags='plus', font = self.font, fill=self.line_color)
    self.paper.register_id( self.item, self)
    self.selector = self.paper.create_rectangle( self.paper.bbox( self.item), fill=self.area_color, outline=self.area_color)
    self.paper.lift( self.item)

  def redraw( self):
    self.update_font()
    self.paper.coords( self.item, self.x, self.y)
    self.paper.itemconfig( self.item, font = self.font, fill=self.line_color)
    if self.selector:
      self.paper.coords( self.selector, self.paper.bbox( self.item))
      self.paper.itemconfig( self.selector, fill=self.area_color, outline=self.area_color)

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='grey')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def get_id( self):
    return self.item

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1
 
  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0
    
  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy)

  def read_package( self, package):
    pnt = package.getElementsByTagName( 'point')[0]
    self.x, self.y, z = self.paper.read_xml_point( pnt)
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
  
  def get_package( self, doc):
    pls = doc.createElement('plus')
    x, y = self.paper.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( pls, 'point', (('x', x),
                                                ('y', y)))
    if self.line_color != '#000':
      pls.setAttribute( 'color', self.line_color)
    if self.area_color != '#ffffff':
      pls.setAttribute( 'background-color', self.area_color)
    return pls

  def delete( self):
    self.paper.delete( self.selector)
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)

  def get_xy( self):
    return self.x, self.y

  def bbox( self):
    return self.paper.bbox( self.item)

  def scale_font( self, ratio):
    """scales font of plus. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()

  def update_font( self):
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

##--------------------TEXT CLASS--------------------

class text( meta_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'text'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo related metas
  meta__undo_simple = ('x', 'y', 'text', 'font_size', 'font_family', 'line_color', 'area_color')

  def __init__( self, paper, xy=(), text='', package=None):
    meta_enabled.__init__( self, paper)
    self.selector = None
    self._selected = 0
    self.ftext = None
    if xy:
      self.set_xy( xy[0], xy[1])
    self.set_text( text)
    self.item = None
    if package:
      self.read_package( package)
    self.focus_item = None

  # public methods

  def set_xy( self, x, y):
    self.x = round( x, 2)
    self.y = round( y, 2)

  def draw( self):
    "draws text"
    self.update_font()
    self.ftext = ftext( self.paper, xy=(self.x, self.y), dom=self.parsed_text, font=self.font, fill=self.line_color)
    self.ftext.draw()
    x1, y1, x2, y2 = self.ftext.bbox()
    self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('text'))
    self.selector = self.paper.create_rectangle( x1, y1, x2, y2, fill=self.area_color, outline='', tags='helper_a')
    self.ftext.lift()
    self.paper.lift( self.item)
    self.paper.register_id( self.item, self)

  def redraw( self):
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self.selector)
    if self.ftext:
      self.ftext.delete()
    self.draw()
    if self._selected:
      self.select()

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='gray')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1

  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0

  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move( dx, dy)

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.set_xy( x, y)
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move_to( x, y)

  def get_x( self):
    return self.x

  def get_y( self):
    return self.y

  def get_xy( self):
    return self.x, self.y

  def delete( self):
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
    if self.ftext:
      self.ftext.delete()
    return self

  def read_package( self, package):
    pos = package.getElementsByTagName( 'point')[0]
    x, y, z = self.paper.read_xml_point( pos)
    self.set_xy( x, y)
    ft = package.getElementsByTagName('ftext')
    self.parsed_text = ft[0]
    self.text = reduce( operator.add, [e.toxml() for e in ft[0].childNodes], '')
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')

  def get_package( self, doc):
    a = doc.createElement('text')
    if self.area_color != '#ffffff':
      a.setAttribute( 'background-color', self.area_color)
    if self.font_size != 12 or self.font_family != 'helvetica' or self.line_color != '#000':
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != '#000':
        font.setAttribute( 'color', self.line_color)
    x, y = self.paper.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( a, 'point', attributes=(('x', x),('y', y)))
    a.appendChild( self.parsed_text)
    return a

  def set_text( self, text):
    self.text = text
    self.parsed_text = dom.parseString( '<ftext>'+self.text+'</ftext>').childNodes[0]

  def get_text( self):
    return self.text

  def bbox( self):
    return self.ftext.bbox()

  def update_font( self):
    #if 'font_family' in self.__dict__ and 'font_size' in self.__dict__:
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)

  def scale_font( self, ratio):
    """scales font of text. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)
