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

"""images for buttons all over bkchem"""

import import_checker
import os_support

__all__ = ['images', 'splash_image']

paths = { 'draw': 'draw.gif',
          'edit': 'edit.gif',
          'text': 'text.gif',
          'rotate': 'rotate.gif',
          'plus': 'plus.gif',
          'template': 'template.gif',
          'arrow': 'arrow.gif',
          'vector': 'oval.gif',
          'bondalign': 'bondalign.gif',
          '1': '1.gif',
          '6': '6.gif',
          '18': '18.gif',
          '30': '30.gif',
          'benzene': 'benzene.gif',
          'cyklopentadiene': 'cyklopentadiene.gif',
          'cyklopentane': 'cyklopentane.gif',
          'cyklohexane': 'cyklohexane.gif',
          'cyklopropane': 'cyklopropane.gif',
          'cyklobutane': 'cyklobutane.gif',
          'cyclooctane': 'cyclooctane.gif',
          'cycloheptane': 'cycloheptane.gif',
          'thiophene': 'thiophene.gif',
          'furane': 'furane.gif',
          'pyrrole': 'pyrrole.gif',
          'purine': 'purine.gif',
          'chair':'chair.gif',
          'normal': 'normal.gif',
          'wedge': 'forth.gif',
          'hatch': 'back.gif',
          'oval': 'oval.gif',
          'circle': 'circle.gif',
          'rectangle': 'rect.gif',
          'square': 'square.gif',
          'polygon': 'polygon.gif',
          'fixed': 'fixed_length.gif',
          'freestyle': 'freestyle.gif',
          'minusincircle': 'minus_in_circle.gif',
          'plusincircle': 'plus_in_circle.gif',
          'radical': 'radical.gif',
          'biradical': 'biradical.gif',
          'electronpair': 'electron_pair.gif',
          'mark': 'biradical.gif',
          'bold': 'bold.gif',
          'italic': 'italic.gif',
          'subscript': 'subscript.gif',
          'superscript': 'superscript.gif',
          'subnum': 'subnum.gif',
          'anormal': 'anormal.gif',
          'spline': 'spline.gif',
          'tovert': 'tovert.gif',
          'tohoriz': 'tohoriz.gif',
          'single': 'single.gif',
          'double': 'double.gif',
          'triple': 'triple.gif'}

splash_image_path = 'logo.ppm'



import Tkinter

#images for buttons
images = {}
for name in paths:
  try:
    # try if the picture can be read by Tkinter
    images[name] = Tkinter.PhotoImage( file = os_support.get_path( paths[name], 'pixmap'))
  except:
    pass

# splash image
try:
  splash_image = Tkinter.PhotoImage( file = os_support.get_path( splash_image_path, 'image'))
except:
  splash_image = None

