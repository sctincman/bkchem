#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002  Beda Kosata <kosatab@vscht.cz>

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

"""CML import-export plugin"""

import plugin
import xml.dom.minidom as dom
import dom_extensions as dom_ext
import math

## DEFINITIONS

class CML_importer( plugin.importer):

  def __init__( self):
    # this makes implementing CML2 much easier - just supply different CML_atom and CML_bond
    self.CML_atom = CML_atom
    self.CML_bond = CML_bond

    self.xs = []
    self.ys = []

  def on_begin( self):
    self.xs = []
    self.ys = []
    self.atoms = []
    return 1

  def get_cdml_dom( self, file_name):
    tree = dom.parse( file_name)
    out = dom.Document()
    root = dom_ext.elementUnder( out, 'cdml', (('version','0.8'),))
    for m in tree.getElementsByTagName( 'molecule'):
      out_m = self.transform_molecule( m, out)
      if out_m:
        root.appendChild( out_m)
    view = self.on_end_set_viewport()
    if view:
      viewport = out.createElement( 'viewport')
      viewport.setAttribute( 'viewport', '%f %f %f %f' % view)
      root.insertBefore( viewport, root.firstChild)
    return root

  def transform_molecule( self, mol, doc):
    #atoms
    out = doc.createElement( 'molecule')
    for a in mol.getElementsByTagName( 'atom'):
      out_a = self.transform_atom( a, doc)
      if out_a:
        out.appendChild( out_a)
    # bonds
    ar = mol.getElementsByTagName( 'bondArray')
    if ar:
      ar = ar[0]
      for b in ar.getElementsByTagName( 'bond'):
        out_b = self.transform_bond( b, doc)
        if out_b:
          out.appendChild( out_b)
    else:
      for b in self.add_nonexisting_bonds():
        out.appendChild( b)
    return out

  def transform_atom( self, a, doc):
    out = doc.createElement( 'atom')
    try:
      atom = self.CML_atom( cml=a)
    except cml_exception, detail:
      # problems converting cml to atom
      raise plugin.import_exception( detail)
    if atom.not_enough_data():
      # atom does not have sufficient data to be safely converted to cdml
      raise plugin.import_exception( "missing "+str( atom.not_enough_data())+" in atom specification")
    self.atoms.append( atom)
    dom_ext.setAttributes( out, (('name', atom.name),
                                 ('id', atom.id)))
    pnt = dom_ext.elementUnder( out, 'point', (('x', str( atom.x)),
                                               ('y', str( atom.y))))
    if atom.z != None:
      pnt.setAttribute( 'z', str( atom.z))
    self.xs.append( atom.x)
    self.ys.append( atom.y)
    return out


  def transform_bond( self, b, doc):
    out = doc.createElement( 'bond')
    try:
      bond = self.CML_bond( cml=b)
    except cml_exception, detail:
      # problems converting cml to bond
      raise plugin.import_exception( str( detail))
    return self.transform_CML_bond( bond, doc)

  def transform_CML_bond( self, bond, doc):
    """called by transform_bond in order to do the transform from CML_bond instance to CDML"""
    bond_types = ['no','single', 'double','triple','wedge','hatch']
    if bond.not_enough_data():
      # bond does not have sufficient data to be safely converted to cdml
      raise plugin.import_exception( "missing "+str( bond.not_enough_data())+" in bond specification")
    out = doc.createElement( 'bond')
    dom_ext.setAttributes( out,  (('type', bond_types[ bond.type]),
                                  ('start', bond.atom1),
                                  ('end', bond.atom2)))
    return out


  def on_end_set_viewport( self):
    if self.xs and self.ys:
      x1, y1, x2, y2 = min(self.xs), min(self.ys), max(self.xs), max(self.ys) 
      if (x1 != x2) and (y1 != y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx > 29 and dy > 29:
          # prevents unnecessary scaling
          return None
        cx = (x2+x1)/2
        cy = (y2+y1)/2
        ratio = float( dy) / dx
        if ratio < 0.75:
          dy = 0.75*dx
        elif ratio > 0.75:
          dx = dy/0.75
        return (cx-dx, cy-dy, cx+dx, cy+dy)
    return None

  def add_nonexisting_bonds( self):
    connect = []
    bonds = []
    for i in range( len( self.atoms)):
      connect.append( len( self.atoms)*[0])
    a = self.atoms
    for i in range( len( a)):
      for j in range( len( a)):
        if a[i] != a[j]:
          if math.sqrt( (a[i].x-a[j].x)**2 + (a[i].y-a[j].y)**2) < 2.0:
            connect[i][j] = 1
    for i in range( len( a)):
      for j in range( len( a)):
        if connect[i][j]:
          b = self.CML_bond()
          b.atom1 = a[i].id
          b.atom2 = a[j].id
          bonds.append( self.transform_CML_bond( b))
    return bonds
    

class CML_exporter( plugin.exporter):

  def __init__( self, paper):
    self.paper = paper
    # this makes implementing CML2 much easier - just supply different CML_atom and CML_bond
    self.CML_atom = CML_atom
    self.CML_bond = CML_bond

  def on_begin( self):
    return self.check_chemistry()

  def check_chemistry( self):
    import validator
    val = validator.validator()
    val.validate( self.paper.molecules)
    if val.report.text_atoms:
      import tkMessageBox
      tkMessageBox.showerror( _("CML export error"),
                              _("Sorry but your drawing includes 'text atoms'\n - atoms with no chemical sense.") + "\n\n" +
                              _("It is not possible to export it to valid CML.") + "\n\n" +
                              _("For details check the chemistry with '%s/%s'.") % (_("Object"), _("Check chemistry")))
      return 0
    if val.report.exceeded_valency:
      import tkMessageBox
      tkMessageBox.showwarning( _("CML export warning"),
                                _("Your drawing includes some atoms with exceeded valency.") + "\n\n" + 
                                _("For details check the chemistry with '%s/%s'.") % (_("Object"), _("Check chemistry")))
    if val.report.group_atoms:
      import tkMessageBox
      yes = tkMessageBox.askyesno( _("Expand groups?"),
                                _("Your drawing includes some groups.") + "\n\n" + 
                                _("These must be expanded in order to export to valid CML. The expansion could be undone with undo after the export") + "\n\n"+
                                _("Proceed with expansion?"))
      if yes:
        self.paper.expand_groups( selected=0)
        return 1
      else:
        return 0
    return 1
        

  def write_to_file( self, name):
    out = dom.Document()
    root = dom_ext.elementUnder( out, 'cml')
    for m in self.paper.molecules:
      mol = dom_ext.elementUnder( root, 'molecule')
      if m.id:
        mol.setAttribute( 'id', m.id)
      atoms = dom_ext.elementUnder( mol, 'atomArray')
      for a in m.atoms_map:
        atoms.appendChild( self.CML_atom( atom=a).get_CML_dom( out))
      bonds = dom_ext.elementUnder( mol, 'bondArray')
      for b in m.bonds:
        bonds.appendChild( self.CML_bond( bond=b).get_CML_dom( out))
    dom_ext.safe_indent( root)
    f = open( name, "w")
    f.write( out.toxml())
    f.close()
    

  
# PLUGIN INTERFACE SPECIFICATION
name = "CML"
extensions = [".cml",".xml"]
importer = CML_importer
exporter = CML_exporter






## PRIVATE CLASSES AND FUNCTIONS



class CML_atom:

  def __init__( self, atom=None, cml=None):
    self.id = None
    self.name = None
    self.x = None
    self.y = None
    self.z = None
    self.charge = 0
    if atom:
      self.read_atom( atom)
    elif cml:
      self.read_CML( cml)
    
  def get_CML_dom( self, doc):
    if self.not_enough_data():
      return None # raise cml_exception( "missing "+str( self.not_enough_data())+" in atom specification")
    out = doc.createElement( 'atom')
    #id
    dom_ext.textOnlyElementUnder( out, 'string', str( self.id), (('builtin','atomId'),
                                                                 ('convention','CML')))
    #name
    dom_ext.textOnlyElementUnder( out, 'string', str( self.name), (('builtin','elementType'),
                                                                   ('convention','CML')))
    # x, y
    if self.z == None:
      dom_ext.textOnlyElementUnder( out, 'float', str( self.x), (('builtin','x2'),))
      dom_ext.textOnlyElementUnder( out, 'float', str( self.y), (('builtin','y2'),))
    else:
      dom_ext.textOnlyElementUnder( out, 'float', str( self.x), (('builtin','x3'),))
      dom_ext.textOnlyElementUnder( out, 'float', str( self.y), (('builtin','y3'),))
      dom_ext.textOnlyElementUnder( out, 'float', str( self.z), (('builtin','z3'),))
    return out

  def not_enough_data( self):
    if (self.id and self.name and self.x!=None and self.y!=None):
      return 0
    else:
      res = []
      for i in ['id','name','x','y']:
        if not self.__dict__[i]:
          res.append( i)
      return res

  def read_atom( self, atom):
    self.x = atom.x
    self.y = atom.y
    self.id = atom.get_cdml_id()
    self.name = atom.name
    self.charge = atom.charge

  def read_CML( self, cml):
    # id could be attribute
    if cml.getAttribute( 'id'):
      self.id = cml.getAttribute( 'id')
    for e in cml.childNodes:
      if e.nodeValue:
        continue
      attr = e.getAttribute( 'builtin')
      if attr == 'atomId':
        self.id = dom_ext.getTextFromElement( e)
      elif attr == 'elementType':
        self.name = dom_ext.getTextFromElement( e)
      elif attr in ['x2', 'x3']:
        self.x = float( dom_ext.getTextFromElement( e))
      elif attr in ['y2', 'y3']:
        self.y = float( dom_ext.getTextFromElement( e))
      elif attr == 'z3':
        self.z = float( dom_ext.getTextFromElement( e))
      



class CML_bond:

  def __init__( self, bond=None, cml=None):
    self.type = 1
    self.atom1 = None
    self.atom2 = None
    if bond:
      self.read_bond( bond)
    elif cml:
      self.read_CML( cml)

    
  def get_CML_dom( self, doc):
    if self.not_enough_data():
      return None
    out = doc.createElement( 'bond')
    #atom1
    dom_ext.textOnlyElementUnder( out, 'string', str( self.atom1), (('builtin','atomRef'),
                                                                    ('convention','CML')))
    #atom2
    dom_ext.textOnlyElementUnder( out, 'string', str( self.atom2), (('builtin','atomRef'),
                                                                    ('convention','CML')))
    #type
    dom_ext.textOnlyElementUnder( out, 'string', str( self.type), (('builtin','order'),
                                                                   ('convention','CML')))
    return out

  def not_enough_data( self):
    if (self.type and self.atom1 and self.atom2):
      return 0
    else:
      res = []
      for i in ['atom1','atom2','type']:
        if not self.__dict__[i]:
          res.append( i)
      return res
      

  def read_bond( self, bond):
    self.atom1 = bond.atom1.get_cdml_id()
    self.atom2 = bond.atom2.get_cdml_id()
    self.type = bond.type

  def read_CML( self, cml):
    for e in cml.childNodes:
      if e.nodeValue:
        continue
      attr = e.getAttribute( 'builtin')
      if attr == 'atomRef':
        if not self.atom1:
          self.atom1 = dom_ext.getTextFromElement( e)
        else:
          self.atom2 = dom_ext.getTextFromElement( e)
      elif attr == 'order':
        type = dom_ext.getTextFromElement( e)
        if type == 'A':
          self.type = 1
        else:
          try:
            self.type = int( type)
          except ValueError:
            raise cml_exception( "Wrong bond type '%s'" % type)

      
## a = CML_importer()
## d = a.get_cdml_dom( 'ccl4.xml')
## dom_ext.safe_indent( d.childNodes[0])
## print d.toxml()

class cml_exception( Exception):
  def __init__( self, value):
    self.value = value

  def __str__( self):
    return self.value

  
