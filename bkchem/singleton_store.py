#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2004 Beda Kosata <beda@zirael.org>

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

"""The Store class which is a manager for application wide singletons resides here"""

class Store:

  """Store class is used as a central point where all the application wide singleton
  objects are stored.
  Making them class attributes allows to loosen the coupling in the system by
  avoiding explicit linking of other objects to these singletons."""
  
  app = None          # the application
  tm = None           # the template manager
  utm = None          # uset templates manager
  gm = None           # the group manager
  pm = None           # the preferences manager
  logger = None       # the logger
  log = None          # the log method of the logger (usually)
  id_manager = None   # the id manager
  
  # recently unused
  clipboard = None    # the clipboard
