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

"""provides external_data_manager class, which takes care of reading external data
specification, stores the references between objects and data and saves the data
to CDML"""


class external_data_manager( object):


  def __init__( self):
    self.records = {}
    self.definitions = {}
    self.read_data_definition( 'ahoj')


  def read_data_definition( self, filename):
    react = {'molecule': {'reactive_atom': { 'type':'atom',
                                             'text':'Reactive atom',
                                             'text-cs': 'Reaktivni atom'
                                             },
                          'reactive_bond': { 'type': 'bond',
                                             'text': 'Reactive bond'
                                             },
                          'relative_reactivity': { 'type': 'IntType',
                                                   'text': 'Relative reactivity'
                                                   },
                          }
             }
    self.definitions[ 'reactivity'] = react


  def get_definitions_for_class_and_type( self, def_class, item_type):
    dclass = self.definitions.get( def_class, None)
    if dclass:
      return dclass.get( item_type, None)
    else:
      return None


  def get_definition_classes( self):
    return self.definitions.keys()
