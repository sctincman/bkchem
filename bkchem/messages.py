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

"""messages for use throughout the program"""

# DRAW

draw_mode_single = _("click on atom to add a new single bond, click on bond to change its order (or change direction)\nShift+click on a double bond to move the position of the second line")
draw_mode_fixed = _("length of the drawn bond is fixed to a preset value")
draw_mode_freestyle = _("freestyle drawing - no bond length or angle restrictions are applied")


# ARROW

arrow_mode_fixed = _("length of the drawn arrow (arrow part) is fixed to a preset value")
arrow_mode_freestyle = _("freestyle drawing - no arrow length or angle restrictions are applied")
arrow_mode_anormal = _("arrow is composed of straight lines")
arrow_mode_spline = _("arrow is drawn as a b-spline")


# ROTATION

rotate_mode_2D = _("drag an atom or a bond to 2D-rotate a molecule around its geometrical center")
rotate_mode_3D = _("drag an atom or a bond to 3D-rotate a molecule around its geometrical center \nPlease note that it is not possible to add a template to an atom with z-coordinate other than 0")


# VECTOR

vector_mode_square = _("click and drag to draw the corresponding shape")
vector_mode_rect = _("click and drag to draw the corresponding shape")
vector_mode_oval = _("click and drag to draw the corresponding shape")
vector_mode_circle = _("click and drag to draw the corresponding shape")
vector_mode_polygon = _("each left-button click creates one point of the polygon, right click closes it")


# MARKS

mark_mode_radical = _("click an atom to add a radical mark to it, it will be romoved in case it is already present")
mark_mode_biradical = _("click an atom to add a biradical mark to it, it will be romoved in case it is already present")
mark_mode_electronpair = _("click an atom to add a free electron pair mark to it, it will be romoved in case it is already present")
mark_mode_plusincircle = _("click an atom to add a plus mark to it, it will be romoved in case it is already present")
mark_mode_minusincircle = _("click an atom to add a minus mark to it, it will be romoved in case it is already present")


# BOND ALIGN

bond_align_mode_tovert = _("click a bond or two atoms to align the specified line into vertical position")
bond_align_mode_tohoriz = _("click a bond or two atoms to align the specified line into horizontal position")
bond_align_mode_invertthrough = _("click an atom or bond to perform an inversion of the molecule through this atom (center of the bond)")
bond_align_mode_mirrorthrough = _("click a bond or two atoms to mirror the molecule through the specified line")

