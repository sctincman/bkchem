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
# Last edited: $Date$
#
#--------------------------------------------------------------------------

"""this module implements undo_manager and state_record classes,
should provide everything needed to perform undo management.
state_record is used only inside of undo_manager and is not
exported in __all__."""

## NOTE that undo uses a low-level access to objects in order to
## speed up the task.

import misc
import copy
import data
from types import *  #should be safe

__all__= ['undo_manager']

##-------------------- UNDO MANAGER --------------------

class undo_manager:
  """class to process requests for undo tracking and undoing"""

  MAX_RECORDS = 20
  
  def __init__( self, paper):
    """well, init"""
    self.paper = paper
    self._records = []
    self.clean()
    self.start_new_record()
    
  def start_new_record( self, name=''):
    """starts new undo_record closing the recent
    name may be set for a record"""
    if len( self._records)-1 > self._pos:
      del self._records[ (self._pos+1):]
    if len( self._records) >= self.MAX_RECORDS:
      del self._records[0]
      self._pos -= 1
    self._records.append( state_record( self.paper, name=name))
    self._pos += 1

  def undo( self):
    """undoes the last step and returns the number of undo records available"""
    self._pos -= 1
    if self._pos >= 0:
      self._records[ self._pos].undo( self._records[ self._pos+1])
    else:
      self._pos = 0
    return self._pos

  def redo( self):
    """redoes the last undone step, returns number of redos available"""
    self._pos += 1
    if self._pos < len( self._records):
      self._records[ self._pos].undo( self._records[ self._pos-1])
    else:
      self._pos = len( self._records)-1
    return len( self._records) - self._pos -1

  def clean( self):
    """removes all undo informations, does not start new undo record"""
    self._pos = -1
    del self._records[:]

  def get_last_record_name( self):
    """returns the last closed record name"""
    if self._pos >= 1:
      return self._records[ self._pos-1].name
    else:
      return None

  def delete_last_record( self):
    """deletes the last record, useful for concatenation of several records to one;
    especially powerfull in combination with named records;
    use with care - it could cause problems"""
    if self._pos > 0:
      del self._records[ self._pos-1]
      self._pos -= 1

##-------------------- STATE RECORD --------------------
    
class state_record:
  """class able to store state of the whole system and then set
  the system back to that stored state"""

  def __init__( self, paper, name=''):
    """hmmm, what is supposed to be in comment for __init__?"""
    self.paper = paper
    self.objects = []
    self.records = []
    self.name = name
    self.stack = []
    self.record_state()

  def record_state( self):
    """stores all necessary information about the system, so that its than able to
    fully recover that state."""
    self.stack = copy.copy( self.paper.stack)

    for o in self.paper.get_all_containers():
      self.record_object( o)

  def record_object( self, o):
    rec = {}
    for a in o.meta__undo_simple:
      rec[a] = o.__dict__[a]
    for a in o.meta__undo_copy:
      rec[a] = copy.copy( o.__dict__[a])
    for a in o.meta__undo_2d_copy:
      subrec = []
      for line in o.__dict__[a]:
        subrec.append( copy.copy( line))
      rec[a] = subrec
    self.objects.append( o)
    self.records.append( rec)
    # process the chidren
    for a in o.meta__undo_children_to_record:
      obj = o.__dict__[a]
      if type( obj) == ListType:
        [self.record_object( i) for i in obj]
      elif type( obj) == DictType:
        [self.record_object( i) for i in obj.itervalues() if i]
      else:
        self.record_object( obj)

  def undo( self, previous):
    """does undo, actually only calls self.set_state"""
    self.set_state( previous)

  def set_state( self, previous):
    """sets the system to the recorded state (update is done only where necessary,
    not changed values are not touched)."""
    # we need to know about deleted bonds before we try to redraw them (when updating atom)
    deleted = misc.difference( self.objects, previous.objects)
    ## CHANGED OBJECTS
    i = 0
    for o in self.objects:
      changed = 0
      for a in o.meta__undo_simple:
        if self.records[i][a] != o.__dict__[a]:
          o.__dict__[a] = self.records[i][a]
          changed = 1
      for a in o.meta__undo_copy:
        if self.records[i][a] != o.__dict__[a]:
          o.__dict__[a] = copy.copy( self.records[i][a])
          changed = 1
      for a in o.meta__undo_2d_copy:
        subrec = []
        for line in self.records[i][a]:
          subrec.append( copy.copy( line))
        o.__dict__[ a] = subrec

      # this part is not really meta info driven but who cares 
      if changed:
        if o.object_type == 'atom':
          [b.redraw() for b in o.molecule.atoms_bonds( o) if b not in deleted]
        elif o.object_type == 'point':
          o.arrow.redraw()  ## redraws arrow multiple times, should be fixed someday
        if o not in deleted and o.object_type != 'molecule':
          o.redraw()
      i += 1
      # end of explicit rules

    ## DELETED OBJECTS
    # deleted are known from the top of this def
    for o in deleted:
      if o.object_type == 'plus':
        self.paper.pluses.append( o)
      elif o.object_type == 'arrow':
        self.paper.arrows.append( o)
      elif o.object_type == 'text':
        self.paper.texts.append( o)
      elif o.object_type == 'molecule':
        self.paper.molecules.append( o)        
      elif o.object_type in data.vector_graphics_types:
        self.paper.vectors.append( o)
      if o.object_type != 'molecule':
        o.draw()
    ## ADDED OBJECTS
    added = misc.difference( previous.objects, self.objects)
    for o in added:
      if o.object_type == 'plus':
        self.paper.pluses.remove( o)
      elif o.object_type == 'arrow':
        self.paper.arrows.remove( o)
      elif o.object_type == 'text':
        self.paper.texts.remove( o)
      elif o.object_type == 'molecule':
        self.paper.molecules.remove( o)
      elif o.object_type in data.vector_graphics_types:
        self.paper.vectors.remove( o)
      if o.object_type != 'molecule':
        o.delete()

    self.paper.stack = copy.copy( self.stack)
    self.paper.add_bindings()

  def get_difference( self, previous):
    """obsolet method that finds difference between two state_records.
    Its too slow to be used in undo tracking so full state_record is used instead"""
    p_records = previous.records
    r_records = self.records
    p_objects = previous.objects
    r_objects = self.objects
    un_rec = undo_record( self.paper)
    for o in r_objects:
      if o not in p_objects:
        un_rec.added.append( o)
      else:
        a = p_records[ p_objects.index(o)]
        b = r_records[ r_objects.index(o)]
        if a != b:
          un_rec.modified.append( o)
          un_rec.modified_records.append( a)
    un_rec.deleted = misc.difference( p_objects, r_objects)
    return un_rec
    


  
