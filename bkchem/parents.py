#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2003  Beda Kosata <beda@zirael.org>

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
# Last edited: $Date$
#
#--------------------------------------------------------------------------

"""This file stores the oldest parents of used classes which are used to provide
mostly the desired meta_behaviour"""


class simple_parent:
  """this class only gives reasonable default values to meta attributes"""
  # other
  # if a class is a container in paper meaning (is not part of bigger structure)
  meta__is_container = 0

  # class is not made up from smaller parts that define the structure (points etc.)
  # if non zero then specifies the number of coordinate pairs
  meta__has_simple_coords = 1
  # undo related
  meta__undo_simple = ()
  meta__undo_copy = ()
  meta__undo_2d_copy = ()
  meta__undo_children_to_record = ()


class meta_enabled( simple_parent):
  """class that has usefull behaviour implemented according to meta infomation"""

  meta__used_standard_values = []

  def __init__( self, paper):
    self.paper = paper
    self.read_standard_values()

  def read_standard_values( self, old_standard=None):
    """if old_standard is given the recent value is read from standard
    only if it differs from the old one - used for 'inteligent' changes of
    standard properties of existing drawing"""
    for i in self.meta__used_standard_values:
      if old_standard and (self.paper.standard.__dict__[i] == old_standard.__dict__[i]):
        continue
      else:
        self.__dict__[i] = self.paper.standard.__dict__[i]
