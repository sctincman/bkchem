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
from parents import meta_enabled


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself


### Class ATOM --------------------------------------------------
class atom( meta_enabled):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ



  object_type = 'atom'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo meta infos
  meta__undo_fake = ('text',)
  meta__undo_simple = ('x', 'y', 'z', 'pos', 'show', 'name', 'molecule', 'font_family',
                       'font_size', 'charge', 'show_hydrogens', 'type', 'line_color', 'area_color')
  meta__undo_copy = ('marks',)
  meta__undo_children_to_record = ('marks',)





  def __init__( self, paper, xy = (), package = None, molecule = None):
    meta_enabled.__init__( self, paper)
    # basic attrs
    self.molecule = molecule

    # presentation attrs
    self.selector = None
    self._selected = 0 #with ftext self.selector can no longer be used to determine if atom is selected
    self.item = None
    self.ftext = None
    if xy:
      self.set_xy( xy[0], xy[1])
    self.z = 0
    self.pos = None
    self.focus_item = None

    # chemistry attrs
    #   self.number = 0
    #   self.show_number = 0
    self.show_hydrogens = 0
    self.show = 0
    self.charge = 0
    self.marks = {'radical': None, 'biradical': None, 'electronpair': None,
                  'plus': None, 'minus': None}
    # used only for monitoring when undo is necessary, it does not always correspond to the atom name
    # only in case of self.show == 1
    self.text = ''

    if package:
      self.read_package( package)
    else:
      self.set_name( 'C')




  def set_name( self, name, interpret=1, check_valency=1):
    # every time name is set the charge should be set to zero
    self.charge = 0
    # name should not be interpreted
    if not interpret:
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'
      return
    # try to interpret name
    if name.lower() != 'c':
      self.show = 1
    else:
      self.show = 0
    if name.capitalize() in PT.periodic_table:
      # name is element symbol
      self.name = name.capitalize()
      self.show_hydrogens = 0
      self.type = 'element'
    elif (name.lower() in GT.groups_table) and ( not check_valency or self.molecule.get_atoms_valency( self) == 1):
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
        valency = self.molecule.get_atoms_valency( self)
        if form['H'] in [i-valency+self.charge for i in PT.periodic_table[a[0]]['valency']]:
          self.name = a[0]
          self.show_hydrogens = 1
          self.type = 'element'
          return
      # try if the name is an alkyl chain such as c6h13
      form = PT.formula_dict( name.upper())
      if form.is_saturated_alkyl_chain():
        self.name = str( form)
        self.show_hydrogens = 1
        self.type = 'chain'
        return
      # its nothing interesting - just text
      self.name = name
      self.show_hydrogens = 0
      self.type = 'text'




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
          ch += str( abs( self.charge))
        if self.charge > 0:
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
      if self.charge:
        ch = ''
        if abs( self.charge) > 1:
          ch += str( abs( self.charge))
        if self.charge > 0:
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

  # properties
  #name = property( get_name, set_name)




  def set_molecule( self, molecule):
    self.molecule = molecule




  def set_xy( self, x, y):
    self.x = self.paper.any_to_px( x) #round( x, 2)
    self.y = self.paper.any_to_px( y) #round( y, 2)




  def decide_pos( self):
    as = self.molecule.atoms_bound_to( self)
    p = 0
    for a in as:
      if a.get_x() < self.x:
        p -= 1
      elif a.get_x() > self.x:
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
      # we use self.text to force undo whet it is changed (e.g. when atom is added to OH so it changes to O)
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
      self.item = self.paper.create_line( x, y, x, y, tags=("atom", 'nonSVG'))
      self.selector = None
    [m.draw() for m in self.marks.itervalues() if m]
    self.paper.register_id( self.item, self)




  def redraw( self):
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
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move( dx, dy)
    if not dont_move_marks:
      for m in self.marks:
        if self.marks[m]:
          self.marks[m].move( dx, dy)




  def move_to( self, x, y, dont_move_marks=0):
    dx = x - self.x
    dy = y - self.y
    #self.set_xy( x, y)
    self.move( dx, dy, dont_move_marks=dont_move_marks)




  def get_x( self):
    return self.x




  def get_y( self):
    return self.y




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




  def round_coords( self, precision=0):
    self.x = round( self.x, precision)
    self.y = round( self.y, precision)




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
    self._cdml_id = package.getAttribute( 'id')
    #self.show_number = a.index( package.getAttribute( 'show_number'))
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = self.paper.read_xml_point( position)
    if z != None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.set_xy( x, y)
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name( reduce( operator.add, [e.toxml() for e in ft[0].childNodes], ''), check_valency=0, interpret=0)
    else:
      self.set_name( package.getAttribute( 'name'), check_valency=0)
    if package.getAttribute( 'hydrogens'):
      self.show_hydrogens = on_off.index( package.getAttribute('hydrogens'))
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
      self.show = a.index( package.getAttribute( 'show'))
    else:
      self.show = (self.name!='C')
    # background color
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # marks
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
                          





  def get_package( self, doc):
    y = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('atom')
    a.setAttribute( 'id', str( self.get_cdml_id()))
    #show attribute is set only when non default
    if (self.show and self.name=='C') or (not self.show and self.name!='C'): 
      a.setAttribute('show', y[ self.show])
    if self.show:
      a.setAttribute( 'pos', self.pos)
    if self.font_size != 12 or self.font_family != 'helvetica' or self.line_color != '#000':
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != '#000':
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
    for m, o in self.marks.items():
      if self.marks[m]:
        x ,y = map( self.paper.px_to_text_with_unit, (o.x, o.y))
        dom_extensions.elementUnder( a, 'mark', attributes=(('type', m),
                                                            ('x', x),
                                                            ('y', y),
                                                            ('auto', str( int( o.auto)))))
    return a




  def get_cdml_id( self):
    if self.item:
      self._cdml_id = 'a'+str( self.item)
    return self._cdml_id




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




  def get_valency( self):
    return self.molecule.get_atoms_valency( self)




  def get_free_valency( self):
    """returns free valency of atom."""
    if self.type != 'element':
      return 0
    valency = self.molecule.get_atoms_valency( self)
    if self.name in PT.periodic_table:
      vals = PT.periodic_table[ self.name]['valency']
      for v in vals:
        # should we increase or decrease valency with charge ?
        if self.charge:
          if abs( self.charge) > 1:
            # charges higher than one should always decrease valency
            charge = abs( self.charge)
          elif (self.name in PT.accept_cation) and (self.charge == 1) and (valency-1 <= PT.accept_cation[self.name]):
            # elements that can accept cations to increase their valency (NH4+)
            charge = -1
          elif (self.name in PT.accept_anion) and (self.charge == -1) and (valency-1 <= PT.accept_anion[self.name]):
            # elements that can accept anions to increase their valency (BH4-)
            charge = -1
          else:
            # otherwise charge reduces valency 
            charge = abs( self.charge)
        else:
          charge = 0
        if valency+charge <= v:
          return v-valency-charge
      # if valency is exceeded return lowest possible negative value
      return max( PT.periodic_table[ self.name]['valency']) - valency - charge
    # if unsuccessful return 0
    return 0
    



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
    for m in self.marks.itervalues():
      if m:
        m.lift()
    if self.selector:
      self.paper.lift( self.selector)
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)




  def set_mark( self, mark='radical', toggle=1, angle='auto'):
    if mark in self.marks:
      if toggle:
        if self.marks[ mark]:
          self.marks[ mark].delete()
          self.marks[ mark] = None
        else:
          self.create_mark( mark=mark, angle=angle)
      else:
        if not self.marks[ mark]:
          self.create_mark( mark=mark, angle=angle)




  def create_mark( self, mark='radical', angle='auto'):
    if self.show:
      dist = self.font_size/2 + round( marks.__dict__[ mark].standard_size/2) + 2
    else:
      dist = 5 + round( marks.__dict__[ mark].standard_size / 2)
    if angle == 'auto':
      x, y = self.molecule.find_least_crowded_place_around_atom( self, range=dist)
      #ang = round( geometry.clockwise_angle_from_east( x -self.x, y -self.y))
    else:
      x = self.x + round( cos( angle) *dist)
      y = self.y + round( sin( angle) *dist)
      #ang = angle

    self.marks[ mark] = marks.__dict__[ mark]( self.paper, x, y,
                                               atom = self,
                                               auto=(angle=='auto'))
    self.marks[ mark].draw()




  def reposition_marks( self):
    for m in self.marks.itervalues():
      if m and m.auto:
        if self.show:
          dist = self.font_size/2 + round( m.size/2) + 2
        else:
          dist = 5 + round( m.size / 2)
        x, y = self.molecule.find_least_crowded_place_around_atom( self, range=dist)
        m.move_to( x, y)




  def transform( self, tr):
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y, dont_move_marks=1)
    for m in self.marks.values():
      if m:
        m.transform( tr)




  def update_after_valency_change( self):
    if self.type == 'element' and self.show_hydrogens:
      self.redraw()
