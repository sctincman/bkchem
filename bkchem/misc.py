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

"""module containing miscelanous functions used in BKchem that don't
fit anywhere else. Does not contain any objects"""

import math
import time
import string
from warnings import warn
import re
import types

def intersection( a, b):
  "returns intersection of 2 lists"
  ret = []
  for i in a:
    if i in b:
      ret.append( i)
  return ret


def difference( a,b):
  "returns difference of 2 lists ( a-b)"
  ret = list( a)  # needed for type conversion of tuple for instance
  for i in b:
    if i in ret:
      ret.remove( i)
  return ret


def signum( a):
  if a == 0:
    return 0
  elif a < 0:
    return -1
  else:
    return 1


def filter_unique( items):
  #t1 = time.time()
  ret = []
  for item in items:
    if item not in ret:
      ret.append( item)
  #print time.time() - t1
  return ret


#def sub_all_numbers( text):
#  return re.sub( "\d+", '<sub>\g<0><\\sub>', text)

def reverse_molecule_formula( formula):
  pass
  

def normalize_coords( coords):
  x1, y1, x2, y2 = coords
  if x2 < x1:
    x2, x1 = x1, x2
  if y2 < y1:
    y2, y1 = y1, y2
  return (x1, y1, x2, y2)


def list_difference( list):
  """return a list of differences between list members,
  the list is by 1 shorter than the original"""
  ret = []
  for i in range( len( list)-1):
    ret.append( list[i]-list[i+1])
  return ret


def split_number_and_unit( txt):
  try:
    v = float( txt)
    return v, ''
  except:
    pass
  cutter = re.compile( "([+-]?\d*\.?\d*)\s*([a-zA-Z]*)")
  if txt:
    a = cutter.match( txt)
    if a and a.group(1):
      return float( a.group(1)), a.group(2)
  return None, None


def lazy_apply( function, arguments):
  """similar to apply but returns a callable (lambda) that performs the apply when called."""
  return lambda: apply( function, arguments)
