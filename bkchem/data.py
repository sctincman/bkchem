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

"""this module contains most of the data that are not module specific.
Serves as central storage of text and other data"""

booleans = ['no', 'yes']

# note that 'no' is there just to shift the index of single to 1
bond_types = ['no','single', 'double','triple','wedge','hatch']
alternative_bond_types = ['n','s', 'd','t','w','h']
numbered_bond_types = ['no','1', '2','3','W','H']

# support for plugable draw methods
# the remaping to new style of bond type names
bond_type_remap = ['','n1','n2','n3','w1','h1']


special_key_symbols = { 'Control_L':'C',
                        'Control_R':'C',
                        'Alt_L':'A',
                        'Alt_R':'A',
                        'Meta_L':'M',
                        'Meta_R':'M',
                        'Shift_L':'S',
                        'Shift_R':'S'}

#key symbols that have same name, but different character when pressed with Ctrl
#we need to capture them to avoid confusion in mode.register_key_sequence
strange_key_symbols = { 'slash': '/',
                        'backslash': '\\',
                        'grave': '`',
                        'question': '?'}
  

#fonts that are guaranteed by Tk to be always available
always_available_fonts = ('helvetica', 'courier', 'times')

align_modes = { 't': 'Top',
                'b': 'Bottom',
                'l': 'Left',
                'r': 'Right',
                'v': 'Vertical center',
                'h': 'Horizontal center'}


about_text = _("""BKchem was concieved and written by BK
and is performed by Python, Pmw & (optionaly :) PIL.

BKchem is free software and is distributed under GNU GPL.
BKchem is provided as is without warranty of any kind.
- see the file 'gpl.txt' in distribution directory for more info.

Among other things GNU GPL allows you to study, modify
and redistribute BKchem as long as you do it under GNU GPL.""")


no_pmw_text = _("""UNABLE TO IMPORT PMW

Sorry, but BKchem relies too heavily on Pmw to be usable without it. Please install Pmw and try again.
(for more info on Pmw see documentation)""")


splash_text = _("""BKchem is starting.

Unfortunatelly,
the splash image was not found :(""")


standards_differ_text = _('''This CDML document was created using different standard values than you are currently using. To retain the same drawing style it could be more convenient to use these new values for this file. Your global preferences will be unaffected. \n\nDo you want set these new standard values?''')



cdml_namespace = 'http://www.freesoftware.fsf.org/bkchem/cdml'

current_CDML_version = '0.11'

current_BKchem_version = '0.6.0'

vector_graphics_types = ('oval', 'rect', 'polygon')

# types that have fonts
font_types = ('atom', 'plus', 'text')

# types that have fill color
line_color_types = vector_graphics_types + ('arrow', 'bond') + font_types

# types that have outline color
area_color_types = vector_graphics_types + font_types

# types that have lines
line_types = vector_graphics_types + ('bond', 'arrow')

# saveable types - types that have their own element under <cdml> in CDML
saveable_types = ('molecule', 'arrow', 'plus', 'text', 'rect', 'oval', 'polygon')

# names of all objects that have their own element under <cdml> in CDML - for reading
loadable_types = ('molecule', 'arrow', 'plus', 'text', 'rect', 'oval', 'polygon', 'circle', 'square') 


paper_types = { 'A4': [297,210],
                'A5': [210,148],
                'B4': [353,250],
                'B5': [250,176],
                'B6': [176,125],
                'Letter': [279.4,215.9],
                'Legal': [355.7,215.9]}
