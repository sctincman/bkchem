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

from __future__ import generators
#from generators import lazy_map, take
import re

"""periodic table as a dictionary, plus functions for molecular
formula manipulation and computation"""

periodic_table = {
  "H":  {"weight": 1.008 , "valency": (1,)},
  "He": {"weight": 4.00  , "valency": (0,2)},
  "Li": {"weight": 6.94  , "valency": (1,)},
  "Be": {"weight": 9.01  , "valency": (2,)},
  "B":  {"weight": 10.81 , "valency": (3,)},
  "C":  {"weight": 12.011, "valency": (4,)},
  "N":  {"weight": 14.007, "valency": (3,5)},
  "O":  {"weight": 15.999, "valency": (2,)},
  "F":  {"weight": 18.998, "valency": (1,)},
  "Ne": {"weight": 20.18 , "valency": (0,2)},
  "Na": {"weight": 22.990, "valency": (1,)},
  "Mg": {"weight": 24.31 , "valency": (2,)},
  "Al": {"weight": 26.98 , "valency": (3,)},
  "Si": {"weight": 28.09 , "valency": (4,)},
  "P":  {"weight": 30.974, "valency": (3,5)},
  "S":  {"weight": 32.064, "valency": (2,4,6)},
  "Cl": {"weight": 35.453, "valency": (1,5,7)},
  "Ar": {"weight": 39.95 , "valency": (0,2)},
  "K":  {"weight": 39.102, "valency": (1,)},
  "Ca": {"weight": 40.80 , "valency": (2,)},
  "Sc": {"weight": 44.96 , "valency": (3,1)},
  "Ti": {"weight": 47.90 , "valency": (4,3)},
  "V":  {"weight": 50.94 , "valency": (2,4,5)},
  "Cr": {"weight": 52.00 , "valency": (2,3,6)},
  "Mn": {"weight": 54.94 , "valency": (2,3,4,6,7)},
  "Fe": {"weight": 55.85 , "valency": (2,3)},
  "Co": {"weight": 58.93 , "valency": (2,3)},
  "Ni": {"weight": 58.70 , "valency": (2,3)},
  "Cu": {"weight": 63.54 , "valency": (2,1)},
  "Zn": {"weight": 65.38 , "valency": (2,)},
  "Ga": {"weight": 69.72 , "valency": (3,)},
  "Ge": {"weight": 72.59 , "valency": (4,)},
  "As": {"weight": 74.92 , "valency": (3,5)},
  "Se": {"weight": 78.96 , "valency": (2,4,6)},
  "Br": {"weight": 79.909, "valency": (1,5)},
  "Kr": {"weight": 83.80 , "valency": (0,2)},
  "Rb": {"weight": 85.47 , "valency": (1,)},
  "Sr": {"weight": 87.62 , "valency": (2,)},
  "Y":  {"weight": 88.91 , "valency": (3,)},
  "Zr": {"weight": 91.22 , "valency": (4,)},
  "Nb": {"weight": 92.91 , "valency": (3,5)},
  "Mo": {"weight": 95.94 , "valency": (3,5,6)},
  "Tc": {"weight": 97.00 , "valency": (5,7)},
  "Ru": {"weight": 101.07, "valency": (3,4,6,8)},
  "Rh": {"weight": 102.91, "valency": (3,4)},
  "Pd": {"weight": 106.42, "valency": (2,4)},
  "Ag": {"weight": 107.87, "valency": (1,)},
  "Cd": {"weight": 112.41, "valency": (2,)},
  "In": {"weight": 114.82, "valency": (3,)},
  "Sn": {"weight": 118.69, "valency": (2,4)},
  "Sb": {"weight": 121.75, "valency": (3,5)},
  "Te": {"weight": 127.60, "valency": (2,4,6)},
  "I":  {"weight":126.904, "valency": (1,5,7)},
  "Xe": {"weight": 131.30, "valency": (0,2)},
  "Cs": {"weight": 132.91, "valency": (1,)},
  "Ba": {"weight": 137.33, "valency": (2,)},
  "La": {"weight": 138.91, "valency": (3,)},
  "Hf": {"weight": 178.49, "valency": (4,)},
  "Ta": {"weight": 180.95, "valency": (5,)},
  "W":  {"weight": 183.85, "valency": (6,)},
  "Re": {"weight": 186.21, "valency": (7,)},
  "Os": {"weight": 190.20, "valency": (4,6,8)},
  "Ir": {"weight": 192.22, "valency": (3,4,6)},
  "Pt": {"weight": 195.09, "valency": (2,4)},
  "Au": {"weight": 196.97, "valency": (1,3)},
  "Hg": {"weight": 200.59, "valency": (1,2)},
  "Tl": {"weight": 204.37, "valency": (1,3)},
  "Pb": {"weight": 207.2 , "valency": (2,4)},
  "Bi": {"weight": 208.98, "valency": (3,5)},
  "Po": {"weight": 209   , "valency": (2,4,6)},
  "At": {"weight": 210   , "valency": (1,7)},
  "Rn": {"weight": 222   , "valency": (0,2)},
  "U":  {"weight": 238.03, "valency": (3,4,5,6)}
  }

