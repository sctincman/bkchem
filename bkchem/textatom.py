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


"""home for the textatom - a vertex of a molecular graph"""

from __future__ import division

from math import atan2, sin, cos, pi, sqrt
import misc
import geometry
from warnings import warn
from ftext import ftext
import dom_extensions
import xml.dom.minidom as dom
import operator
import tkFont
from oasa import periodic_table as PT
import groups_table as GT
from parents import meta_enabled, area_colored, point_drawable, text_like, child_with_paper
from special_parents import vertex_common
import data
import re
import debug
import marks
import types

import oasa

from singleton_store import Screen


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class TEXTATOM --------------------------------------------------
class textatom( meta_enabled, area_colored, point_drawable, text_like,
                child_with_paper, vertex_common, oasa.graph.vertex):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ



  object_type = 'atom'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo meta infos
  meta__undo_fake = ('text',)
  meta__undo_simple = ()
  meta__undo_properties = area_colored.meta__undo_properties + \
                          point_drawable.meta__undo_properties + \
                          text_like.meta__undo_properties + \
                          vertex_common.meta__undo_properties + \
                          ( 'z', 'name', 'molecule', 'charge', 'pos')
  meta__undo_copy = vertex_common.meta__undo_copy + ('_neighbors',)
  meta__undo_children_to_record = vertex_common.meta__undo_children_to_record


  def __init__( self, standard=None, xy = (), package = None, molecule = None):
    meta_enabled.__init__( self, standard=standard)
    vertex_common.__init__( self)
    self.molecule = molecule
    point_drawable.__init__( self)
    oasa.graph.vertex.__init__( self)

    if xy:
      self.x, self.y = xy
    self.z = 0

    # presentation attrs
    self.selector = None
    self._selected = 0 #with ftext self.selector can no longer be used to determine if atom is selected
    self.item = None
    self.ftext = None
    self.free_valency = 0

    self.pos = None
    self.focus_item = None

    self.__reposition_on_redraw = 0

    # used only for monitoring when undo is necessary, it does not always correspond to the atom name
    self.text = ''

    self.group_graph = None
    self.name = ''

    if package:
      self.read_package( package)



  ## ---------------------------------------- PROPERTIES ------------------------------
      
  # molecule
  def _get_molecule( self):
    return self.__molecule

  def _set_molecule( self, mol):
    self.__molecule = mol

  molecule = property( _get_molecule, _set_molecule)


  # x
  def _get_x( self):
    return self.__x

  def _set_x( self, x):
    self.__x = Screen.any_to_px( x)

  x = property( _get_x, _set_x)


  # y
  def _get_y( self):
    return self.__y

  def _set_y( self, y):
    self.__y = Screen.any_to_px( y)

  y = property( _get_y, _set_y)


  # z
  def _get_z( self):
    return self.__z or 0

  def _set_z( self, z):
    self.__z = z

  z = property( _get_z, _set_z)


  # name
  def _get_name( self):
    return self.__name

  def _set_name( self, name):
    try:
      t = unicode( name)
    except UnicodeDecodeError:
      t = name.decode( 'utf-8')
    self.__name = t.encode('utf-8')
    self.dirty = 1

  name = property( _get_name, _set_name)



  #LOOK charge
  def _get_charge( self):
    return 0

  def _set_charge( self, charge):
    pass

  charge = property( _get_charge, _set_charge)



  # pos
  def _get_pos( self):
    return self.__pos

  def _set_pos( self, pos):
    self.__pos = pos
    self.dirty = 1

  pos = property( _get_pos, _set_pos)



  #valency (setting)
  def _get_valency( self):
    return 1

  def _set_valency( self, val):
    pass

  valency = property( _get_valency, _set_valency, None, "atoms (maximum) valency, used for hydrogen counting")



  # xml_text (override of text_like.xml_text)
  def _get_xml_text( self):
    return self.get_ftext()

  def _set_xml_text( self, xml_text):
    pass
    #self.set_name( xml_text)  -- ignored for now

  xml_text = property( _get_xml_text, _set_xml_text)



  # font_size (override of text_like.xml_text)
  def _get_font_size( self):
    return self.__font_size

  def _set_font_size( self, font_size):
    self.__font_size = font_size
    self.dirty = 1
    self.__reposition_on_redraw = 1

  font_size = property( _get_font_size, _set_font_size)



  # parent
  def _get_parent( self):
    return self.molecule

  def _set_parent( self, par):
    self.molecule = par

  parent = property( _get_parent, _set_parent, None,
                     "returns self.molecule")



  # drawn
  def _get_drawn( self):
    """is the atoms drawn? on the paper or just virtual"""
    if self.item:
      return 1
    return 0

  drawn = property( _get_drawn, None, None, "tells if the atom is already drawn")


  ## JUST TO MIMICK ATOM
  # show
  def _get_show( self):
    return 1

  def _set_show( self, show):
    pass

  show = property( _get_show, _set_show, None,
                   "should the atom symbol be displayed? accepts both 0|1 and yes|no")


  # show_hydrogens
  def _get_show_hydrogens( self):
    return 1

  def _set_show_hydrogens( self, show_hydrogens):
    pass

  show_hydrogens = property( _get_show_hydrogens, _set_show_hydrogens)

  ## //




  ## // -------------------- END OF PROPERTIES --------------------------


  def copy_settings( self, other):
    """copies settings of self to other, does not check if other is capable of receiving it"""
    meta_enabled.copy_settings( self, other)
    area_colored.copy_settings( self, other)
    point_drawable.copy_settings( self, other)
    text_like.copy_settings( self, other)
    child_with_paper.copy_settings( self, other)
    other.pos = self.pos



  def set_name( self, name, interpret=1, occupied_valency=None):
    self.name = name
    return True



  def get_text( self):
    doc = dom.parseString( "<a>%s</a>" % self.name)
    return dom_extensions.getAllTextFromElement( doc)


  def get_ftext( self):
    return self.name



  def decide_pos( self):
    as = self.get_neighbors()
    p = 0
    for a in as:
      if a.x < self.x:
        p -= 1
      elif a.x > self.x:
        p += 1
    if p > 0:
      self.pos = 'center-last'
    else:
      self.pos = 'center-first'




  def draw( self, redraw=False):
    "draws atom with respect to its properties"
    if self.item:
      warn( "drawing atom that is probably drawn", UserWarning, 2)
    x, y = self.x, self.y
    self.update_font()
    if not self.pos:
      self.decide_pos()
    # we use self.text to force undo when it is changed (e.g. when atom is added to OH so it changes to O)
    self.text = self.get_ftext()
    name = '<ftext>%s</ftext>' % self.text
    self.ftext = ftext( self.paper, (self.x, self.y), name, font=self.font, pos=self.pos, fill=self.line_color)
    x1, y1, x2, y2 = self.ftext.draw()
    self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('atom'))
    ## shrink the selector to improve appearance (y2-2)
    self.selector = self.paper.create_rectangle( x1, y1, x2, y2-3, fill=self.area_color, outline='',tags='helper_a')
    self.ftext.lift()
    self.paper.lift( self.item)
    # marks
    if not redraw:
      [m.draw() for m in self.marks]

    self.paper.register_id( self.item, self)
    self.__reposition_on_redraw = 0


  def redraw( self, suppress_reposition=0):
    if self.__reposition_on_redraw and not suppress_reposition:
      self.reposition_marks()
      self.__reposition_on_redraw = 0

    self.update_font()
    # at first we delete everything...
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self. selector)
    if self.ftext:
      self.ftext.delete()
    self.item = None # to ensure that warning in draw() is not triggered when redrawing
    # ...then we draw it again
    self.draw( redraw=True)
    [m.redraw() for m in self.marks]

    if self._selected:
      self.select()
    else:
      self.unselect()
    if not self.dirty:
      pass
      #print "redrawing non-dirty atom"
    self.dirty = 0

      



  def focus( self):
    self.paper.itemconfig( self.selector, fill='grey')



  def unfocus( self):
    self.paper.itemconfig( self.selector, fill=self.area_color)



  def select( self):
    self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1




  def unselect( self):
    self.paper.itemconfig( self.selector, outline='')
    self._selected = 0



  def move( self, dx, dy, dont_move_marks=0):
    """moves object with his selector (when present)"""
    # saving old dirty value
    # d = self.dirty
    self.x += dx
    self.y += dy
    if self.drawn:
      self.paper.move( self.item, dx, dy)
      if self.selector:
        self.paper.move( self.selector, dx, dy)
      if self.ftext:
        self.ftext.move( dx, dy)
      if not dont_move_marks:
        for m in self.marks:
          m.move( dx, dy)
    # restoring dirty value because move does not dirty the atom
    # self.dirty = d



  def move_to( self, x, y, dont_move_marks=0):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy, dont_move_marks=dont_move_marks)





  def get_xy( self):
    return self.x, self.y




  def get_xyz( self, real=0):
    """returns atoms coordinates, default are screen coordinates, real!=0
    changes it to real coordinates (these two are usually different for imported molecules)"""
    if real:
      x, y = self.paper.screen_to_real_coords( (self.x, self.y))
      z = self.z *self.paper.screen_to_real_ratio()
      return x, y, z
    else:
      return self.x, self.y, self.z





  def delete( self):
    for m in self.marks:
      m.delete()

    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.unselect()
      self.paper.delete( self.selector)
      self.selector = None
      self._selected = 0
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None
    if self.ftext:
      self.ftext.delete()
    return self



  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
    # marks
    for m in package.getElementsByTagName( 'mark'):
      mrk = marks.mark.read_package( m, self)
      self.marks.add( mrk)

    # position
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = Screen.read_xml_point( position)
    if z != None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.x = x
    self.y = y
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name( reduce( operator.add, [e.toxml() for e in ft[0].childNodes], '').encode('utf-8'))
    else:
      raise TypeError, "not text atom"
    # font and fill color
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    # background color
    if package.getAttributeNode( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # number
    if package.getAttribute( 'show_number'):
      self.show_number = bool( data.booleans.index( package.getAttribute( 'show_number')))
    if package.getAttribute( 'number'):
      self.number = package.getAttribute( 'number')




  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('text')
    a.setAttribute( 'id', str( self.id))
    a.setAttribute( 'pos', self.pos)
    # font properties
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    # the text
    a.appendChild( dom.parseString( '<ftext>%s</ftext>' % self.name).childNodes[0])
    # area color
    if self.area_color != self.paper.standard.area_color:
      a.setAttribute( 'background-color', self.area_color)
    # needed to support transparent handling of molecular size
    x, y, z = map( Screen.px_to_text_with_unit, self.get_xyz( real=1))
    if self.z:
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y), ('z', z)))
    else: 
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y)))
    # marks
    for o in self.marks:
      a.appendChild( o.get_package( doc))
    # number
    if self.number:
      a.setAttribute( 'number', self.number)
      a.setAttribute( 'show_number', data.booleans[ int( self.show_number)])

    return a





  def toggle_center( self, mode = 0):
    """toggles the centering of text between 'center-first' and 'center-last'(mode=0)
    or sets it strictly - mode=-1, mode=1"""
    if not mode:
      if self.pos == 'center-last':
        self.pos = 'center-first'
      else:
        self.pos = 'center-last'
    elif mode == -1:
      self.pos = 'center-first'
    else:
      self.pos = 'center-last'
    self.redraw()




  def update_font( self):
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)
        



  def scale_font( self, ratio):
    """scales font of atom. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()




  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    return PT.formula_dict()



  ##LOOK
  def atoms_bound_to( self):
    return self.get_neighbors()




  def lift( self):
    # marks
    [m.lift() for m in self.marks]
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)


  def lift_selector( self):
    if self.selector:
      self.paper.lift( self.selector)




  def transform( self, tr):
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y, dont_move_marks=1)
    for m in self.marks:
      m.transform( tr)


  def __str__( self):
    return self.id



  def get_occupied_valency( self):
    i = 0
    for b in self._neighbors.keys():
      ord = b.order
      if ord == 4:
        ord = 1
      i += ord
    return i



  def bbox( self):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    if self.item:
      return self.paper.bbox( self.item)
    else:
      # we have to calculate it, the atoms was not drawn yet
      length = self.font.measure( self.get_text())
      if self.pos == 'center-first':
        dx = self.font.measure( self.get_text()[0]) / 2
        return (self.x + length - dx, self.y + 0.3*self.font_size, self.x - dx, self.y - 0.7*self.font_size) 
      else:
        dx = self.font.measure( self.get_text()[-1]) / 2
        return (self.x + dx, self.y + 0.3*self.font_size, self.x - length + dx, self.y - 0.7*self.font_size) 






