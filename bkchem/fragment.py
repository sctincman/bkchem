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


from sets import Set



class fragment( object):

  def __init__( self, id, name=""):
    self.id = id
    self.name = name
    self.edges = Set()
    self.properties = {}  # this is the place for information about an particular fragment
    

  def _get_name( self):
    return self._name

  def _set_name( self, name):
    self._name = name

  name = property( _get_name, _set_name, None, "name of the fragment")


  def _get_id( self):
    return self._id

  def _set_id( self, id):
    self._id = id

  id = property( _get_id, _set_id, None, "id of the fragment")


  
  
