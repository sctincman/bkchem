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


"""GTML import-export plugin"""

import plugin
import xml.dom.minidom as dom
import dom_extensions as dom_ext
from xml import xpath
from molecule import molecule
from atom import atom
from bond import bond
import math


## gtml_to_bkchem_bond_order_remap = {'single':1,
##                                    'double':2,
##                                    'triple':3}

gtml_to_bkchem_bond_order_remap = ['empty','single','double','triple']


## DEFINITIONS

class gtml_importer:

  gives_molecule = 1
  gives_cdml = 0



  def __init__( self, paper):
    self.paper = paper
    self._atom_id_remap = {}




  def on_begin( self):
    """this method is called before every import"""
    return 1




  def get_molecule( self, file_name):
    self.molecules = []

    doc = dom.parse( file_name)
    for ch in xpath.Evaluate( "//graph[@type='molecule']", doc):
      m = self._read_molecule( ch)
      self.molecules.append( m)

    self.place_molecules()

    return self.molecules[0]





  def _read_molecule( self, el):
    m = molecule( self.paper)
    for v in xpath.Evaluate( "vertex", el):
      a2 = self._read_atom( v, m)
      m.insert_atom( a2)
      # bonds
      bond_lengths = []
    for b in xpath.Evaluate("edge", el):
      b2 = self._read_bond( b)
      m.insert_bond( b2)
    return m




  def _read_atom( self, at, mol):
    a = atom( self.paper, molecule=mol)
    a.name = dom_ext.getAllTextFromElement( xpath.Evaluate("symbol", at)[0])
    a.x = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/x", at)[0]))
    a.y = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/y", at)[0]))
    a.z = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/z", at)[0]))
    self._atom_id_remap[ at.getAttribute( 'id')] = a
    return a



  def _read_bond( self, bo):
    b = bond( self.paper)
    b.order = gtml_to_bkchem_bond_order_remap.index( dom_ext.getAllTextFromElement( xpath.Evaluate("bond", bo)[0]))
    ids = [i.nodeValue for i in xpath.Evaluate( "end/@idref", bo)]
    b.atoms = [self._atom_id_remap[ i] for i in ids]
    return b



  def place_molecules( self):
    # data for rescaling
    maxx, maxy, minx, miny = 4 * [None]
    bond_lengths = []
    for m in self.molecules:
      for a2 in m.atoms:
        if not maxx or a2.x > maxx:
          maxx = a2.x
        if not minx or a2.x < minx:
          minx = a2.x
        if not miny or a2.y < miny:
          miny = a2.y
        if not maxy or a2.y > maxy:
          maxy = a2.y
      for b2 in m.bonds:
        bond_lengths.append( math.sqrt( (b2.atom1.x-b2.atom2.x)**2 + (b2.atom1.y-b2.atom2.y)**2))
      # rescale
      bl = sum( bond_lengths) / len( bond_lengths)
      scale = self.paper.any_to_px( self.paper.standard.bond_length) / bl
      movex = 320 - scale*(maxx+minx)/2
      movey = 240 - scale*(maxy+miny)/2
      for a in m.atoms:
        a.x = movex + scale*a.x
        a.y = movey + scale*a.y



class gtml_exporter:

  def __init__( self, paper):
    pass

  
# PLUGIN INTERFACE SPECIFICATION
name = "GTML"
extensions = [".gtml",".xml"]
importer = gtml_importer
exporter = gtml_exporter






## PRIVATE CLASSES AND FUNCTIONS
