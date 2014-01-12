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

"""Starter of the application.

"""

from __future__ import print_function

## support for loading from outside of bkchem dir
import sys

import os_support

sys.path.insert(1, os_support.get_module_path())

### now starting for real
import pref_manager

from singleton_store import Store

# at first preference manager
Store.pm = pref_manager.pref_manager(
  [os_support.get_config_filename( "prefs.xml", level="global", mode='r'),
   os_support.get_config_filename( "prefs.xml", level="personal", mode='r')])


## first turn locale support on

import gettext
import os.path

user_lang = Store.pm.get_preference( "lang")
if user_lang:
  langs = [[user_lang], None]
else:
  langs = [None]

if user_lang == "en":
  if sys.version_info[2] > 2:
    import builtins
  else:
    import __builtin__ as builtins
  builtins.__dict__['_'] = lambda m: m
  builtins.__dict__['ngettext'] = gettext.ngettext
  Store.lang = "en"
else:
  Store.lang = None
  for lang in langs:
    for localedir in (os.path.normpath(os.path.join(
                        os_support.get_bkchem_run_dir(),
                        '../../../../share/locale')),
                      os.path.normpath(os.path.join(
                        os_support.get_bkchem_run_dir(), '../locale')),
                      None):
      if gettext.find( 'BKChem', localedir=localedir, languages=lang):
        # find what language was loaded
        rest = gettext.find( 'BKChem', localedir=localedir, languages=lang)
        for i in range( 3):
          rest, Store.lang = os.path.split( rest)

        tr = gettext.translation( 'BKChem', localedir=localedir, languages=lang)
        try:
          tr.install(unicode=True, names=['ngettext'])
        except TypeError:
          # In newer Python unicode keyword is dropped
          tr.install(names=['ngettext'])
        break
    if Store.lang:
      break

  if not Store.lang:
    if sys.version_info[0] > 2:
      import builtins
    else:
      import __builtin__ as builtins
    builtins.__dict__['_'] = lambda m: m
    builtins.__dict__['ngettext'] = gettext.ngettext
    Store.lang = "en"



import config

if not config.debug:
  # checking of important modules availability
  # import modules
  import import_checker
  import messages

  # At least version 2.6 is required for the new exception syntax,
  # 'with' statement, built in next() and other future compatibility goodies
  if not import_checker.python_version_ok:
    print((messages.low_python_version_text % import_checker.python_version).encode('utf-8'))
    sys.exit()

  # can't do without Pmw
  if not import_checker.Pmw_available:
    print(messages.no_pmw_text.encode('utf-8'))
    sys.exit()

  # oasa is the core now, we need it
  if not import_checker.oasa_available:
    print(messages.no_oasa_text.encode('utf-8'))
    sys.exit()


#import Tkinter
from main import BKChem
from splash import Splash
from singleton_store import Store

myapp = BKChem()
myapp.withdraw()

if __name__ == '__main__':

  import messages
  enc = sys.getfilesystemencoding()
  if not enc:
    enc = sys.getdefaultencoding()
  opts = [i.decode(enc) for i in sys.argv[1:]
                          if ((sys.version_info[0] > 2 and isinstance(i, bytes)) or
                              (sys.version_info[0] < 3 and isinstance(i, str)))]
  opts.extend(i for i in sys.argv[1:]
                  if ((sys.version_info[0] > 2 and isinstance(i, str)) or
                      (sys.version_info[0] < 3 and isinstance(i, unicode))))

  if "-v" in opts or "--version" in opts:
    print("BKChem", config.current_BKChem_version)
    sys.exit()
  if "-h" in opts or "--help" in opts:
    print(messages.usage_text)
    sys.exit()
  if "-H" in opts:
    i = opts.index("-H")
    del opts[i]
    if len( opts) > i:
      os_support.set_bkchem_private_dir( opts[i])
      del opts[i]
  if "-b" in opts:
    i = opts.index("-b")
    if len( opts) >= i:

      # we are in batch mode
      #import time
      #t = time.time()
      myapp.initialize_batch()
      myapp.process_batch( opts)
      #print(" %f ms" % (1000*(time.time()-t)))
    sys.exit()
  else:
    # normal interactive mode
    files = opts
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
##     try:
##       import psyco
##       psyco.profile()
##     except ImportError:
##       pass

    # destroy splash
    splash.destroy()
    del splash

  # start the application
  g = Store.pm.get_preference( 'geometry')
  if g:
    geometry = g
  else:
    geometry = "640x480+10+10"
  myapp.geometry(geometry)
  myapp.update_idletasks()
  myapp.deiconify()
  myapp.mainloop()
  #import profile
  #profile.run( 'myapp.mainloop()')
  #print("BKChem finished")
  myapp.destroy()

# the module was imported from outside
else:
  # application initialization
  myapp.initialize()
  # start the application
  g = Store.pm.get_preference( 'geometry')
  if g:
    geometry = g
  else:
    geometry = "640x480+10+10"
  myapp.geometry(geometry)
  myapp.update_idletasks()
  myapp.deiconify()

