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


"""provides exporters to XML formats (SVG for now)"""

import xml.dom.minidom as dom
from xml.dom.minidom import Document
import re
import data
import dom_extensions
import operator
import svg_helper_functions as svg_help
import dom_extensions
import os


class XML_writer:
  """This is abstract class that serves as parent for specialized writters - CDML, SVG ...
  construct_dom_tree method is virtual and should be overriden"""
  def __init__( self, paper):
    self.paper = paper
    self.document = Document()
    self.top = None # top level element
    #self.construct_dom_tree()

  def construct_dom_tree( self, top_levels):
    pass

  def write_xml_to_file( self, file):
    "writes XML representation of entire 'paper' to 'file'"
    pass

  def get_nicely_formated_document( self):
    """returns text form of self.document indented with dom_extensions.safe_indent"""
    dom_extensions.safe_indent( self.top)
    return self.document.toxml()

# Tkinter states that it takes font sizes in pt. However this is not true (as for python 2.2.2)
# therefor there is this variable to quickly change the settings and control the SVG output
pt_or_px="pt"


class SVG_writer( XML_writer):

  def __init__( self, paper):
    XML_writer.__init__( self, paper)
    self.full_size = not (paper.get_paper_property( 'crop_svg') and len( paper.stack))

  def construct_dom_tree( self, top_levels):
    """constructs the SVG dom from all top_levels"""
    self._id = 0
    doc = self.document
    self.top = dom_extensions.elementUnder( doc, "svg", attributes=(("xmlns", "http://www.w3.org/2000/svg"),
                                                                    ("version", "1.0")))
    if self.full_size:
      sx = self.paper.get_paper_property( 'size_x')
      sy = self.paper.get_paper_property( 'size_y')
      dom_extensions.setAttributes( self.top, (("width", '%fmm' % sx),
                                               ("height", '%fmm' % sy),
                                               ('viewBox', '0 0 %d %d' % (self.paper.mm_to_px(sx), self.paper.mm_to_px(sy)))))
    else:
      items = list( self.paper.find_all())
      items.remove( self.paper.background)
      x1, y1, x2, y2 = self.paper.list_bbox( items)
      dom_extensions.setAttributes( self.top, (("width", str(x2-x1+20)),
                                               ("height", str(y2-y1+20)))) #,
                                               #("viewBox",'%d %d %d %d' % ( x1, y1, x2-x1+10, y2-y1+10))))
    self.group = dom_extensions.elementUnder( self.top, 'g',
                                              (('style', 'stroke:#000'),
                                               ('font-size', '12pt'),
                                               ('font-family', 'Helvetica'),
                                               ('stroke-width', '1pt'),
                                               ('stroke-linecap', 'round')))
    if not self.full_size:
      self.group.setAttribute( 'transform', 'translate('+str(-x1+10)+', '+str(-y1+10)+')')
      
    # sort the top_levels according to paper.stack
    cs = []
    for c in self.paper.stack:
      if c in top_levels:
        cs.append( c)
    for o in cs:
      if o.object_type == 'molecule':
        for b in o.bonds:
          self.add_bond( b)
        for a in o.atoms:
          self.add_atom( a)
      elif o.object_type == 'arrow':
        self.add_arrow( o)
      elif o.object_type == 'text':
        self.add_text( o)
      elif o.object_type == 'plus':
        self.add_plus( o)
      elif o.object_type in data.vector_graphics_types:
        if o.object_type == 'rect':
          self.add_rect( o)
        elif o.object_type == 'oval':
          self.add_oval( o)
        elif o.object_type == 'polygon':
          self.add_polygon( o)
          

    
  def add_bond( self, b):
    """adds bond item to SVG document"""
    if b.line_width != 1.0 or b.line_color != '#000' or b.type == 'b':
      line_width = (b.type == 'b') and b.wedge_width or b.type != 'w' and b.line_width or 1.0
      l_group = dom_extensions.elementUnder( self.group, 'g',
                                             (( 'stroke-width', str( line_width)),
                                              ( 'stroke', b.line_color)))
    else:
      l_group = self.group #dom_extensions.elementUnder( self.group, 'g')
    # items to be exported
    if b.type == 'd':
      # d is a little bit twisted
      if b.simple_double and not b.center and not b.order == 1:
        line_items = [b.item]
        items = b.second + b.third
      else:
        line_items = []
        items = b.items + b.second + b.third
    else:
      if b.type == 'h':
        items = b.items
      else:
        if b.center:
          if not b.order == 2:
            print b.order, b.center, b.type
          items = []
        else:
          items = [b.item]
      # simple doubles?
      if b.type == 'n' or (not b.simple_double and not b.center):
        items += b.second
        items += b.third
        line_items = []
      else:
        line_items = b.second + b.third
    # the conversion function for coordinates
    convert = str
    # export itself
    if b.type in 'nbhd':
      for i in items:
        x1, y1, x2, y2 = self.paper.coords( i)
        line = dom_extensions.elementUnder( l_group, 'line',
                                            (( 'x1', convert( x1)),
                                             ( 'y1', convert( y1)),
                                             ( 'x2', convert( x2)),
                                             ( 'y2', convert( y2))))
    elif b.type == 'w':
      for i in items:
        coords = self.paper.coords( b.item)
        line = dom_extensions.elementUnder( l_group, 'polygon',
                                            (( 'fill', b.line_color),
                                             ( 'stroke', b.line_color),
                                             ( 'points', list_to_svg_points( coords))))
    elif b.type in 'h':
      for i in items:
        for p in i:
          x1, y1, x2, y2 = self.paper.coords( p)
          line = dom_extensions.elementUnder( l_group, 'line',
                                              (( 'x1', convert( x1)),
                                               ( 'y1', convert( y1)),
                                               ( 'x2', convert( x2)),
                                               ( 'y2', convert( y2))))
    elif b.type == 'a':
      for i in items:
        coords = self.paper.coords( i)
        points = ' '.join( map( str, coords))
        line = dom_extensions.elementUnder( l_group, 'polyline',
                                            (( 'points', points),
                                             ( 'fill', 'none')))
    # the line items for simple_double
    for i in line_items:
      x1, y1, x2, y2 = self.paper.coords( i)
      line = dom_extensions.elementUnder( l_group, 'line',
                                          (( 'x1', convert( x1)),
                                           ( 'y1', convert( y1)),
                                           ( 'x2', convert( x2)),
                                           ( 'y2', convert( y2)),
                                           ( 'stroke-width', str( b.line_width))))

            
  def add_arrow( self, a):
    """adds arrow item to SVG document"""
    i = self._id
    if a.pin == 1 or a.pin == 3:
      d1, d2, d3 = a.shape
      defs = dom_extensions.elementUnder( self.group, 'defs')
      arrow = dom_extensions.elementUnder( defs, 'marker', (('id','Arrow'+str(i)),('refX',str(d2)),('refY',str(d3)),
                                                            ('markerUnits','userSpaceOnUse'),
                                                            ('markerWidth',str(d2)),('markerHeight',str(2*d3)),
                                                            ('orient','auto'),
                                                            ('stroke', a.line_color),
                                                            ('fill', a.line_color)))
      dom_extensions.elementUnder( arrow, 'path', (('d', 'M %d %d L 0 0 L %d %d L 0 %d z'%(d2, d3, d2-d1, d3, 2*d3)),))
    if a.pin == 2 or a.pin == 3:
      d1, d2, d3 = a.shape
      defs = dom_extensions.elementUnder( self.group, 'defs')
      arrow = dom_extensions.elementUnder( defs, 'marker', (('id','ArrowBack'+str(i)),('refX','0'),('refY',str(d3)),
                                                            ('markerUnits','userSpaceOnUse'),
                                                            ('markerWidth',str(d2)),('markerHeight',str(2*d3)),
                                                            ('orient','auto'),
                                                            ('stroke', a.line_color),
                                                            ('fill', a.line_color)))
      dom_extensions.elementUnder( arrow, 'path', (('d', 'M 0 %d L %d 0 L %d %d L %d %d z'%(d3, d2, d1, d3, d2, 2*d3)),))

    if a.spline and len( a.points) > 2:
      x,y = a.points[0].get_xy()
      ps = 'M%d,%d ' % (x,y)
      odd = 1
      for (x,y) in [p.get_xy() for p in a.points[1:]]:
        if odd:
          ps += 'Q%d,%d ' % (x,y)
        else:
          ps += '%d,%d ' % (x,y)
        odd = not odd

