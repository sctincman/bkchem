#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2004 Beda Kosata <beda@zirael.org>

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



class reaction( object):


  def __init__( self):
    self.reactants = []
    self.products = []
    self.arrows = []
    self.conditions = []
    self.pluses = []



  def add_reactant( self, mol):
    self.reactants.append( mol)

    

  def get_package( self, doc):
    e = doc.createElement( 'reaction')
    for name in ('reactant','product','arrow','condition'):
      for m in self.__dict__[name+'s']:
        el = doc.createElement( name)
        el.setAttribute( 'idref', m.id)
        e.appendChild( el)
    # pluses must be separate because of their fucked plural form :)
    for m in self.pluses:
      el = doc.createElement( 'plus')
      el.setAttribute( 'idref', m.id)
      e.appendChild( el)

    return e


  def is_empty( self):
    for name in ('reactants','products','conditions', 'pluses'):
      if self.__dict__[ name]:
        return 0
    return 1
