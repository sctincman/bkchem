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


"""few functions focused on SVG"""

import xml.dom.minidom as dom
import dom_extensions
from singleton_store import Store



def ftext_to_svg_dom( ftext):
  fd = dom.parseString( '<ftext>%s</ftext>' % ftext).childNodes[0]
  svg = dom.Document()
  return ftext_dom_to_svg_dom( fd, svg)


def ftext_dom_to_svg_dom( ftext, doc, add_to=None):
  if not add_to:
    element = doc.createElement( 'text')
  else:
    element = add_to

  if not ftext.nodeValue:
    name = ftext.nodeName
    # check if to add attributes to already existing element or create a new one
    if (not element.lastChild and element.nodeName == "tspan") or name == "ftext":
      my_svg = element
    else:
      my_svg = doc.createElement( 'tspan')
      element.appendChild( my_svg)

    # now put the attributes inside
    if name == 'b':
      dom_extensions.setAttributes( my_svg, (('font-weight', 'bold'),))
    elif name == 'i':
      dom_extensions.setAttributes( my_svg, (('font-style', 'italic'),))
    elif name == 'sup':
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'super'),('font-size','75%')))
    elif name == 'sub':
      dom_extensions.setAttributes( my_svg, (('baseline-shift', 'sub'),('font-size','75%')))

    # continue with the children
    for el in ftext.childNodes:
      ftext_dom_to_svg_dom( el, doc, add_to=my_svg)
  else:
    if Store.pm.get_preference( "replace_minus"):
      element.appendChild( doc.createTextNode( ftext.nodeValue.replace( "-", unichr( 8722))))
    else:
      element.appendChild( doc.createTextNode( ftext.nodeValue))

  return element

