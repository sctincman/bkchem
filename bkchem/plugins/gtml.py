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
import xml.sax
import StringIO

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
    self._mol_ids = {}
    self._reactions = []


  def on_begin( self):
    """this method is called before every import"""
    return 1




  def get_molecules( self, file_name):
    self.molecules = []

    # prepare the file to resolve entities
    f = StringIO.StringIO()
    f.write( "<!DOCTYPE item [")
    entities = file( 'mathmlentities.ent')
    f.write( entities.read())
    entities.close()
    f.write( "<!ENTITY epsilon '&#x3B5;'><!ENTITY nevim '&amp;nevim;'>]>")

    the_file = file( file_name)
    f.write( the_file.read())
    the_file.close()
    f.seek(0)
    
    doc = dom.parse( f)
    f.close()


    for ch in xpath.Evaluate( "//graph[@type='molecule']", doc):
      m = self._read_molecule( ch)
      self.molecules.append( m)

    # reactions
    self.process_reactions( doc)
    if self._reactions:
      print "no support for reactions, yet"
      return []

    self.place_molecules()

    # things that have to be done after the whole molecule is read and places
    for m in self.molecules:
      [a.generate_marks_from_cheminfo() for a in m.atoms]

    return self.molecules





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

    self._mol_ids[ el.getAttribute( 'id')] = m
    return m




  def _read_atom( self, at, mol):
    a = atom( self.paper, molecule=mol)
    a.name = dom_ext.getAllTextFromElement( xpath.Evaluate("symbol", at)[0])
    a.x = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/x", at)[0]))
    a.y = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/y", at)[0]))
    a.z = float( dom_ext.getAllTextFromElement( xpath.Evaluate("coordinates/z", at)[0]))
    a.show_hydrogens = int( a.name != 'C')
    # charge
    chel = xpath.Evaluate("charge", at)
    if chel:
      a.charge = int( dom_ext.getAllTextFromElement( chel[0]))
    # remap of ids
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
    if self._reactions:
      for react in self.reactions:
        reactants, products = react
          
    else:
      for m in self.molecules:
        bbox, bl = m.get_geometry()
        maxx, maxy, minx, miny = bbox

        if bl:
          scale = self.paper.any_to_px( self.paper.standard.bond_length) / bl
        else:
          scale = 1
        movex = 320 #- scale*(maxx+minx)/2
        movey = 240 #- scale*(maxy+miny)/2
        for a in m.atoms:
          a.x = movex + scale*a.x
          a.y = movey + scale*a.y


  def _scale_and_move_molecule( self, mol):
    pass



  def process_reactions( self, doc):
    for react in xpath.Evaluate( "//graph[@type='reaction']", doc):
      print react
      reactants = []
      products = []
      for e in xpath.Evaluate( "edge/end[@type='initial']", react):
        id = e.getAttribute( 'idref')
        if id not in reactants:
          reactants.append( id)
      for e in xpath.Evaluate( "edge/end[@type='terminal']", react):
        id = e.getAttribute( 'idref')
        if id not in products:
          products.append( id)
      self._reactions.append( (reactants,products))
          



class gtml_exporter:

  def __init__( self, paper):
    pass

  
# PLUGIN INTERFACE SPECIFICATION
name = "GTML"
extensions = [".gtml",".xml"]
importer = gtml_importer
exporter = gtml_exporter






## PRIVATE CLASSES AND FUNCTIONS



