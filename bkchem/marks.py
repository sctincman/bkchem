#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002-2004 Beda Kosata <beda@zirael.org>

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


"""set of marks such as charges, radicals etc."""

from __future__ import division
import geometry
import xml.dom.minidom as dom
import dom_extensions
import warnings
from parents import simple_parent
from singleton_store import Screen
import data
import tkFont



class mark( simple_parent):
  # note that all children of simple_parent have default meta infos set
  # therefor it is not necessary to provide them for all new classes if they
  # don't differ (are not non-empty)

  object_type = 'mark'
  standard_size = 4
  # undo related metas
  meta__undo_simple = ('x', 'y', 'auto','size')
  meta__save_attrs = {}

  def __init__( self, atom, x, y, size=4, auto=1):
    """size is a diameter of the mark"""
    self.x = x
    self.y = y
    self.atom = atom
    self.size = size
    self.items = []
    self.auto = auto
    #self.draw()

  def _get_paper( self):
    return self.atom.paper

  paper = property( _get_paper, None, None, "the paper the mark is drawn onto")
  


  def draw( self):
    pass

  def delete( self):
    if self.paper.is_registered_object( self):
      self.unregister()
    [self.paper.delete( o) for o in self.items]
    self.items = []

  def move( self, dx, dy):
    self.x += dx
    self.y += dy
    [self.paper.move( o, dx, dy) for o in self.items]

  def move_to( self, x, y):
    dx = x - self.x
    dy = y - self.y
    self.move( dx, dy)

  def lift( self):
    [self.paper.lift( i) for i in self.items]

  def redraw( self):
    registered = self.paper.is_registered_object( self)
    if registered:
      self.unregister()
    self.delete()
    self.draw()
    if registered:
      self.register()
      

  def get_svg_element( self, doc):
    pass

  def transform( self, tr):
    # do only move, the direction-using marks would need to override it and make real transform
    x, y = tr.transform_xy( self.x, self.y)
    self.move_to( x, y)

  def focus( self):
    self.set_color( "red")

  def unfocus( self):
    self.set_color( self.atom.line_color)


  def set_color( self, color):
    [self.paper.itemconfig( i, outline=color, fill=color) for i in self.items if self.paper.type( i) in ("oval",)]
    [self.paper.itemconfig( i, fill=color) for i in self.items if self.paper.type( i) in ("line","text")]
    

  def register( self):
    [self.paper.register_id( i, self) for i in self.items]

  def unregister( self):
    [self.paper.unregister_id( i) for i in self.items]



  def get_package( self, doc):
    a = doc.createElement('mark')
    x ,y = map( Screen.px_to_text_with_unit, (self.x, self.y))
    dom_extensions.setAttributes( a, (('type', self.__class__.__name__),
                                      ('x', x),
                                      ('y', y),
                                      ('auto', str( int( self.auto))),
                                      ('size', str( self.size))))
    for (attr, typ) in self.meta__save_attrs.iteritems():
      val = getattr( self, attr)
      if typ == bool:
        value = data.booleans[ int( val)]
      else:
        value = str( val)
      a.setAttribute( attr, value)
    return a



  def read_package( self, package, atom):
    typ = package.getAttribute( 'type')
    cls = globals().get( typ, None)
    if cls:
      auto = (package.getAttribute( 'auto') != None and package.getAttribute( 'auto')) or 0
      x, y, z = Screen.read_xml_point( package)
      size = package.getAttribute( 'size') and int( package.getAttribute( 'size')) or None
      if size:
        m = cls( atom, x, y, size=size, auto=int(auto))
      else:
        m = cls( atom, x, y, auto=int(auto))

      # class specific attributes
      for (attr, typ) in m.meta__save_attrs.iteritems():
        val = package.getAttribute( attr)
        if val != '':
          if typ == bool:
            value = bool( data.booleans.index( val))
          elif typ == int:
            value = int( val)
          else:
            value = val
          setattr( m, attr, value)

      return m
    else:
      raise ValueError, "no such mark type %s" % typ

  read_package = classmethod( read_package)






class radical( mark):

  def draw( self):
    """outline color is used for both outline and fill for radical"""
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s,
                                          fill=self.atom.line_color, outline=self.atom.line_color,
                                          tags='mark')]



  def get_svg_element( self, doc):
    e = doc.createElement( 'ellipse')
    dom_extensions.setAttributes( e,
                                 (( 'cx', str( self.x)),
                                  ( 'cy', str( self.y)),
                                  ( 'rx', str( self.size /2)),
                                  ( 'ry', str( self.size /2)),
                                  ( 'fill', self.atom.line_color),
                                  ( 'stroke', self.atom.line_color),
                                  ( 'stroke-width', '1')))
    return e







