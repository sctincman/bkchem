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


"""set of basic classes such as arrow, standard, plus, text etc.
also imports atom, bond and molecule from historical reasons :)"""

from __future__ import division
from __future__ import generators

from math import atan2, sin, cos, pi, sqrt
import misc
from warnings import warn
from ftext import ftext
import dom_extensions
import xml.dom.minidom as dom
import operator
import tkFont
from parents import meta_enabled, container, with_line, text_like, line_colored
from parents import area_colored, point_drawable, interactive, drawable, top_level
from parents import child


### NOTE: now that all classes are children of meta_enabled, so the read_standard_values method
### is called during their __init__ (in fact meta_enabled.__init__), therefor these values are
### not set in __init__ itself



##-------------------- STANDARD CLASS ------------------------------

class standard:

  def __init__( self):
    # common
    self.line_width = '1px'
    self.font_size = 12
    self.font_family = 'helvetica'
    self.line_color = "#000"
    self.area_color = '#ffffff'
    # bond
    self.bond_length = '1cm'
    self.bond_width = '6px'
    self.wedge_width = '5px'
    self.double_length_ratio = 0.75
    # arrow
    self.arrow_length = '1.6cm'
    # paper
    self.paper_type = 'A4'
    self.paper_orientation = 'portrait'
    self.paper_crop_svg = 0


  def __eq__( self, other):
    for (k,v) in self.__dict__.iteritems():
      if str( v) != str( other.__dict__[ k]):
        return 0
    return 1

  def __ne__( self, other):
    return not self.__eq__( other)


  def get_package( self, doc):
    ret = doc.createElement( 'standard')
    dom_extensions.setAttributes( ret, (('line_width', str( self.line_width)),
                                        ('font_size', str( self.font_size)),
                                        ('font_family', str( self.font_family)),
                                        ('line_color', self.line_color),
                                        ('area_color', self.area_color),
                                        ('paper_type', self.paper_type),
                                        ('paper_orientation', self.paper_orientation),
                                        ('paper_crop_svg', str( self.paper_crop_svg))))
    dom_extensions.elementUnder( ret, 'bond', (('length', str( self.bond_length)),
                                               ('width', str( self.bond_width)),
                                               ('wedge-width', str( self.wedge_width)),
                                               ('double-ratio', str( self.double_length_ratio))))
    dom_extensions.elementUnder( ret, 'arrow', (('length', str( self.arrow_length)),))
    return ret

  def read_package( self, p):
    for attr in ('line_width', 'font_size', 'font_family', 'line_color','area_color',
                 'paper_crop_svg','paper_orientation','paper_type'):
      if p.getAttribute( attr):
        self.__dict__[ attr] = p.getAttribute( attr)
    self.font_size = int( self.font_size)
    self.paper_crop_svg = int( self.paper_crop_svg)
    b = dom_extensions.getFirstChildNamed( p, 'bond')
    if b:
      self.bond_length = b.getAttribute( 'length') or self.bond_length
      self.bond_width = b.getAttribute( 'width') or self.bond_width
      self.double_length_ratio = b.getAttribute( 'double-ratio') or self.double_length_ratio
      self.double_length_ratio = float( self.double_length_ratio)
      self.wedge_width = b.getAttribute( 'wedge-width') or self.wedge_width
    a = dom_extensions.getFirstChildNamed( p, 'arrow')
    if a:
      self.arrow_length = a.getAttribute( 'length')
      
    

##-------------------- ARROW CLASS ------------------------------