##       x,y = a.points[0].get_xy()
##       x1,y1 = a.points[1].get_xy()
##       x2,y2 = a.points[2].get_xy()
##       ps = 'M%d,%d Q%d,%d %d,%d' % (x,y,x1,y1,x2,y2)
##       for (x,y) in [p.get_xy() for p in a.points[3:]]:
##         ps += ' T%d,%d ' % (x,y)

      line = dom_extensions.elementUnder( self.group, 'path',
                                          (( 'd', ps),
                                           ( 'stroke-width', str( a.line_width)),
                                           ( 'fill', 'none'),
                                           ( 'stroke', a.line_color)))
    else:
      ps = ''
      for (x,y) in [p.get_xy() for p in a.points]:
        ps += '%d,%d ' % (x,y)
      line = dom_extensions.elementUnder( self.group, 'polyline',
                                          (( 'points', ps),
                                           ( 'stroke-width', str( a.line_width)),
                                           ( 'fill', 'none'),
                                           ( 'stroke', a.line_color)))
    if a.pin == 1 or a.pin == 3:
      line.setAttribute( 'marker-end','url(#Arrow'+str(i)+')')
    if a.pin == 2 or a.pin == 3:
      line.setAttribute( 'marker-start','url(#ArrowBack'+str(i)+')')
    self._id += 1

  def add_text( self, t):
    """adds text item to SVG document"""
    item = t.item
    x1, y1 = t.get_xy()
    x, y, x2, y2 = self.paper.bbox( item)
    dom_extensions.elementUnder( self.group, 'rect',
                                 (( 'x', str( x)),
                                  ( 'y', str( y)),
                                  ( 'width', str( x2-x)),
                                  ( 'height', str( y2-y)),
                                  ( 'fill', t.area_color),
                                  ( 'stroke', t.area_color)))
    y1 += (y2-y)/4.0
    text = svg_help.ftext_dom_to_svg_dom( t.get_parsed_text(), self.document)
    dom_extensions.setAttributes( text, (( "x", str( x)),
                                         ( "y", str( y1)),
                                         ( "font-family", t.font_family),
                                         ( "font-size", '%d%s' % (t.font_size, pt_or_px)),
                                         ( 'stroke', t.line_color),
                                         ( 'fill', t.line_color)))
    self.group.appendChild( text)

  def add_plus( self, p):
    """adds plus item to SVG document"""
    item = p.item
    x1, y1 = p.get_xy()
    x, y, x2, y2 = self.paper.bbox( item)
    dom_extensions.elementUnder( self.group, 'rect',
                                 (( 'x', str( x)),
                                  ( 'y', str( y)),
                                  ( 'width', str( x2-x)),
                                  ( 'height', str( y2-y)),
                                  ( 'fill', p.area_color),
                                  ( 'stroke', p.area_color)))
    y1 += (y2-y)/4.0
    text = dom_extensions.textOnlyElementUnder( self.group, 'text', '+',
                                                (('font-size', "%d%s" % (p.font_size, pt_or_px)),
                                                 ('font-family', p.font_family),
                                                 ( "x", str( x)),
                                                 ( "y", str( round( y1))),
                                                 ( 'stroke', p.line_color),
                                                 ( 'fill', p.line_color)))

  def add_atom( self, a):
    """adds atom item to SVG document"""
    if a.show:
      item = a.selector
      x1, y1 = a.get_xy()
      x, y, x2, y2 = self.paper.bbox( item)
      if os.name == 'nt':
        x += 2  #nasty hack to improve results on win machines (they have larger fonts?!?)
        x2 -= 2 
      dom_extensions.elementUnder( self.group, 'rect',
                                   (( 'x', str( x)),
                                    ( 'y', str( y)),
                                    ( 'width', str( x2-x)),
                                    ( 'height', str( y2-y)),
                                    ( 'fill', a.area_color),
                                    ( 'stroke', a.area_color)))
      y1 += (y2-y)/4.0
      text = svg_help.ftext_to_svg_dom( a.get_ftext())
      dom_extensions.setAttributes( text, (( "x", str( x)),
                                           ( "y", str( y1)),
                                           ( "font-family", a.font_family),
                                           ( "font-size", '%d%s' % (a.font_size, pt_or_px)),
                                           ( 'stroke', a.line_color),
                                           ( 'fill', a.line_color),
                                           ( 'textLength', "%dpx" % (x2-x-2))))  # -2 is a nasty hack
      self.group.appendChild( text)
    for m in a.marks.itervalues():
      if m:
        self.group.appendChild( m.get_svg_element( self.document))

  def add_rect( self, o):
    x1, y1, x2, y2 = o.coords
    dom_extensions.elementUnder( self.group, 'rect',
                                 (( 'x', str( x1)),
                                  ( 'y', str( y1)),
                                  ( 'width', str( x2-x1)),
                                  ( 'height', str( y2-y1)),
                                  ( 'fill', o.area_color),
                                  ( 'stroke', o.line_color),
                                  ( 'stroke-width', str( o.line_width))))
    
  def add_oval( self, o):
    x1, y1, x2, y2 = o.coords
    dom_extensions.elementUnder( self.group, 'ellipse',
                                 (( 'cx', str( (x2+x1)/2)),
                                  ( 'cy', str( (y2+y1)/2)),
                                  ( 'rx', str( (x2-x1)/2)),
                                  ( 'ry', str( (y2-y1)/2)),
                                  ( 'fill', o.area_color),
                                  ( 'stroke', o.line_color),
                                  ( 'stroke-width', str( o.line_width))))


  def add_polygon( self, o):
    ps = ''
    for (x,y) in [p.get_xy() for p in o.points]:
      ps += '%d,%d ' % (x,y)
    poly = dom_extensions.elementUnder( self.group, 'polygon',
                                        (( 'points', ps),
                                         ( 'stroke-width', str( o.line_width)),
                                         ( 'fill', o.area_color),
                                         ( 'stroke', o.line_color),
                                         ( 'fill-rule', 'evenodd')))



def list_to_svg_points( l):
  for a in l:
    return ' '.join( map( str, l))



  
