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
import dom_extensions as dom_ext
import xml.sax.saxutils


class fragment( object):

  def __init__( self, id="", name="", type="explicit"):
    self.id = id
    self.name = name
    self.edges = Set()
    self.type = type # type is one og "explicit", "implicit"
    self.properties = {}  # this is the place for information about an particular fragment
    

  # properties

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




  def is_consistent( self, molecule):
    for e in self.edges:
      if e not in molecule.edges:
        return False
    return True
  


  def get_all_vertices( self):
    vs = Set()
    for e in self.edges:
      vs |= Set( e.vertices)
    return vs

  # property for easier manipulation
  vertices = property( get_all_vertices, None, None, "the vertices associated with fragment bonds")



  def get_package( self, doc):
    el = doc.createElement( "fragment")
    el.setAttribute( "id", self.id)
    el.setAttribute( "type", self.type)
    dom_ext.textOnlyElementUnder( el, "name", xml.sax.saxutils.escape( self.name))
    for e in self.edges:
      dom_ext.elementUnder( el, "bond", (("id", e.id),))
    return el



  def read_package( self, doc, id_manager):
    self.id = doc.getAttribute( "id")
    self.type = doc.getAttribute( "type") or "explicit"
    name = dom_ext.getFirstChildNamed( doc, "name")
    if name:
      self.name = dom_ext.getAllTextFromElement( name)
    for b in dom_ext.simpleXPathSearch( doc, "bond"):
      self.edges.add( id_manager.get_object_with_id( b.getAttribute( "id")))
    
