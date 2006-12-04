#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2006 Beda Kosata <beda@zirael.org>

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


class Tuning:

    # how to shift subscript in relation to the baseline (y)
    ftext_subscript_y_shift = 2
    
    # when placing subscript or superscript after a letter, how to tweak the x position
    ftext_supsubscript_x_shift = -1
    
    # how to shift texts x coordinate when exporting via piddle
    piddle_text_x_shift = 0.7