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

"""PostScript Export plugin"""

import plugin
import oasa_bridge
import types

class molfile_importer( plugin.importer):

  gives_molecule = 1
  gives_cdml = 0

  def __init__( self, paper):
    plugin.importer.__init__( self)
    self.paper = paper

  def on_begin( self):
    return 1

  def get_molecules( self, name):
    file = open( name, 'r')
    mol = oasa_bridge.read_molfile( file, self.paper)
    file.close()
    return [mol]


class molfile_exporter( plugin.exporter):

  def __init__( self, paper):
    plugin.exporter.__init__( self, paper)

  def on_begin( self):
    conts, u = self.paper.selected_to_unique_top_levels()
    mols = [o for o in conts if o.object_type == 'molecule']
    if not mols:
      import tkMessageBox
      tkMessageBox.showerror( _("No molecule selected."),
                              _('You have to select exactly one molecule (any atom or bond will do).'))
      return 0
    elif len( mols) > 1:
      import tkMessageBox
      tkMessageBox.showerror( _("%d molecules selected.") % len( mols),
                              _('You have to select exactly one molecule (any atom or bond will do).'))
      return 0
    else:
      self.molecule = mols[0]
      return 1

  def write_to_file( self, name):
    if type( name) == types.StringType:
      file = open( name, 'w')
    else:
      file = name
    oasa_bridge.write_molfile( self.molecule, file)
    

name = "Molfile"
extensions = ['.mol']
exporter = molfile_exporter
importer = molfile_importer

if not oasa_bridge.oasa_available:
  del importer
  del exporter