class biradical( mark):

  def move( self, dx, dy):
    """marks that have a direction and not only position should be redrawn on move"""
    self.x += dx
    self.y += dy
    self.redraw()

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    s = round( self.size / 2)
    x1, y1, x2, y2 = self.x, self.y, self.atom.x, self.atom.y
    x, y = geometry.find_parallel( x1, y1, x2, y2, s*1.5)[0:2]
    # one circle
    self.items = [self.paper.create_oval( x-s, y-s, x+s, y+s,
                                          fill=self.atom.line_color, outline=self.atom.line_color,
                                          tags='mark')]
    # and the second on the other side
    x, y = geometry.find_parallel( x1, y1, x2, y2, -s*1.5)[0:2]
    self.items.append( self.paper.create_oval( x-s, y-s, x+s, y+s,
                                               fill=self.atom.line_color, outline=self.atom.line_color,
                                               tags='mark'))
    

  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    for i in self.items:
      x1, y1, x2, y2 = self.paper.coords( i)
      x = (x1 + x2)/2
      y = (y1 + y2)/2
      dom_extensions.elementUnder( e, 'ellipse',
                                   (( 'cx', str( x)),
                                    ( 'cy', str( y)),
                                    ( 'rx', str( self.size /2)),
                                    ( 'ry', str( self.size /2)),
                                    ( 'fill', self.atom.line_color),
                                    ( 'stroke', self.atom.line_color),
                                    ( 'stroke-width', '1')))
    return e


  def transform( self, tr):
    self.x, self.y = tr.transform_xy( self.x, self.y)
    for i in self.items:
      coords = self.paper.coords( i)
      if self.paper.type( i) == 'oval':
        x, y = (coords[0]+coords[2])/2.0, (coords[1]+coords[3])/2.0
        d = abs(coords[2]-coords[0])/2.0
        x, y = tr.transform_xy( x, y)
        tr_coords = [x-d, y-d, x+d, y+d]
      else:
        tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))






class electronpair( mark):

  def __init__( self, atom, x, y, size=10, auto=1):
    mark.__init__( self, atom, x, y, size=size, auto=auto)

  def move( self, dx, dy):
    """marks that have a direction and not only position should be redrawn on move"""
    self.x += dx
    self.y += dy
    self.redraw()

  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    s = round( self.size / 2)
    x1, y1, x2, y2 = self.x, self.y, self.atom.x, self.atom.y
    # one end
    x, y = geometry.find_parallel( x1, y1, x2, y2, s)[0:2]
    # and the other
    x0, y0 = geometry.find_parallel( x1, y1, x2, y2, -s)[0:2]
    self.items = [self.paper.create_line( x, y, x0, y0, fill=self.atom.line_color,
                                          width=round(s/2), tags='mark')]
    

  def get_svg_element( self, doc):
    e = doc.createElement( 'line')
    x1, y1, x2, y2 = self.paper.coords( self.items[0])
    dom_extensions.setAttributes( e,
                                 (( 'x1', str( x1)),
                                  ( 'y1', str( y1)),
                                  ( 'x2', str( x2)),
                                  ( 'y2', str( y2)),
                                  ( 'stroke-width', str( round( round( self.size /2)/2))),
                                  ( 'fill', self.atom.line_color),
                                  ( 'stroke', self.atom.line_color)))
    return e

  def transform( self, tr):
    self.x, self.y = tr.transform_xy( self.x, self.y)
    for i in self.items:
      coords = self.paper.coords( i)
      tr_coords = tr.transform_xy_flat_list( coords)
      self.paper.coords( i, tuple( tr_coords))






class plus( mark):

  standard_size = 10
  meta__undo_simple = mark.meta__undo_simple + \
                      ('draw_circle',)
  meta__save_attrs = {"draw_circle": bool}


  def __init__( self, atom, x, y, size=10, auto=1):
    mark.__init__( self, atom, x, y, size=size, auto=auto)
    self.draw_circle = True


  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)

    self.items = [self.paper.create_line( x-s+2, y, x+s-2, y,
                                          fill=self.atom.line_color, tags='mark')]
    self.items.append( self.paper.create_line( x, y-s+2, x, y+s-2,
                                               fill=self.atom.line_color, tags='mark'))
    if self.draw_circle:
      self.items.append( self.paper.create_oval( x-s, y-s, x+s, y+s, fill='',
                                                 outline=self.atom.line_color, tags='mark'))


  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    x, y = self.x, self.y
    s = round( self.size / 2)
    if self.draw_circle:
      dom_extensions.elementUnder( e, 'ellipse',
                                   (( 'cx', str( x)),
                                    ( 'cy', str( y)),
                                    ( 'rx', str( s)),
                                    ( 'ry', str( s)),
                                    ( 'fill', 'none'),
                                    ( 'stroke', self.atom.line_color),
                                    ( 'stroke-width', '1')))
    for x1, y1, x2, y2 in [(x-s+2, y, x+s-2, y), (x, y-s+2, x, y+s-2)]:
      dom_extensions.elementUnder( e, 'line',
                                    (( 'x1', str( x1)),
                                     ( 'y1', str( y1)),
                                     ( 'x2', str( x2)),
                                     ( 'y2', str( y2)),
                                     ( 'stroke-width', '1'),
                                     ( 'fill', self.atom.line_color),
                                     ( 'stroke', self.atom.line_color)))

    return e


  def set_color( self, color):
    [self.paper.itemconfig( i, outline=color) for i in self.items if self.paper.type( i) in ("oval",)]
    [self.paper.itemconfig( i, fill=color) for i in self.items if self.paper.type( i) in ("line",)]





