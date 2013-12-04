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

from __future__ import print_function

__all__ = []

# 'bitmap' and 'gtml' were removed for the release
_names = ["CML",
          "CML2",
          "openoffice",
          "ps_builtin",
          "molfile",
          "pdf_piddle",
          "ps_piddle",
          "pdf_cairo",
          "png_cairo",
          "odf",
          "svg_cairo",
          "ps_cairo",
          "CDXML"]

import sys

for _name in _names:
  try:
    exec('from . import %s' % _name)
    __all__.append(_name)
  except IOError:
    print("Could not load module %s" % _name, file=sys.stderr)

del _name
del _names
