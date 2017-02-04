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

"""Home for atom class.

"""

from __future__ import division

import re
import sys
import oasa

from warnings import warn

import data
import marks
import dom_extensions

from oasa import periodic_table as PT
from singleton_store import Screen, Store
from special_parents import drawable_chem_vertex


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefore these values are
### not set in __init__ itself


class atom(drawable_chem_vertex, oasa.atom):
  # note that all children of simple_parent have default meta infos set
  # therefore it is not necessary to provide them for all new classes if they
  # don't differ

  object_type = 'atom'
  meta__undo_properties = drawable_chem_vertex.meta__undo_properties + \
                          ( 'show', 'show_hydrogens',
                            'multiplicity', 'valency', 'free_sites')


  def __init__( self, standard=None, xy=(), package=None, molecule=None):
    drawable_chem_vertex.__init__( self, standard=standard, xy=xy, molecule=molecule)
    if xy:
      oasa.atom.__init__( self, coords=(xy[0],xy[1],0))
    else:
      oasa.atom.__init__( self)

    # chemistry attrs
    self.show = 0
    self.multiplicity = 1

    if package:
      self.read_package( package)
    else:
      self.set_name( 'C')


  # Override the oasa.atom.symbol property
  @property
  def symbol(self):
    """Atom symbol.

    """
    return self._symbol


  @symbol.setter
  def symbol(self, symbol):
    oasa.atom.symbol.__set__(self, symbol)
    if self._symbol != 'C':
      self.show = True


  @property
  def show(self):
    """Should the atom symbol be displayed?

    Accepts both 0|1 and yes|no.
    """
    return self._show


  @show.setter
  def show(self, show):
    if show in data.booleans:
      self._show = data.booleans.index(show)
    else:
      self._show = int(show)
    self.dirty = 1
    self._reposition_on_redraw = 1


  @property
  def show_hydrogens(self):
    return self._show_hydrogens


  @show_hydrogens.setter
  def show_hydrogens(self, show_hydrogens):
    if show_hydrogens in data.on_off:
      self._show_hydrogens = data.on_off.index( show_hydrogens)
    else:
      self._show_hydrogens = int( show_hydrogens)
    self.dirty = 1
    self._reposition_on_redraw = 1


  # Override of oasa.chem_vertex.charge
  @property
  def charge(self):
    return drawable_chem_vertex.charge.__get__(self)


  @charge.setter
  def charge(self, charge):
    drawable_chem_vertex.charge.__set__(self, charge)
    self.dirty = 1


  @property
  def valency(self):
    """Atom's (maximum) valency.

    Used for hydrogen counting.
    """
    try:
      self._valency
    except AttributeError:
      self.set_valency_from_name()
    return self._valency


  @valency.setter
  def valency(self, val):
    drawable_chem_vertex.valency.__set__(self, val)


  # Replace oasa.atom.free_sites
  @property
  def free_sites(self):
    """Free sites of the atom.

    """
    return self._free_sites


  @free_sites.setter
  def free_sites(self, free_sites):
    self._free_sites = free_sites
    marks = self.get_marks_by_type( "free_sites")
    if self._free_sites:
      if not marks:
        self.create_mark( "free_sites", draw=self.drawn)
      elif self.drawn:
        marks[0].redraw()
    else:
      if marks:
        self.remove_mark( "free_sites")


  @property
  def free_sites_text(self):
    """Atom's free_sites as text.

    Used by free-site mark.
    """
    if self.free_sites:
      return "[%d]" % self.free_sites
    else:
      return ""


  # Oxidation number as text
  @property
  def oxidation_number_text(self):
    """Atom's oxidation number as text.

    """
    return data.roman_numbers[self.oxidation_number]


  # Override drawable_chem_vertex.xml_ftext
  @property
  def xml_ftext(self):
    """Text used for rendering using the ftext class.

    """
    ret = self.symbol
    if not self.pos:
      self.decide_pos()
    # hydrogens
    if self.show_hydrogens:
      v = self.free_valency
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
        ch = '<sup>%s%s</sup>' % (ch, self.paper.get_paper_property('use_real_minus') and unichr(8722) or "-")
    else:
      ch = ''
    if self.pos == 'center-last':
      ret = ch + ret
    else:
      ret = ret + ch
    return ret.encode('utf-8')


  ## -------------------- OVERRIDES OF CHEM_VERTEX METHODS --------------------
  def decide_pos( self):
    if self.show_hydrogens or self.free_valency:
      # in case hydrogens are shown, use the chem_vertex.decide_pos algorithm
      drawable_chem_vertex.decide_pos( self)
    else:
      #  otherwise always center the first letter
      self.pos = "center-first"


  ## // -------------------- END --------------------


  def set_name( self, name, interpret=1, check_valency=1, occupied_valency=None):
    ret = self._set_name( name, interpret=interpret, check_valency=check_valency, occupied_valency=occupied_valency)
    self.set_valency_from_name()
    return ret


  def _set_name( self, name, interpret=1, check_valency=1, occupied_valency=None):
    if sys.version_info[0] > 2:
      if isinstance(name, bytes):
        name = name.decode('utf-8')
    else:
      if isinstance(name, str):
        name = name.decode('utf-8')
    # every time name is set the charge should be set to zero or the value specified by marks
    self.charge = self.get_charge_from_marks()
    self.dirty = 1
    # try to interpret name
    if name.lower() != 'c':
      self.show = 1
    else:
      self.show = 0
    elch = self.split_element_and_charge( name)
    if elch:
      # name is element symbol + charge
      self.symbol = elch[0]
      #self.show_hydrogens = 0
      self.charge += elch[1]
      return True
    else:
      # try if name is hydrogenated form of an element
      form = PT.text_to_hydrogenated_atom( name)
      if form:
        # it is!
        a = form.keys()
        a.remove( 'H')
        if occupied_valency is None:
          valency = self.occupied_valency
        else:
          valency = occupied_valency
        if form['H'] in [i-valency+self.charge for i in PT.periodic_table[a[0]]['valency']]:
          self.symbol = a[0]
          self.show_hydrogens = 1
          # decide hydrogen placement based on how the name was written (only if it has no neighbor)
          if occupied_valency:
            self.pos = None # decide later
          else:
            if name.lower().find( "h") < name.lower().find( self.symbol.lower()):
              self.pos = "center-last"
            else:
              self.pos = "center-first"
          #self.show = 1
          return True
    return False


  def draw( self, redraw=False):
    "draws atom with respect to its properties"
    
    # Here we scale the coordinates, as self.vertex_item is not defined yet.
    x, y = self.x*self.paper._scale, self.y*self.paper._scale
    
    if self.show:
      # Vertex_item defines the position of the vertex on the canvas (for bonding). 
      self.vertex_item = self.paper.create_line( x, y, x, y, tags=("no_export"))
      # Draws the atom label
      drawable_chem_vertex.draw( self, redraw=redraw)
    else:
      if self.item:
        warn( "drawing atom that is probably drawn", UserWarning, 2)
      self.item = self.paper.create_line( x, y, x, y, tags=("atom", 'nonSVG'), fill='')
      # Vertex_item is item if the atom is not shown.
      self.vertex_item = self.item
      # Generate selector
      self.selector = None
      if not redraw:
        [m.draw() for m in self.marks]
      self.paper.register_id( self.item, self)
      self._reposition_on_redraw = 0


  def focus( self):
    # Since selection has to do merely with GUI, item coords are used instead of real atom position
    if self.show:
      drawable_chem_vertex.focus( self)
    else:
      x, y = self.paper.coords(self.item)[0:2] 
      self.focus_item = self.paper.create_oval( x-4, y-4, x+4, y+4, tags=('helper_f','no_export'), outline=self.paper.highlight_color)
      self.paper.lift( self.item)


  def unfocus( self):
    if self.show:
      drawable_chem_vertex.unfocus( self)
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None


  def select( self):
    # Since selection has to do merely with GUI, item coords are used instead of real atom position
    if self.show:
      drawable_chem_vertex.select( self)
    else:
      x, y = self.paper.coords(self.item)[0:2]
      if self.selector:
        self.paper.coords( self.selector, x-2, y-2, x+2, y+2)
      else:
        self.selector = self.paper.create_rectangle( x-2, y-2, x+2, y+2, outline=self.paper.highlight_color)
      self.paper.lower( self.selector)
      self._selected = 1


  def unselect( self):
    if self.show:
      drawable_chem_vertex.unselect( self)
    else:
      self.paper.delete( self.selector)
      self.selector = None
      self._selected = 0


  def read_package( self, package):
    """reads the dom element package and sets internal state according to it"""
    a = ['no','yes']
    on_off = ['off','on']
    self.id = package.getAttribute( 'id')
    # marks (we read them here because they influence the charge)
    for m in package.getElementsByTagName( 'mark'):
      mrk = marks.mark.read_package( m, self)
      self.marks.add( mrk)
    self.pos = package.getAttribute( 'pos')
    position = package.getElementsByTagName( 'point')[0]
    # reading of coords regardless of their unit
    x, y, z = Screen.read_xml_point( position)
    if z is not None:
      self.z = z* self.paper.real_to_screen_ratio()
    # needed to support transparent handling of molecular size
    x, y = self.paper.real_to_screen_coords( (x, y))
    self.x = x
    self.y = y
    ft = package.getElementsByTagName('ftext')
    if ft:
      self.set_name(''.join([e.toxml('utf-8') for e in ft[0].childNodes]),
                    check_valency=0,
                    interpret=0)
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
      self.show = (self.symbol!='C')
    # background color
    if package.getAttributeNode( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
    # multiplicity
    if package.getAttribute( 'multiplicity'):
      self.multiplicity = int( package.getAttribute( 'multiplicity'))
    # valency
    if package.getAttribute( 'valency'):
      self.valency = int( package.getAttribute( 'valency'))
    # number
    if package.getAttribute( 'show_number'):
      self.show_number = bool( data.booleans.index( package.getAttribute( 'show_number')))
    if package.getAttribute( 'number'):
      self.number = package.getAttribute( 'number')
    # free_sites
    if package.getAttribute( 'free_sites'):
      self.free_sites = int( package.getAttribute( 'free_sites'))


  def get_package( self, doc):
    """returns a DOM element describing the object in CDML,
    doc is the parent document which is used for element creation
    (the returned element is not inserted into the document)"""
    yes_no = ['no','yes']
    on_off = ['off','on']
    a = doc.createElement('atom')
    a.setAttribute( 'id', str( self.id))
    # charge
    if self.charge:
      a.setAttribute( "charge", str( self.charge))
    #show attribute is set only when non default
    if (self.show and self.symbol=='C') or (not self.show and self.symbol!='C'):
      a.setAttribute('show', yes_no[ self.show])
    if self.show:
      a.setAttribute( 'pos', self.pos)
    if self.font_size != self.paper.standard.font_size \
       or self.font_family != self.paper.standard.font_family \
       or self.line_color != self.paper.standard.line_color:
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != self.paper.standard.line_color:
        font.setAttribute( 'color', self.line_color)
    a.setAttribute( 'name', self.symbol)
    if self.show_hydrogens:
      a.setAttribute('hydrogens', on_off[self.show_hydrogens])
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
    # multiplicity
    if self.multiplicity != 1:
      a.setAttribute( 'multiplicity', str( self.multiplicity))
    # valency
    a.setAttribute( 'valency', str( self.valency))
    # number
    if self.number:
      a.setAttribute( 'number', self.number)
      a.setAttribute( 'show_number', data.booleans[ int( self.show_number)])
    # free_sites
    if self.free_sites:
      a.setAttribute( 'free_sites', str( self.free_sites))
    return a


  def get_formula_dict( self):
    """returns formula as dictionary that can
    be passed to functions in periodic_table"""
    ret = PT.formula_dict( self.symbol)
    if self.free_valency > 0:
      ret['H'] = self.free_valency
    return ret


  # overrides special_parents.drawable_chem_vertex method
  def _set_mark_helper( self, mark, sign=1):
    drawable_chem_vertex._set_mark_helper( self, mark, sign=sign)
    mark, _ = self._mark_to_name_and_class( mark)
    if mark == 'plus':
      self.charge += 1*sign
    elif mark == 'minus':
      self.charge -= 1*sign
    elif mark == "radical":
      self.multiplicity += 1*sign
    elif mark == "biradical":
      self.multiplicity += 2*sign


  def update_after_valency_change( self):
    if self.free_valency <= 0:
      self.raise_valency_to_senseful_value()
    if self.show_hydrogens:
      self.redraw()


  def __str__( self):
    return self.id


  def get_charge_from_marks( self):
    res = 0
    for m in self.marks:
      if m.__class__.__name__ == 'plus':
        res += 1
      elif m.__class__.__name__ == "minus":
        res -= 1
    return res


  def generate_marks_from_cheminfo( self):
    if self.charge == 1 and not self.get_marks_by_type( 'plus'):
      self.create_mark( 'plus', draw=0)
    elif self.charge == -1 and not self.get_marks_by_type( 'minus'):
      self.create_mark( 'minus', draw=0)
    if self.multiplicity == 2 and not self.get_marks_by_type( 'radical'):
      self.create_mark( 'radical', draw=0)
    elif self.multiplicity == 3 and not (self.get_marks_by_type( 'biradical') or len( self.get_marks_by_type( 'radical')) == 2):
      self.create_mark( 'biradical', draw=0)


  def set_valency_from_name( self):
    for val in PT.periodic_table[ self.symbol]['valency']:
      self.valency = val
      try:
        fv = self.free_valency
      except:
        return  # this happens on read
      if fv >= 0:
        return


  def bbox( self, substract_font_descent=False):
    """returns the bounding box of the object as a list of [x1,y1,x2,y2]"""
    if self.show:
      return drawable_chem_vertex.bbox( self, substract_font_descent=substract_font_descent)
    else:
      if self.item:
        return self.paper.bbox( self.item)
      else:
        # we have to calculate it, the atoms was not drawn yet
        return self.x, self.y, self.x, self.y


  ##LOOK  (make static)
  def split_element_and_charge( self, txt):
    """returns tuple of (element, charge) or None if the text does not match this pattern"""
    ### this could be a static method
    splitter = re.compile("^([a-z]+)([0-9]*)([+-]?)$")
    matcher = re.compile( "^([a-z]+)([0-9]*[+-])?$")
    if not matcher.match( txt.lower()):
      return None
    match = splitter.match( txt.lower())
    if match:
      if match.group(1).capitalize() not in PT.periodic_table or 'query' in PT.periodic_table[ match.group(1).capitalize()].keys():
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


  def after_undo( self):
    """this is run after undo"""
    self._clean_cache()

