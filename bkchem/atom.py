#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002, 2003, 2004 Beda Kosata <beda@zirael.org>

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


"""home for atom class"""

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
import periodic_table as PT
import groups_table as GT
import marks
from parents import meta_enabled, area_colored, point_drawable, text_like, child
import data
import re
import debug

### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class ATOM --------------------------------------------------
class atom( meta_enabled, area_colored, point_drawable, text_like, child):
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
                          ( 'z', 'show', 'name', 'molecule', 'charge', 'show_hydrogens',
                            'pos', 'type', 'multiplicity', 'valency')
  meta__undo_copy = ('marks',)
  meta__undo_children_to_record = ('marks',)


  meta__configurable = {'show': (None, str),
                        'show_hydrogens': (int, str),
                        'charge': (int, str)
                        }


  def __init__( self, paper, xy = (), package = None, molecule = None):
    meta_enabled.__init__( self, paper)
    point_drawable.__init__( self)
    # hidden
    self.__reposition_on_redraw = 0

    # basic attrs
    self.molecule = molecule

    # presentation attrs
    self.selector = None
    self._selected = 0 #with ftext self.selector can no longer be used to determine if atom is selected
    self.item = None
    self.ftext = None
    if xy:
      self.x, self.y = xy
    self.z = 0
    self.pos = None
    self.focus_item = None
    self.marks = {'radical': None, 'biradical': None, 'electronpair': None,
                  'plus': None, 'minus': None}

    # chemistry attrs
    #   self.number = 0
    #   self.show_number = 0
    self.show_hydrogens = 0
    self.show = 0
    self.charge = 0
    self.multiplicity = 1
    # used only for monitoring when undo is necessary, it does not always correspond to the atom name
    # only in case of self.show == 1
    self.text = ''

    if package:
      self.read_package( package)
    else:
      self.set_name( 'C')
    self.update_font()



  ## ---------------------------------------- PROPERTIES ------------------------------
      
  # molecule
  def __get_molecule( self):
    return self.__molecule

  def __set_molecule( self, mol):
    self.__molecule = mol

  molecule = property( __get_molecule, __set_molecule)


  # x
  def __get_x( self):
    return self.__x

  def __set_x( self, x):
    self.__x = self.paper.any_to_px( x)

  x = property( __get_x, __set_x)


  # y
  def __get_y( self):
    return self.__y

  def __set_y( self, y):
    self.__y = self.paper.any_to_px( y)

  y = property( __get_y, __set_y)


  # z
  def __get_z( self):
    return self.__z

  def __set_z( self, z):
    self.__z = z

  z = property( __get_z, __set_z)


  # name
  def __get_name( self):
    return self.__name

  def __set_name( self, name):
    try:
      t = unicode( name)
    except UnicodeDecodeError:
      t = name.decode( 'utf-8')
    self.__name = t.encode('utf-8')
    self.dirty = 1
    #self.show = int( self.__name != 'C')

  name = property( __get_name, __set_name)


  # show
  def __get_show( self):
    return self.__show

  def __set_show( self, show):
    if show in data.booleans:
      self.__show = data.booleans.index( show)
    else:
      self.__show = int( show)
    self.dirty = 1
    self.__reposition_on_redraw = 1

  show = property( __get_show, __set_show, None,
                   "should the atom symbol be displayed? accepts both 0|1 and yes|no")


  # show_hydrogens
  def __get_show_hydrogens( self):
    return self.__show_hydrogens

  def __set_show_hydrogens( self, show_hydrogens):
    if show_hydrogens in data.on_off:
      self.__show_hydrogens = data.on_off.index( show_hydrogens)
    else:
      self.__show_hydrogens = int( show_hydrogens)
    self.dirty = 1
    self.__reposition_on_redraw = 1

  show_hydrogens = property( __get_show_hydrogens, __set_show_hydrogens)


  # charge
  def __get_charge( self):
    return self.__charge

  def __set_charge( self, charge):
    self.__charge = charge
    self.dirty = 1

  charge = property( __get_charge, __set_charge)



  # pos
  def __get_pos( self):
    return self.__pos

  def __set_pos( self, pos):
    self.__pos = pos
    self.dirty = 1

  pos = property( __get_pos, __set_pos)


  # type
  def __get_type( self):
    return self.__type

  def __set_type( self, type):
    self.__type = type
    self.dirty = 1

  type = property( __get_type, __set_type)



  # valency
  def __get_valency( self):
    try:
      self.__valency
    except AttributeError:
      self.set_valency_from_name()
    return self.__valency

  def __set_valency( self, val):
    self.__valency = val

  valency = property( __get_valency, __set_valency, None, "atoms (maximum) valency, used for hydrogen counting")



  # xml_text (override of text_like.xml_text)
  def __get_xml_text( self):
    return self.get_ftext()

  def __set_xml_text( self, xml_text):
    pass
    #self.set_name( xml_text)  -- ignored for now

  xml_text = property( __get_xml_text, __set_xml_text)



  # font_size (override of text_like.xml_text)
  def __get_font_size( self):
    return self.__font_size

  def __set_font_size( self, font_size):
    self.__font_size = font_size
    self.dirty = 1
    self.__reposition_on_redraw = 1

  font_size = property( __get_font_size, __set_font_size)



  # parent
  def __get_parent( self):
    return self.molecule

  parent = property( __get_parent, None, None,
                     "returns self.molecule")



  # multiplicity
  def __get_multiplicity( self):
    return self.__multiplicity
  
  def __set_multiplicity( self, multiplicity):
    self.__multiplicity = multiplicity

  multiplicity = property( __get_multiplicity, __set_multiplicity, None,
                           "returns multiplicity of molecule")


  # drawn
  def __get_drawn( self):
    """is the atoms drawn? on the paper or just virtual"""
    if self.item:
      return 1
    return 0

  drawn = property( __get_drawn, None, None, "tells if the atom is already drawn")




  ## // -------------------- END OF PROPERTIES --------------------------

  def set_name( self, name, interpret=1, check_valency=1):
    self._set_name( name, interpret=interpret, check_valency=check_valency)
    self.set_valency_from_name()


  def _set_name( self, name, interpret=1, check_valency=1):
    # every time name is set the charge should be set to zero or the value specified by marks
    self.charge = self.get_charge_from_marks()
    self.dirty = 1
    # name should not be interpreted
    if not interpret:
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'
      self.show = 1
      return
    # try to interpret name
    if name.lower() != 'c':
      self.show = 1
    else:
      self.show = 0
    elch = self.split_element_and_charge( name)
    if elch:
      # name is element symbol + charge
      self.name = elch[0]
      self.show_hydrogens = 0
      self.type = 'element'
      self.charge += elch[1]
    elif (name.lower() in GT.groups_table) and ( not check_valency or self.molecule.get_atoms_occupied_valency( self) == 1):
      # name is a known group
      self.name = GT.groups_table[ name.lower()]['name']
      self.show_hydrogens = 0
      self.type = 'group'
    else:
      # try other possibilities such as alkyl chain or atom with hydrogens
      # try if name is hydrogenated form of an element
      form = PT.text_to_hydrogenated_atom( name)
      if form:
        # it is!
        a = form.keys()
        a.remove( 'H')
        valency = self.molecule.get_atoms_occupied_valency( self)
        if form['H'] in [i-valency+self.charge for i in PT.periodic_table[a[0]]['valency']]:
          self.name = a[0]
          self.show_hydrogens = 1
          self.type = 'element'
          #self.show = 1
          return
      # try if the name is an alkyl chain such as c6h13
      form = PT.formula_dict( name.upper())
      if form.is_saturated_alkyl_chain() and self.get_occupied_valency() == 1:
        self.name = str( form)
        self.show_hydrogens = 1
        self.type = 'chain'
        return
      # its nothing interesting - just text
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'
      debug.log( name, 'is text')




  def get_text( self):
    if self.type in ('text', 'group'):
      return self.name
    elif self.type == 'element' and not self.show:
      return self.name
    elif self.type == 'element' and self.show:
      ret = self.name
      # hydrogens
      if self.show_hydrogens:
        v = self.get_free_valency()
        if v:
          h = 'H'
        else:
          h = ''
        if v > 1:
          h += '%d' % v
        if self.pos == 'center-last':
          ret = h + ret
        else:
          ret = ret + h
      # charge
      if self.charge:
        ch = ''
        if abs( self.charge) > 1:
          ch += str( abs( self.charge - self.get_charge_from_marks()))
        if self.charge -self.get_charge_from_marks() > 0:
          ch += '+'
        else:
          ch += '-'
      else:
        ch = ''
      if self.pos == 'center-last':
        return ch + ret
      else:
        return ret + ch
    elif self.type == 'chain':
      return PT.formula_dict( self.name).__str__( reverse=(self.pos=='center-last'))




  def get_ftext( self):
    if self.type == 'text':
      return self.name
    elif self.type == 'group':
      if self.pos == 'center-first':
        return GT.groups_table[ self.name.lower()]['textf']
      else:
        return GT.groups_table[ self.name.lower()]['textb']
    elif self.type == 'element':
      ret = self.name
      # hydrogens
      if self.show_hydrogens:
        v = self.get_free_valency()
        if v:
          h = 'H'
        else:
          h = ''
        if v > 1:
          h += '<sub>%d</sub>' % v
        if self.pos == 'center-last':
          ret = h + ret
        else:
          ret = ret + h
      # charge
      if self.charge -self.get_charge_from_marks():
        ch = ''
        if abs( self.charge) > 1:
          ch += str( abs( self.charge -self.get_charge_from_marks()))
        if self.charge -self.get_charge_from_marks() > 0:
          ch = '<sup>%s+</sup>' % ch
        else:
          ch = '<sup>%s-</sup>' % ch
      else:
        ch = ''
      if self.pos == 'center-last':
        return ch + ret
      else:
        return ret + ch
    elif self.type == 'chain':
      return PT.formula_dict( self.name).get_html_repr_as_string( reverse=(self.pos=='center-last'))






  def decide_pos( self):
    as = self.molecule.atoms_bound_to( self)
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




  def draw( self):
    "draws atom with respect to its properties"
    if self.item:
      warn( "drawing atom that is probably drawn", UserWarning, 2)
    x, y = self.x, self.y
    if self.show:
      self.update_font()
      if not self.pos:
        self.decide_pos()
      # we use self.text to force undo when it is changed (e.g. when atom is added to OH so it changes to O)
      self.text = self.get_ftext()
      parsed_name = dom.parseString( '<ftext>%s</ftext>' % self.text).childNodes[0]
      self.ftext = ftext( self.paper, xy=(self.x, self.y), dom=parsed_name, font=self.font, pos=self.pos, fill=self.line_color)
      self.ftext.draw()
      x1, y1, x2, y2 = self.ftext.bbox()
      self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('atom'))
      ## shrink the selector to improve appearance (y2-2)
      self.selector = self.paper.create_rectangle( x1, y1, x2, y2-3, fill=self.area_color, outline='',tags='helper_a')
      self.ftext.lift()
      self.paper.lift( self.item)
    else:
      self.item = self.paper.create_line( x, y, x, y, tags=("atom", 'nonSVG'), fill='')
      self.selector = None
    [m.draw() for m in self.marks.itervalues() if m]
    self.paper.register_id( self.item, self)
    # 
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
    [m.delete() for m in self.marks.itervalues() if m]
    # ...then we draw it again
    self.draw()
    if self._selected:
      self.select()
    else:
      self.unselect()
    if not self.dirty:
      pass
      #print "redrawing non-dirty atom"
    self.dirty = 0

      



  def focus( self):
    if self.show:
      self.paper.itemconfig( self.selector, fill='grey')
    else:
      x, y = self.x, self.y
      self.focus_item = self.paper.create_oval( x-4, y-4, x+4, y+4, tags='helper_f')
      self.paper.lift( self.item)




  def unfocus( self):
    if self.show:
      self.paper.itemconfig( self.selector, fill=self.area_color)
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None




  def select( self):
    if self.show:
      self.paper.itemconfig( self.selector, outline='black')
    else:
      x, y = self.x, self.y
      if self.selector:
        self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
      else:
        self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2)
      self.paper.lower( self.selector)
    self._selected = 1




  def unselect( self):
    if self.show:
      self.paper.itemconfig( self.selector, outline='')
      #self.paper.lower( self.selector)
    else:
      self.paper.delete( self.selector)
      self.selector = None
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
          if self.marks[m]:
            self.marks[m].move( dx, dy)
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
      if self.marks[m]:
        self.marks[m].delete()
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.unselect()
      if self.show:
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
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
    # marks (we read them here because they influence the charge)
    for m in package.getElementsByTagName( 'mark'):
      auto = (m.getAttribute( 'auto') != None and m.getAttribute( 'auto')) or 0
      if auto == True:
        auto = 1
      type = m.getAttribute( 'type')
      x, y, z = self.paper.read_xml_point( m)
      self.marks[ type] = marks.__dict__[ type]( self.paper,
                                                 x, y,
                                                 atom=self,
                                                 auto= int(auto))
    #self.show_number = a.index( package.getAttribute( 'show_number'))
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = self.paper.read_xml_point( position)
    if z != None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.x = x
    self.y = y
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name( reduce( operator.add, [e.toxml() for e in ft[0].childNodes], '').encode('utf-8'), check_valency=0, interpret=0)
    else:
      self.set_name( package.getAttribute( 'name'), check_valency=0)
    # charge
    self.charge = package.getAttribute('charge') and int( package.getAttribute('charge')) or 0
    # hydrogens
    if package.getAttribute( 'hydrogens'):
      self.show_hydrogens = package.getAttribute('hydrogens')
    else:
      self.show_hydrogens = 0
    # font and fill color
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    # show
    if package.getAttribute( 'show'):
      self.show = package.getAttribute( 'show')
    else:
      self.show = (self.name!='C')
    # background color
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # multiplicity
    if package.getAttribute( 'multiplicity'):
      self.multiplicity = int( package.getAttribute( 'multiplicity'))



  def get_package( self, doc):
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('atom')
    a.setAttribute( 'id', str( self.id))
    # charge
    if self.charge:
      a.setAttribute( "charge", str( self.charge))
    #show attribute is set only when non default
    if (self.show and self.name=='C') or (not self.show and self.name!='C'): 
      a.setAttribute('show', y[ self.show])
    if self.show:
      a.setAttribute( 'pos', self.pos)
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    if self.type == 'text':
      a.appendChild( dom.parseString( '<ftext>%s</ftext>' % self.name).childNodes[0])
    else:
      a.setAttribute( 'name', self.name)
      if self.show_hydrogens:
        a.setAttribute('hydrogens', on_off[self.show_hydrogens])
    if self.area_color != "#ffffff":
      a.setAttribute( 'background-color', self.area_color)
    # needed to support transparent handling of molecular size
    x, y, z = map( self.paper.px_to_text_with_unit, self.get_xyz( real=1))
    if self.z:
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y), ('z', z)))
    else: 
      dom_extensions.elementUnder( a, 'point', attributes=(('x', x), ('y', y)))
    # marks
    for m, o in self.marks.items():
      if o:
        x ,y = map( self.paper.px_to_text_with_unit, (o.x, o.y))
        dom_extensions.elementUnder( a, 'mark', attributes=(('type', m),
                                                            ('x', x),
                                                            ('y', y),
                                                            ('auto', str( int( o.auto)))))
    # multiplicity
    if self.multiplicity != 1:
      a.setAttribute( 'multiplicity', str( self.multiplicity))

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






  def get_free_valency( self, strict=0):
    """returns free valency of atom."""
    if not strict:
      while not self.get_free_valency( strict=1) >= 0:
        vals = list( PT.periodic_table[ self.name]['valency'])
        if self.valency not in vals:
          self.valency = vals[0]
        elif self.valency == vals[-1]:
          return 0
        else:
          self.valency = vals[ vals.index( self.valency) + 1]
      return self.get_free_valency( strict = 1)
    else:
      if self.type != 'element':
        return 4
      occupied_valency = self.get_occupied_valency()

      v = self.valency
      # should we increase or decrease valency with charge ?
      if self.charge:
        if abs( self.charge) > 1:
          # charges higher than one should always decrease valency
          charge = abs( self.charge)
        elif (self.name in PT.accept_cation) and (self.charge == 1) and (occupied_valency-1 <= PT.accept_cation[self.name]):
          # elements that can accept cations to increase their valency (NH4+)
          charge = -1
        elif (self.name in PT.accept_anion) and (self.charge == -1) and (occupied_valency-1 <= PT.accept_anion[self.name]):
          # elements that can accept anions to increase their valency (BH4-)
          charge = -1
        else:
          # otherwise charge reduces valency 
          charge = abs( self.charge)
      else:
        charge = 0
      return v-occupied_valency-charge-self.multiplicity+1

    



  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    if self.type == 'text':
      return PT.formula_dict()
    elif self.type == 'group':
      return PT.formula_dict( GT.groups_table[ self.name.lower()]['composition'])
    elif self.type == 'element':
      ret = PT.formula_dict( self.name)
      free_val = self.get_free_valency()
      if free_val > 0:
        ret['H'] = free_val
      return ret
    elif self.type == 'chain':
      return PT.formula_dict( self.name)




  def atoms_bound_to( self):
    """just link to molecule.atoms_bound_to()"""
    return self.molecule.atoms_bound_to( self)




  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    for m in self.marks.itervalues():
      if m:
        m.lift()
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)




  def set_mark( self, mark='radical', toggle=1, angle='auto'):
    """sets the mark and takes care of toggling and charge and multiplicity changes"""
    if mark in self.marks:
      if toggle:
        if self.marks[ mark]:
          self.marks[ mark].delete()
          self.marks[ mark] = None
          self._set_mark_helper( mark, sign=-1)
        else:
          self.create_mark( mark=mark, angle=angle)
          self._set_mark_helper( mark, sign=1)
      else:
        if not self.marks[ mark]:
          self.create_mark( mark=mark, angle=angle)
          self._set_mark_helper( mark, sign=1)



  def _set_mark_helper( self, mark, sign=1):
    if mark == 'plus':
      self.charge += 1*sign
    elif mark == 'minus':
      self.charge -= 1*sign
    elif mark == "radical":
      self.multiplicity += 1*sign
    elif mark == "biradical":
      self.multiplicity += 2*sign

    



  def create_mark( self, mark='radical', angle='auto', draw=1):
    """creates the mark, does not care about the chemical meaning of this"""
    # decide where to put the mark
    if angle == 'auto':
      x, y = self.find_place_for_mark( mark)
    else:
      x = self.x + round( cos( angle) *dist)
      y = self.y + round( sin( angle) *dist)
      #ang = angle

    self.marks[ mark] = marks.__dict__[ mark]( self.paper, x, y,
                                               atom = self,
                                               auto=(angle=='auto'))
    if draw:
      self.marks[ mark].draw()




  def reposition_marks( self):
    for k,m in self.marks.iteritems():
      if m and m.auto:
        self.set_mark( k, toggle=1)
        self.set_mark( k, toggle=1)



  def transform( self, tr):
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y, dont_move_marks=1)
    for m in self.marks.values():
      if m:
        m.transform( tr)




  def update_after_valency_change( self):
    if self.type == 'element' and self.show_hydrogens:
      self.redraw()




  def __str__( self):
    return self.id



  def get_charge_from_marks( self):
    return (self.marks['plus'] != None and 1) + (self.marks['minus'] != None and -1)




  def generate_marks_from_cheminfo( self):
    if self.charge == 1 and not self.marks[ 'plus']:
      self.create_mark( 'plus', draw=0)
    elif self.charge == -1 and not self.marks[ 'minus']:
      self.create_mark( 'minus', draw=0)
    if self.multiplicity == 2 and not self.marks[ 'radical']:
      self.create_mark( 'radical', draw=0)
    elif self.multiplicity == 3 and not self.marks[ 'biradical']:
      self.create_mark( 'biradical', draw=0)
  




  def get_occupied_valency( self):
    return self.molecule.get_atoms_occupied_valency( self)



  def set_valency_from_name( self):
    if self.type == 'element':
      for val in PT.periodic_table[ self.name]['valency']:
        self.valency = val
        try:
          fv = self.get_free_valency( strict=1)
        except:
          return  # this happens on read
        if fv >= 0:
          return
    elif self.type == 'group':
      self.valency = 0
    else:
      self.valency = 8  # any big value would do :)



  def find_place_for_mark( self, mark):
    if not self.show:
      dist = 5 + round( marks.__dict__[ mark].standard_size / 2)
    else:
      dist = 0.75*self.font_size + round( marks.__dict__[ mark].standard_size / 2)

    atms = self.molecule.atoms_bound_to( self)
    x, y = self.get_xy()

    # special cases
    if not atms:
      # single atom molecule
      if self.show_hydrogens and self.pos == "center-first":
        return x -dist, y-3
      else:
        return x +dist, y-3

    # normal case
    coords = [(a.x,a.y) for a in atms]
    # we have to take marks into account
    [coords.append( (self.marks[m].x, self.marks[m].y)) for m in self.marks if self.marks[m]]
    # hydrogen positioning is also important
    if self.show_hydrogens and self.show:
      if self.pos == 'center-last':
        coords.append( (x-10,y))
      else:
        coords.append( (x+10,y))
    # now we can compare the angles
    angles = [geometry.clockwise_angle_from_east( x1-x, y1-y) for x1,y1 in coords]
    angles.append( 2*pi + min( angles))
    angles.sort()
    angles.reverse()
    diffs = misc.list_difference( angles)
    i = diffs.index( max( diffs))
    angle = (angles[i] +angles[i+1]) / 2

    # in visible text x,y are not on the center, therefore we compensate for it
    if self.show:
      y -= 0.166 * self.font_size
    
    return x +dist*cos( angle), y +dist*sin( angle)
    

  def bbox( self):
    if self.item:
      return self.paper.bbox( self.item)
    else:
      # we have to calculate it, the atoms was not drawn yet
      if self.show:
        length = self.font.measure( self.get_text())
        if self.pos == 'center-first':
          dx = self.font.measure( self.get_text()[0]) / 2
          return (self.x + length - dx, self.y + 0.3*self.font_size, self.x - dx, self.y - 0.7*self.font_size) 
        else:
          dx = self.font.measure( self.get_text()[-1]) / 2
          return (self.x + dx, self.y + 0.3*self.font_size, self.x - length + dx, self.y - 0.7*self.font_size) 
      else:
        return self.x, self.y, self.x, self.y



  def split_element_and_charge( self, txt):
    """returns tuple of (element, charge) or None if the text does not match this pattern"""
    ### this could be a static method
    splitter = re.compile("^([a-z]+)([0-9]*)([+-]?)$")
    match = splitter.match( txt.lower())
    if match:
      if match.group(1).capitalize() not in PT.periodic_table:
        return None
      if match.group(3) == '+':
        charge = match.group(2) and int( match.group(2)) or 1
      elif match.group(3) == '-':
        charge = match.group(2) and -int( match.group(2)) or -1
      else:
        charge = 0
      return (match.group(1).capitalize(), charge)
    else:
      return None



