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

"""template manager resides here"""

import math
from transform import transform
from classes import molecule
import xml.dom.minidom as dom
from warnings import warn
import data
import os.path
import os_support
import xml.sax
import misc

class template_manager:
  templates = []

  def __init__( self, paper):
    self.templates = []
    self._prepared_templates = []
    self.paper = paper

  def add_template_from_CDML( self, file):
    if not os.path.isfile( file):
      file = os_support.get_path( file, "template")
      if not file:
        warn( "template file %s does not exist - ignoring" % file)
        return
    try:
      doc = dom.parse( file).getElementsByTagName( 'cdml')[0]
    except xml.sax.SAXException: 
      warn( "template file %s cannot be parsed - ignoring" % file)
      return
    # when loading old versions of CDML try to convert them, but do nothing when they cannot be converted
    import CDML_versions
    CDML_versions.transform_dom_to_version( doc, data.current_CDML_version)
    for tmp in doc.getElementsByTagName('molecule'):
      self.templates.append( tmp) 
      self._prepared_templates.append( molecule( self.paper, package=tmp))

  def get_template( self, n):
    return self.templates[n]

  def get_template_names( self):
    return [o.name for o in self._prepared_templates]

  def get_transformed_template( self, n, coords, type='empty'):
    """type is type of connection - 'bond', 'atom1'(for single atom), 'atom2'(for atom with more than 1 bond), 'empty'"""
    current = self._prepared_templates[n]
    self._prepared_templates[n] = molecule( self.paper, package=self.templates[n])
    current.name = ''
    current.id = ''
    self._scale_ratio = 1
    trans = transform()
    # type empty - just draws the template - no conection
    if type == 'empty':
      xt1, yt1 = current.t_atom.get_xy()
      xt2, yt2 = current.next_to_t_atom.get_xy()
      x1, y1 = coords
      bond_length = self.paper.any_to_px( self.paper.standard.bond_length)
      current.delete_items( [current.t_atom])
      trans.set_move( -xt2, -yt2)
      trans.set_scaling( bond_length / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2))
      trans.set_move( x1, y1)
    #type atom
    elif type == 'atom1' or type == 'atom2':
      xt1, yt1 = current.t_atom.get_xy()
      xt2, yt2 = current.next_to_t_atom.get_xy()
      x1, y1, x2, y2 = coords
      trans.set_move( -xt2, -yt2)
      trans.set_scaling( math.sqrt( (x1-x2)**2 + (y1-y2)**2) / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2))
      trans.set_rotation( math.atan2( xt1-xt2, yt1-yt2) - math.atan2( x1-x2, y1-y2))
      trans.set_move( x2, y2)
    #type bond
    elif type == 'bond':
      if not (current.t_bond_first and current.t_bond_second):
        warn( "this template is not capable to be added to bond - sorry.")
        return None
      current.delete_items( [current.t_atom])
      xt1, yt1 = current.t_bond_first.get_xy()
      xt2, yt2 = current.t_bond_second.get_xy()
      x1, y1, x2, y2 = coords
      self._scale_ratio = math.sqrt( (x1-x2)**2 + (y1-y2)**2) / math.sqrt( (xt1-xt2)**2 + (yt1-yt2)**2) # further needed for bond.bond_width transformation
      trans.set_move( -xt1, -yt1)
      trans.set_rotation( math.atan2( xt1-xt2, yt1-yt2) - math.atan2( x1-x2, y1-y2))
      trans.set_scaling( self._scale_ratio)
      trans.set_move( x1, y1)
    self.transform_template( current, trans)
    #remove obsolete info from template
    if type == 'atom1':
      current.delete_items( [current.t_atom])
    elif type == 'atom2':
      current.t_atom.set_xy( x1, y1)
    current.t_atom = None
    current.t_bond_first = None
    current.t_bond_second = None
    #return ready template
    return current 
  
  def transform_template( self, temp, trans):
    for a in temp.atoms_map:
      x, y = a.get_xy()
      x, y = trans.transform_xy( x, y)
      a.set_xy( x, y)
      a.scale_font( self._scale_ratio)
    for b in temp.bonds:
      if b.type != 1:
        b.bond_width *= self._scale_ratio
    # update template according to current default values
    self.paper.apply_current_standard( [temp])
    # return the ready template
    return temp


