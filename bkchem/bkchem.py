#! /usr/bin/python
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

"""this is just a starter of the application"""

## support for loading from outside of bkchem dir

import os_support, sys
sys.path.append( os_support.get_module_path)

### now starting for real

## first turn locale support on

import gettext

## for some strange reason python gettext raises error when no translation is found
## (fixed in Python 2.2.1 but we must be backward compatible with 2.2)
## this makes it to use the original strings when translation is not available
if gettext.find( 'BKchem'):
  # at first try if locale is in its standard location
  try:
    gettext.install( 'BKchem', unicode=1)
  except IOError:
    import __builtin__
    __builtin__.__dict__['_'] = lambda m: m
else:
  # it is not. then we are in the single directory deployment probably
  try:
    gettext.install( 'BKchem', '../locale', unicode=1)
  except IOError:
    import __builtin__
    __builtin__.__dict__['_'] = lambda m: m
      
# import modules
import import_checker
# can't do without Pmw
if not import_checker.Pmw_available:
  import data
  print data.no_pmw_text.encode( 'utf-8')
  import sys
  sys.exit()
  
#import Tkinter
from main import BKchem
from splash import Splash

myapp = BKchem()
myapp.withdraw()

#splash screen
splash = Splash()
splash.withdraw()
splash.update_idletasks()
width = splash.winfo_reqwidth()
height = splash.winfo_reqheight()
x = (myapp.winfo_screenwidth() - width) / 2 - myapp.winfo_vrootx()
y = (myapp.winfo_screenheight() - height) / 3 - myapp.winfo_vrooty()
if x < 0:
    x = 0
if y < 0:
    y = 0
geometry = '%dx%d+%d+%d' % (width, height, x, y)
splash.geometry(geometry)
splash.update_idletasks()
splash.deiconify()
myapp.update()

# now initialize the main application part
myapp.initialize()
if len( sys.argv) > 1:
  import os.path
  if os.path.isfile( sys.argv[1]):
    myapp.load_CDML( file=sys.argv[1])
  else:
    myapp.set_file_name( sys.argv[1], check_ext=1)

# destroy splash
splash.destroy()
del splash

#start the application
geometry = "+10+10"
myapp.geometry(geometry)
myapp.update_idletasks()
myapp.deiconify()
myapp.mainloop()
#import profile
#profile.run( 'myapp.mainloop()')
#print "BKchem finished"

