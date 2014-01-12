#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

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

from random import randint
from warnings import warn



class id_manager(object):

  def __init__(self):
    self.id_map = {}


  def register_id(self, obj, Id):
    if self.is_registered_object(obj):
      raise ValueError("Object is already registered " + str(obj))
    self.id_map[Id] = obj


  def unregister_id(self, Id, obj):
    try:
      if self.id_map[Id] != obj:
        raise ValueError("Id and object do not correspond")
      del self.id_map[Id]
    except KeyError:
      raise ValueError("Id %s is not registered" % Id)


  def get_object_with_id(self, Id):
    return self.id_map[Id]


  def get_object_with_id_or_none(self, Id):
    return self.id_map.get(Id, None)


  def generate_id(self, prefix='id'):
    while 1:
      Id = prefix + str(randint(1, 100000))
      if Id not in self.id_map:
        return Id


  def generate_and_register_id(self, obj, prefix='id'):
    Id = self.generate_id(prefix=prefix)
    self.register_id(obj, Id)
    return Id


  def is_registered_object(self, obj):
    return (obj in self.id_map.values())


  def get_id_of_object(self, obj):
    for k, v in self.id_map.items():
      if v == obj:
        return k
    return None


  def unregister_object(self, obj):
    self.unregister_id(self.get_id_of_object(obj), obj)

