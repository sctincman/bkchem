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
# Last edited: $Date: 2003/09/26 10:47:02 $
#
#--------------------------------------------------------------------------

"""provides validator class that checks chemistry"""

import types
import classes

class validator:

  def __init__( self):
    self.report = None

  def start_new_report( self):
    self.report = validator_report()

  def validate( self, o):
    self.start_new_report()
    self.validate_object( o)

  def validate_object( self, o):
    if type( o) == types.ListType:
      self.validate_list( o)
    elif isinstance( o, classes.atom):
      self.validate_atom( o)
    elif isinstance( o, classes.molecule):
      self.validate_molecule( o)

  def validate_atom( self, a):
    if a.type == "text":
      self.report.text_atoms.append( a)
    elif a.type == "group":
      self.report.group_atoms.append( a)
    else:
      fval = a.get_free_valency()
      if fval < 0:
        self.report.exceeded_valency.append( a)

  def validate_molecule( self, mol):
    [self.validate_atom( a) for a in mol.atoms_map]

  def validate_list( self, objs):
    [self.validate_object( o) for o in objs]


class validator_report:

  def __init__( self):
    #self._report_text = ""
    self.text_atoms = []
    self.group_atoms = []
    self.exceeded_valency = []

  def get_text_report( self):
    pass

  def get_summary( self):
    out = ""
    if self.text_atoms:
      out += _("%d text only atom(s) (atoms without known chemical interpretation)") % len( self.text_atoms)
      out += "\n"
    if self.exceeded_valency:
      out += _("%d atom(s) with exceeded valency") % len( self.exceeded_valency)
      out += "\n"
    if self.group_atoms:
      out += _("%d group(s) (groups need to be expanded for some export formats)") % len( self.group_atoms)
      out += "\n"
    if not out:
      out = "OK"
    return out
