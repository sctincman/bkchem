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


"""this is just a starter of the application"""

## support for loading from outside of bkchem dir

import os_support, sys
sys.path.insert( 1, os_support.get_module_path())


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

import config

if not config.debug:
  # checking of important modules availability
  # import modules
  import import_checker
  import messages

  # we need sets from the 2.3 version
  if not import_checker.python_version_ok:
    print (messages.low_python_version_text % import_checker.python_version).encode('utf-8')
    sys.exit()

  # can't do without Pmw
  if not import_checker.Pmw_available:
    print messages.no_pmw_text.encode( 'utf-8')
    sys.exit()

  # oasa is the core now, we need it
  if not import_checker.oasa_available:
    print messages.no_oasa_text.encode( 'utf-8')
    sys.exit()

  
#import Tkinter
from main import BKchem
from splash import Splash

myapp = BKchem()
myapp.withdraw()


if __name__ == '__main__':

  # parse the command line options
  opts = ()
  files = ()
  if len( sys.argv) > 1:
    import os.path
    from getopt import gnu_getopt, GetoptError
    try:
      opts, files = gnu_getopt( sys.argv[1:], "bf:t:o:l:d:")
    except GetoptError, o:
      print _(" * unknown option -%s")
      sys.exit()


  # now initialize the main application part or the batch mode
  if opts and opts[0][0] == "-b":
    # we are in batch mode
    import time
    t = time.time()
    myapp.initialize_batch()
    myapp.process_batch( opts, files)
    print " %f ms" % (1000*(time.time()-t))
    sys.exit()
  else:
    # normal interactive mode
    if opts:
      print "the command line options are ignored in interactive mode, use -b to switch to batch mode"
    # splash screen
    splash = Splash()
    splash.withdraw()
    #splash.overrideredirect( 1)
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

    # application initialization
    myapp.initialize()
    for i in range( 0, len( files)):
      if i > 0:
        myapp.add_new_paper()
      if os.path.isfile( files[i]):
        myapp.load_CDML( file=files[i], replace=1)
      else:
        myapp.set_file_name( files[i], check_ext=1)

    ## here we try to load psyco - this could speed things up
    try:
      import psyco
      psyco.profile()
    except ImportError:
      pass

    # destroy splash
    splash.destroy()
    del splash

  # start the application
  g = myapp.pm.get_preference( 'geometry')
  if g:
    geometry = g
  else:
    geometry = "+10+10"
  myapp.geometry(geometry)
  myapp.update_idletasks()
  myapp.deiconify()
  myapp.mainloop()
  myapp.destroy()
  #import profile
  #profile.run( 'myapp.mainloop()')
  #print "BKchem finished"

# the module was imported from outside
else:
  # application initialization
  myapp.initialize()
  # start the application
  g = myapp.pm.get_preference( 'geometry')
  if g:
    geometry = g
  else:
    geometry = "+10+10"
  myapp.geometry(geometry)
  myapp.update_idletasks()
  myapp.deiconify()
  