class minus( mark):

  standard_size = 10
  meta__undo_simple = mark.meta__undo_simple + \
                      ('draw_circle',)
  meta__save_attrs = {"draw_circle": bool}
  

  def __init__( self, atom, x, y, size=10, auto=1):
    mark.__init__( self, atom, x, y, size=size, auto=auto)
    self.draw_circle = True


  def draw( self):
    if self.items:
      warnings.warn( "draw called on already drawn mark!", UserWarning, 2)
      self.delete()
    x, y = self.x, self.y
    s = round( self.size / 2)
    self.items = [self.paper.create_line( x-s+2, y, x+s-2, y,
                                          fill=self.atom.line_color, tags='mark')]
    if self.draw_circle:
      self.items.append( self.paper.create_oval( x-s, y-s, x+s, y+s, fill='',
                                                 outline=self.atom.line_color, tags='mark'))


  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    x, y = self.x, self.y
    s = round( self.size / 2)
    if self.draw_circle:
      dom_extensions.elementUnder( e, 'ellipse',
                                   (( 'cx', str( x)),
                                    ( 'cy', str( y)),
                                    ( 'rx', str( s)),
                                    ( 'ry', str( s)),
                                    ( 'fill', 'none'),
                                    ( 'stroke', self.atom.line_color),
                                    ( 'stroke-width', '1')))
    for x1, y1, x2, y2 in [(x-s+2, y, x+s-2, y)]:
      dom_extensions.elementUnder( e, 'line',
                                    (( 'x1', str( x1)),
                                     ( 'y1', str( y1)),
                                     ( 'x2', str( x2)),
                                     ( 'y2', str( y2)),
                                     ( 'stroke-width', '1'),
                                     ( 'fill', self.atom.line_color),
                                     ( 'stroke', self.atom.line_color)))

    return e


  def set_color( self, color):
    [self.paper.itemconfig( i, outline=color) for i in self.items if self.paper.type( i) in ("oval",)]
    [self.paper.itemconfig( i, fill=color) for i in self.items if self.paper.type( i) in ("line",)]





class text_mark( mark):

  meta__undo_simple = mark.meta__undo_simple + ('text',)
  meta__save_attrs = {"text": str}
    

  def __init__( self, atom, x, y, text="", size=8, auto=1):
    mark.__init__( self, atom, x, y, size=size, auto=auto)
    self.text = text

  # the text property
  def _set_text( self, text):
    self._text = str( text)

  def _get_text( self):
    return self._text

  text = property( _get_text, _set_text, None, "the text of the mark")
    

  def draw( self):
    
    self.items = [self.paper.create_text( self.x,
                                          self.y,
                                          text=self.text,
                                          fill=self.atom.line_color,
                                          font=(self.atom.font_family, self.size, "normal"),
                                          tags="mark")]


  def get_svg_element( self, doc):
    e = doc.createElement( 'g')
    x, y = self.x, self.y
    font = tkFont.Font( family=self.atom.font_family, size=self.size)
    dx = font.measure( self.text) / 2
    y += font.metrics('descent')

    text = dom_extensions.textOnlyElementUnder( e, 'text', self.text,
                                                (('font-size', "%dpt" % self.size),
                                                 ('font-family', self.atom.font_family),
                                                 ( "x", str( x - dx)),
                                                 ( "y", str( y)),
                                                 ( 'fill', self.atom.line_color)))
    return e





class referencing_text_mark( text_mark, mark):
  """similar to text mark but the text is taken from the referenced atom"""

  meta__undo_simple = mark.meta__undo_simple
  meta__save_attrs = {"refname": str}
  

  def __init__( self, atom, x, y, refname, size=8, auto=1):
    mark.__init__( self, atom, x, y, size=size, auto=auto)
    self.refname = refname

  # the text property
  def _get_text( self):
    if hasattr( self.atom, self.refname):
      return getattr( self.atom, self.refname)

  text = property( _get_text, None, None, "the text of the mark")


  def draw( self):
    text_mark.draw( self)




class atom_number( referencing_text_mark):

  def __init__( self, atom, x, y, size=8, auto=1):
    referencing_text_mark.__init__( self, atom, x, y, "number", size=size, auto=auto)
  
