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
import validator
import widgets
import xml


def ask_name_for_selected( paper):
  """opens dialog for input of molecule name and sets it"""
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return

  dial = Pmw.PromptDialog( paper,
                           title=_('Name'),
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
                             title=_('Id'),
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





def check_validity( app, mols):
  val = validator.validator()
  val.validate( mols)
  if val.report.text_atoms:
    import tkMessageBox
    tkMessageBox.showerror( _("Validity error"),
                            _("Sorry but your drawing includes 'text atoms'\n - atoms with no chemical sense.") + "\n\n" +
                            _("It is not possible to export them.") + "\n\n" +
                            _("For details check the chemistry with '%s/%s'.") % (_("Chemistry"), _("Check chemistry")))
    return 0
  if val.report.exceeded_valency:
    import tkMessageBox
    tkMessageBox.showwarning( _("Validity warning"),
                              _("Your drawing includes some atoms with exceeded valency.") + "\n\n" + 
                              _("For details check the chemistry with '%s/%s'.") % (_("Chemistry"), _("Check chemistry")))
  if val.report.group_atoms:
    import tkMessageBox
    yes = tkMessageBox.askokcancel( _("Expand groups?"),
                                    _("Your drawing includes some groups.") + "\n\n" + 
                                    _("These must be expanded in order to get chemicaly valid drawing. The expansion could be undone afterwards.") + "\n\n"+
                                    _("Proceed with expansion?"))
    if yes:
      app.paper.expand_groups( selected=0)
      return 1
    else:
      return 0
  return 1





def ask_inchi_program_path( app):
  path = app.pm.get_preference( "inchi_program_path") or ""
  dial = widgets.FileSelectionWithText( app, title=_("The INChI program path"),
                                        prompt =_("Select the INChI program executable: "),
                                        value = path,
                                        filetypes=((_("Executable files"), ("*",)),)
                                        )
  a = dial.activate()
  if a == _("OK"):
    app.pm.add_preference( "inchi_program_path", dial.value)
    app.chemistry_menu.entryconfigure( _("Generate INChI"), state="normal")
    return 1
  return 0



def ask_display_form_for_selected( paper):
  top_levels, unique = paper.selected_to_unique_top_levels()
  ms = [o for o in top_levels if isinstance( o, molecule)]

  if not ms:
    tkMessageBox.showerror( _("No molecule selected."),
                            _("At least one molecule must be selected. Please select it."))
    return

  dial = Pmw.Dialog( paper,
                     title=_('Display Form'),
                     #defaultbutton = _('OK'),
                     buttons=(_('OK'),_('Cancel')))
  input = widgets.HTMLLikeInput( dial.interior(), paper.app)
  input.pack()
  input.editPool.focus_set()
                                 
  # if only one mol is selected use it as default
  if len( ms) == 1 and ms[0].display_form:
    input.text = ms[0].display_form
  res = dial.activate()
  if res == _('OK'):
    df = input.editPool.get()
    df = unicode( df).encode( 'utf-8')
    ## catch not well-formed text
    try:
      xml.sax.parseString( "<a>%s</a>" % df, xml.sax.ContentHandler())
    except xml.sax.SAXParseException:
      df = xml.sax.saxutils.escape( df)
      # the second round of try: except: should catch problems not
      # related to XML wellfomedness but rather to encoding
      try:
        xml.sax.parseString( "<a>%s</a>" % df, xml.sax.ContentHandler())
      except xml.sax.SAXParseException:        
        tkMessageBox.showerror( _("Parse Error"), _("Unable to parse the text-\nprobably problem with input encoding!"))
        self.app.paper.bell()
        return
  else:
    return

  for m in ms:
    m.display_form = df
  paper.signal_to_app( _('Display form %s was set to molecule(s)') % df)
  paper.start_new_undo_record()