class arrow( meta_enabled, drawable, with_line, line_colored, container, interactive, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  _pins = ['none', 'last', 'first', 'both']
  object_type = 'arrow'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color']
  # other meta infos
  meta__is_container = 1
  # undo related metas
  meta__undo_simple = ('pin', 'spline')
  meta__undo_properties = with_line.meta__undo_properties + \
                          line_colored.meta__undo_properties
  meta__undo_copy = ('points',)
  meta__undo_children_to_record = ('points',)



  def __init__( self, paper, points=[], shape=(8,10,3), pin=1, spline=0, package=None, fill="#000"):
    meta_enabled.__init__( self, paper)
    drawable.__init__( self)
    with_line.__init__( self)
    line_colored.__init__( self)

    self.points = []
    self.spline = spline
    self.paper = paper
    self.shape = shape
    self.item = None
    self.pin = 1
    if points:
      for p in points:
        pnt = point( self.paper, p[0], p[1], arrow=self)
        self.points.append( pnt)
    if package:
      self.read_package( package)


  # PROPERTIES

  # shape_defining_points
  def __get_shape_defining_points( self):
    return self.points

  shape_defining_points = property( __get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")

  # // PROPERTIES


  def read_standard_values( self, old_standard=None):
    meta_enabled.read_standard_values( self, old_standard=old_standard)
    if not old_standard or (self.paper.standard.line_width != old_standard.line_width):
      self.line_width = self.paper.any_to_px( self.paper.standard.line_width)    
    


  def draw( self):
    if len( self.points) > 1:
      #type = self.spline and 'circle' or 'invisible'
      type = 'invisible'
      for p in self.points:
        p.type = type
      [pnt.draw() for pnt in self.points]
      ps = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
      self.item = self.paper.create_line( ps, tags='arrow', arrow=self._pins[ self.pin], arrowshape=self.shape,\
                                          width=self.line_width, smooth=self.spline, fill=self.line_color)
      self.paper.register_id( self.item, self)
    
  def redraw( self):
    if not self.item:
      self.draw()
    else:
      if len( self.points) > 1:
        #type = self.spline and 'circle' or 'invisible'
        type = 'invisible'
        [pnt.change_type( type) for pnt in self.points]
        ps = reduce( operator.add, map( lambda b: b.get_xy(), self.points))
        self.paper.coords( self.item, ps)
        self.paper.itemconfig( self.item, arrow=self._pins[ self.pin], arrowshape=self.shape,\
                               width=self.line_width, smooth=self.spline, fill=self.line_color)

  def focus( self):
    self.paper.itemconfig( self.item, width = self.line_width+2)

  def unfocus( self):
    self.paper.itemconfig( self.item, width = self.line_width)

#  def get_id( self):
#    return self.id

  def select( self):
    #self.selector = hg.selection_rect( self.paper, self, coords=self.bbox())
    [pnt.select() for pnt in self.points]

  def unselect( self):
    #self.selector.delete()
    [pnt.unselect() for pnt in self.points]

  def create_new_point( self, x, y, position=-1):
    "creates new point, position specifies relative position of point in points, usualy -1 or 0"
    pnt = point( self.paper, xy=(x,y), arrow=self)
    if position < 0:
      self.points.append( pnt)
    else:
      try:
        self.points.insert( position, pnt)
      except IndexError:
        self.points.append( pnt)
        warn( "bad position for adding point in arrow", UserWarning, 2)
    return pnt

  def delete_point( self, pnt):
    try:
      self.points.remove( pnt)
    except IndexError:
      warn( "trying to remove nonexisting point from arrow")
    pnt.delete()

  def delete( self):
    [p.delete() for p in self.points]
    self.points = []
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    self.item = None

  def is_empty_or_single_point( self):
    return len( self.points) < 2 

  def move( self, dx, dy):
    [p.move( dx, dy) for p in self.points]
    self.redraw()

  def read_package( self, package):
    a = ['no', 'yes']
    start = a.index( package.getAttribute( 'start'))
    end = a.index( package.getAttribute( 'end'))
    if start and end:
      self.pin = 3
    elif start:
      self.pin = 2
    elif end:
      self.pin = 1
    else:
      self.pin = 0
    self.spline = a.index( package.getAttribute( 'spline'))
    self.line_width = float( package.getAttribute( 'width'))
    #self.shape = package.getAttribute( 'shape')
    self.line_color = package.getAttribute( 'color')
    for p in package.getElementsByTagName( 'point'):
      self.points.append( point( self.paper, arrow=self, package=p))
  
  def get_package( self, doc):
    a = ['no', 'yes']
    arr = doc.createElement('arrow')
    start, end = 0, 0
    if self.pin == 2 or self.pin == 3:
      start = 1
    if self.pin == 1 or self.pin ==3:
      end = 1
    dom_extensions.setAttributes( arr, (('shape', str( self.shape)),
                                       ('spline', a[self.spline]),
                                        ('width', str( self.line_width)),
                                        ('start', a[start]),
                                        ('end', a[end]),
                                        ('color', str( self.line_color))))
    for p in self.points:
      arr.appendChild( p.get_package( doc))
    return arr

  def change_direction( self):
    self.pin += 1
    if self.pin > 3:
      self.pin = 0
    self.redraw()

  def bbox( self):
    return self.paper.bbox( self.item)

  def set_pins( self, start=None, end=None):
    st, en = self.get_pins()      
    if start != None:
      st = start
    if end != None:
      en = end
    self.pin = en + 2*st

  def get_pins( self):
    """returns tuple of boolean values (start, end)"""
    return divmod( self.pin, 2)

  def lift( self):
    if self.item:
      self.paper.lift( self.item)
    [o.lift() for o in self.points]



## -------------------- POINT CLASS ------------------------------

class point( point_drawable, interactive, child):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'point'

  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties
  

  def __init__( self, paper, xy=(), arrow=None, package=None, type='invisible'):
    point_drawable.__init__( self)
    if xy:
      self.x, self.y = xy
    self.paper = paper
    self.item = None
    self.focus_item = None
    self.selector = None
    self.type = type
    if arrow:
      self.arrow = arrow
    if package:
      self.read_package( package)

  def set_arrow( self, arrow):
    self.arrow = arrow

  def draw( self):
    if self.item:
      self.redraw()
    else:
      if self.type == 'invisible':
        self.item = self.paper.create_line( self.x, self.y, self.x, self.y, tags='point')
      elif self.type == 'circle':
        self.item = self.paper.create_oval( self.x-2, self.y-2, self.x+2, self.y+2, fill='grey', outline='grey', tags='point')
      else:
        warn( 'unknown point type')
        return 
      self.paper.register_id( self.item, self)

  def redraw( self):
    if not self.item:
      self.draw()
    else:
      self.paper.delete( self.item)
      self.item = None
      self.draw()
      if self.selector:
        self.paper.coords( self.selector, self.x-2, self.y-2, self.x+2, self.y+2)

  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    if not self.item:
      self.x = x
      self.y = y
      self.draw()
    else:
      dx = x -self.x
      dy = y -self.y
      self.move( dx, dy)

  def focus( self):
    self.focus_item = self.paper.create_oval( self.x-4, self.y-4, self.x+4, self.y+4)
    if self.item:
      self.paper.lift( self.item)

  def unfocus( self):
    if self.focus_item:
      self.paper.delete( self.focus_item)
      self.focus_item = None

  def select( self):
    if not self.selector:
      self.selector = self.paper.create_rectangle( self.x-2, self.y-2, self.x+2, self.y+2)
      self.paper.lower( self.selector)

  def unselect( self):
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    
  def get_xy( self):
    return self.x, self.y

  def delete( self):
    self.unselect()
    self.unfocus()
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
      self.item = None

  def read_package( self, package):
    x, y, z = self.paper.read_xml_point( package)
    self.x, self.y = self.paper.real_to_screen_coords( (x,y))
    #self.z = int( package.getAttribute( 'z') )
  
  def get_package( self, doc):
    pnt = doc.createElement('point')
    x, y = map( self.paper.px_to_text_with_unit, self.paper.screen_to_real_coords( (self.x, self.y)))
    dom_extensions.setAttributes( pnt, (('x', x),
                                        ('y', y)))
    return pnt

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

  def change_type( self, type):
    self.type = type
    self.redraw()


  # parent
  def __get_parent( self):
    return self.molecule

  parent = property( __get_parent, None, None,
                     "returns self.molecule")








##-------------------- PLUS CLASS ------------------------------

class plus( meta_enabled, interactive, point_drawable, text_like, area_colored, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'plus'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_family']
  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties +\
                          text_like.meta__undo_properties +\
                          area_colored.meta__undo_properties

  def __init__( self, paper, xy=(), package=None):
    meta_enabled.__init__( self, paper)
    point_drawable.__init__( self)
    text_like.__init__( self)
    area_colored.__init__( self)

    self.x = self.y = None
    self.focus_item = None
    self.selector = None
    self._selected = 0
    self.font_size = 20
    if xy:
      self.x, self.y = xy
    if package:
      self.read_package( package)
    # standard values
    self.update_font()
    
  def draw( self):
    self.update_font()
    self.item = self.paper.create_text( self.x, self.y, text='+', tags='plus', font = self.font, fill=self.line_color)
    self.paper.register_id( self.item, self)
    self.selector = self.paper.create_rectangle( self.paper.bbox( self.item), fill=self.area_color, outline=self.area_color)
    self.paper.lift( self.item)

  def redraw( self):
    self.update_font()
    self.paper.coords( self.item, self.x, self.y)
    self.paper.itemconfig( self.item, font = self.font, fill=self.line_color)
    if self.selector:
      self.paper.coords( self.selector, self.paper.bbox( self.item))
      self.paper.itemconfig( self.selector, fill=self.area_color, outline=self.area_color)

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='grey')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def get_id( self):
    return self.item

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1
 
  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0
    
  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy)

  def read_package( self, package):
    pnt = package.getElementsByTagName( 'point')[0]
    self.x, self.y, z = self.paper.read_xml_point( pnt)
    if package.getAttribute( 'font_size'):
      self.font_size = int( package.getAttribute( 'font_size')) 
    if package.getAttribute( 'color'):
      self.line_color = package.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')
  
  def get_package( self, doc):
    pls = doc.createElement('plus')
    x, y = self.paper.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( pls, 'point', (('x', x),
                                                ('y', y)))
    pls.setAttribute('font_size', str( self.font_size))
    if self.line_color != '#000':
      pls.setAttribute( 'color', self.line_color)
    if self.area_color != '#ffffff':
      pls.setAttribute( 'background-color', self.area_color)
    return pls

  def delete( self):
    self.paper.delete( self.selector)
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)

  def get_xy( self):
    return self.x, self.y

  def bbox( self):
    return self.paper.bbox( self.item)

  def scale_font( self, ratio):
    """scales font of plus. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()

  def update_font( self):
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)

  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.item:
      self.paper.lift( self.item)

##--------------------TEXT CLASS--------------------

class text( meta_enabled, interactive, point_drawable, text_like, area_colored, top_level):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'text'
  # these values will be automaticaly read from paper.standard on __init__
  meta__used_standard_values = ['line_color','area_color','font_size','font_family']
  # undo related metas
  meta__undo_properties = point_drawable.meta__undo_properties +\
                          text_like.meta__undo_properties +\
                          area_colored.meta__undo_properties
  meta__undo_simple = ('text',)

  def __init__( self, paper, xy=(), text='', package=None):
    text_like.__init__( self)
    point_drawable.__init__( self)
    area_colored.__init__( self)
    meta_enabled.__init__( self, paper)
    
    self.selector = None
    self._selected = 0
    self.ftext = None
    if xy:
      self.set_xy( xy[0], xy[1])
    self.set_text( text)
    self.item = None
    if package:
      self.read_package( package)
    self.focus_item = None


  # public methods

  def set_xy( self, x, y):
    self.x = round( x, 2)
    self.y = round( y, 2)

  def draw( self):
    "draws text"
    self.update_font()
    self.ftext = ftext( self.paper, xy=(self.x, self.y), dom=self.parsed_text, font=self.font, fill=self.line_color)
    self.ftext.draw()
    x1, y1, x2, y2 = self.ftext.bbox()
    self.item = self.paper.create_rectangle( x1, y1, x2, y2, fill='', outline='', tags=('text'))
    self.selector = self.paper.create_rectangle( x1, y1, x2, y2, fill=self.area_color, outline='', tags='helper_a')
    self.ftext.lift()
    self.paper.lift( self.item)
    self.paper.register_id( self.item, self)

  def redraw( self):
    self.paper.unregister_id( self.item)
    self.paper.delete( self.item)
    if self.selector:
      self.paper.delete( self.selector)
    if self.ftext:
      self.ftext.delete()
    self.draw()
    if self._selected:
      self.select()

  def focus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill='gray')

  def unfocus( self):
    if self.selector:
      self.paper.itemconfig( self.selector, fill=self.area_color)

  def select( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline='black')
    self._selected = 1




  def unselect( self):
    if self.selector:
      self.paper.itemconfig( self.selector, outline=self.area_color)
    self._selected = 0




  def move( self, dx, dy):
    """moves object with his selector (when present)"""
    self.x += dx
    self.y += dy
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move( dx, dy)




  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.set_xy( x, y)
    self.paper.move( self.item, dx, dy)
    if self.selector:
      self.paper.move( self.selector, dx, dy)
    if self.ftext:
      self.ftext.move_to( x, y)



  def get_x( self):
    return self.x



  def get_y( self):
    return self.y




  def get_xy( self):
    return self.x, self.y




  def delete( self):
    if self.focus_item:
      self.unfocus()
    if self.selector:
      self.paper.delete( self.selector)
      self.selector = None
    if self.item:
      self.paper.unregister_id( self.item)
      self.paper.delete( self.item)
    if self.ftext:
      self.ftext.delete()
    return self




  def read_package( self, package):
    pos = package.getElementsByTagName( 'point')[0]
    x, y, z = self.paper.read_xml_point( pos)
    self.set_xy( x, y)
    ft = package.getElementsByTagName('ftext')
    try:
      self.parsed_text = ft[0].cloneNode( 1)
      self.text = reduce( operator.add, [e.toxml() for e in ft[0].childNodes], '')
    except IndexError:
      self.text = "?"
      self.parsed_text = dom.parseString( "<ftext>%s</ftext>" % self.text).childNodes[0]
    fnt = package.getElementsByTagName('font')
    if fnt:
      fnt = fnt[0]
      self.font_size = int( fnt.getAttribute( 'size'))
      self.font_family = fnt.getAttribute( 'family')
      if fnt.getAttribute( 'color'):
        self.line_color = fnt.getAttribute( 'color')
    if package.getAttribute( 'background-color'):
      self.area_color = package.getAttribute( 'background-color')



  def get_package( self, doc):
    a = doc.createElement('text')
    if self.area_color != '#ffffff':
      a.setAttribute( 'background-color', self.area_color)
    if self.font_size != 12 or self.font_family != 'helvetica' or self.line_color != '#000':
      font = dom_extensions.elementUnder( a, 'font', attributes=(('size', str( self.font_size)), ('family', self.font_family)))
      if self.line_color != '#000':
        font.setAttribute( 'color', self.line_color)
    x, y = self.paper.px_to_text_with_unit( (self.x, self.y))
    dom_extensions.elementUnder( a, 'point', attributes=(('x', x),('y', y)))
    a.appendChild( self.parsed_text)
    return a



  def set_text( self, text):
    try:
      t = unicode( text)
    except UnicodeDecodeError:
      t = text.decode( 'utf-8')
    self.text = t.encode('utf-8')
    self.parsed_text = dom.parseString( '<ftext>'+self.text+'</ftext>').childNodes[0]



  def get_text( self):
    return self.text



  def bbox( self):
    return self.ftext.bbox()



  def update_font( self):
    #if 'font_family' in self.__dict__ and 'font_size' in self.__dict__:
    self.font = tkFont.Font( family=self.font_family, size=self.font_size)



  def scale_font( self, ratio):
    """scales font of text. does not redraw !!"""
    self.font_size = int( round( self.font_size * ratio))
    self.update_font()




  def lift( self):
    if self.selector:
      self.paper.lift( self.selector)
    if self.ftext:
      self.ftext.lift()
    if self.item:
      self.paper.lift( self.item)



