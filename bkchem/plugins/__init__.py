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
#
#
#
#--------------------------------------------------------------------------

__all__ = []
_names = ['CML','CML2','openoffice','postscript','molfile','gtml','pdf','bitmap', 'postscript2']


import sys

for _name in _names:
  try:
    exec 'import %s' % _name
    __all__.append( _name)
  except:
    print >> sys.stderr, "could not load module %s" % _name

del _name
del _names
