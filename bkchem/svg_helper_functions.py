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

"""few functions focused on SVG"""

import xml.dom.minidom as dom
import dom_extensions

def ftext_to_svg_dom( ftext):
  fd = dom.parseString( '<ftext>%s</ftext>' % ftext).childNodes[0]
  svg = dom.Document()
  return ftext_dom_to_svg_dom( fd, svg)

def ftext_dom_to_svg_dom( ftext, doc):
  if not ftext.nodeValue:
    name = ftext.nodeName
    my_svg = None
    if name == 'b':
      my_svg = doc.createElement( 'tspan')
      dom_extensions.setAttributes( my_svg, (('font-weight', 'bold'),))
    elif name == 'i':
      my_svg = doc.createElement( 'tspan')
      dom_extensions.setAttributes( my_svg, (('font-style', 'italic'),))
    elif name == 'sup':
      my_svg = doc.createElement( 'tspan')
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'super'),('font-size','75%')))
    elif name == 'sub':
      my_svg = doc.createElement( 'tspan')
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'sub'),('font-size','75%')))
    elif name == 'ftext':
      my_svg = doc.createElement( 'text')
    if my_svg:
      for el in ftext.childNodes:
        my_svg.appendChild( ftext_dom_to_svg_dom( el, doc))
      return my_svg
  else:
    return doc.createTextNode( ftext.nodeValue)