# elements that accept cations and raise their valency; for each element a valency is specified
# because this property is valency (oxidation state) specific 
accept_cation = {'N': 3, 'P': 3, 'O': 2, 'S': 2, 'Se': 2}

# elements that accept anions and raise their valency; for each element a valency is specified
# because this property is valency (oxidation state) specific 
accept_anion = {'B': 3, 'Al': 3, 'P': 5}


class composition_dict( dict):
  """special dict that automatically converts itself to human readable composition on str()"""
  def __str__( self):
    ret = ''
    for n in ('C','H'):
      if n in self:
        if ret:
          ret += ', '
        ret += "%s: %2.3f%%" % (n, self[n])
    k = self.keys()
    k.sort()
    for n in self:
      if n not in ('C','H'):
        if ret:
          ret += ', '
        ret += "%s: %2.3f%%" % (n, self[n])
    return ret

class formula_dict( dict):
  """special dict that automatically converts itself to human readable
  formula on str(). Implements += for convenient formula concatenation"""

  def __init__( self, form=None):
    dict.__init__( self)
    ## incomplete means that there were some problems to fully convert a formula to this dict
    self.incomplete = 0
    if form:
      self.read_formula_string( form)
  
  def __str__( self, reverse=0):
    sum = ''
    k = self.sorted_keys()
    if reverse:
      k.reverse()
    for s in k:
      if self[s] == 1:
        num = ''
      else:
        num = str( self[s])
      sum += s+num
    return sum

  def __iadd__( self, other):
    for s in other:
      if s in self:
        self[s] += other[s]
      else:
        self[s] = other[s]
    return self

  def __add__( self, other):
    ret = formula_dict()
    for form in (self, other):
      for s in form:
        if s in ret:
          ret[s] += form[s]
        else:
          ret[s] = form[s]
    return ret

  def get_element_fraction( self, element):
    if element in self:
      return self[element]*periodic_table[element]['weight']/self.get_molecular_weight()
    return 0

  def get_molecular_weight( self):
    tot = 0
    for i in self:
      tot += self[i]* periodic_table[i]['weight']
    return tot
  
  def keys_in_order( self):
    return self.sorted_keys()

  def sorted_keys( self):
    k = self.keys()
    ret = []
    for a in ('C','H'):
      if a in k:
        ret.append( a)
        k.remove( a)
    k.sort()
    return ret+k

  def read_formula_string( self, form):
    is_formula = re.compile("^([A-Z][a-z]?[0-9]*)*$")
    if not is_formula.match( form):
      return None
    chunks = re.split( "([A-Z][a-z]*)", form)
    del chunks[0]
    for i in range( 0, len( chunks), 2):
      if chunks[i] in self:
        if chunks[i+1] == '':
          j = 1
        else:
          j = int( chunks[i+1])
        self[ chunks[i]] += j
      elif chunks[i] in periodic_table:
        if chunks[i+1] == '':
          j = 1
        else:
          j = int( chunks[i+1])
        self[ chunks[i]] = j
      else:
        self.incomplete = 1

  def get_html_repr_as_string( self, outer_element=None, reverse=0):
    sum = ''
    k = self.sorted_keys()
    if reverse:
      k.reverse()
    for s in k:
      if self[s] == 1:
        num = ''
      else:
        num = '<sub>%d</sub>' % self[s]
      sum += s+num
    if outer_element:
      return '<%s>%s</%s>' % (outer_element, sum, outer_element)
    return sum
    
  def is_saturated_alkyl_chain( self):
    if (self.sorted_keys() == ['C','H']) and (self['H'] == 2*self['C']+1):
      return 1
    else:
      return 0

    
def dict_to_composition( form):
  w = form.get_molecular_weight()
  ret = composition_dict()
  for s in form:
    ret[ s] = form.get_element_fraction(s) * 100
  return ret

def formula_to_weight( formula):
  return formula_dict( formula).get_molecular_weight()

def formula_to_formula( formula):
  return str( formula_dict( formula))

def formula_to_composition( formula):
  return dict_to_composition( formula_to_dict( formula))


## other support functions

def text_to_hydrogenated_atom( text):
  a = re.match( '([a-z]{0,2})(h)(\d*)([a-z]{0,2})', text.lower())
  if a:
    hydrogens = a.group(3)
    atom1 = a.group(1)
    atom2 = a.group(4)
    if atom1 and atom2:
      return None
    else:
      atom = atom1 or atom2
      if atom.capitalize() in periodic_table:
        ret = formula_dict()
        ret[ atom.capitalize()] = 1
        if hydrogens:
          ret[ 'H'] = int( hydrogens)
        else:
          ret[ 'H'] = 1
        return ret
      else:
        return None
  else:
    return None


def gen_bit_masks( length):
  ret = length * [0]
  yield ret
  for i in xrange( 2 ** length):
    ret[0] += 1
    for j in xrange( length):
      if ret[j] == 2:
        ret[j] = 0
        if j == length-1:
          raise StopIteration
        else:
          ret[j+1] += 1
      else:
        break
    yield ret
  

