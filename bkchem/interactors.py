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

"""here reside functions that implement a glue between application or paper
(main.py or paper.py) and the dialogs (dialogs.py)"""


from molecule import molecule
import Pmw
import tkMessageBox


def ask_name_for_selected( paper):
  """opens dialog for input of molecule name and sets it"""
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return

  dial = Pmw.PromptDialog( paper,
                           title='Name',
                           label_text=_('Name:'),
                           entryfield_labelpos = 'n',
                           buttons=(_('OK'),_('Cancel')))
  # if only one mol is selected use it as default
  if len( ms) == 1 and ms[0].name:
    dial.insertentry( 0, ms[0].name)
  res = dial.activate()
  if res == _('OK'):
    name = dial.get()
  else:
    return

  for m in ms:
    m.name = name
  paper.signal_to_app( _('Name %s was set to molecule(s)') % name)
  paper.start_new_undo_record()




def ask_id_for_selected( paper):
  """opens dialog for input of molecule ID and sets it"""
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return 

  if len( ms) > 1:
    tkMessageBox.showerror( _("Only one molecule should be selected."),
                            _("ID must be unique value, therefore it is obviously possible to set it to one molecule only. Please select only one molecule"))
    return

  m = ms[0]

  while 1:
    dial = Pmw.PromptDialog( paper,
                             title='Id',
                             label_text=_('Id:'),
                             entryfield_labelpos = 'n',
                             buttons=(_('OK'),_('Cancel')))
    # put the recent value
    if m.id:
      dial.insertentry( 0, m.id)

    res = dial.activate()
    if res == _('OK'):
      id = dial.get()
    else:
      return

    collision = 0
    for mol in paper.molecules:
      if mol != m and mol.id == id:
        tkMessageBox.showerror( _("ID collision"),
                                _("This ID is already used, use a different one"))
        collision = 1
        break
    if not collision:
      break

  m.id = id
  paper.signal_to_app( _('ID %s was set to molecule') % id)
  paper.start_new_undo_record()
