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

"""the Splash class resides here"""

import Tkinter
import import_checker
import data

class Splash( Tkinter.Toplevel):

  def __init__( self):
    Tkinter.Toplevel.__init__( self)

    self.title(_('BKchem starting...'))
    #if import_checker.PIL_available:
    import pixmaps
    splash_image = pixmaps.splash_image
    #else:
    #  splash_image = None
    #splash_image = Tkinter.PhotoImage( file = '../images/logo.ppm')
    text = Tkinter.Label( self,
                          font=('Helvetica', 12, 'normal'),
                          relief = 'raised',
                          borderwidth = 2,
                          padx=50, pady=50,
                          image = splash_image,
                          text = data.splash_text
                          )
    text.pack(fill = 'both', expand = 1)

