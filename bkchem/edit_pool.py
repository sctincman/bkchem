#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002, 2003, 2004 Beda Kosata <beda@zirael.org>

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


"""the 'edit pool' widget resides here"""

from Tkinter import Frame, Button, Entry
import Tkinter
import data, re, string
from groups_table import groups_table
import misc

font_decorations = ('italic', 'bold', 'subscript', 'superscript')
font_decorations_to_html = {'italic':'i', 'bold':'b', 'subscript':'sub', 'superscript':'sup'}

class editPool( Frame):

  def __init__( self, app, master, **kw):
    Frame.__init__( self, master, **kw)
    self.app = app
    self.text = ''
    self.editPool = Entry( self, width=60, state='disabled')
    self.editPool.pack( side='left')

    self.editPool.bind( '<Return>', self._interpretButtonPressed)
    self.editPool.bind( '<Escape>', self._cancel)

    self.editPool.bind("<KeyPress>", self._key)

    self.interpretButton = Button( self, text=_('Interpret'), command=self._interpretButtonPressed, state='disabled')
    self.interpretButton.pack( side='left')

    self.setButton = Button( self, text=_('As is'), command=self._setButtonPressed, state='disabled')
    self.setButton.pack( side='left')

    pix = self.app.request( 'pixmap', name='subnum')
    if pix:
      self.numbersToSubButton = Button( self, image=pix, command=self._numbersToSubButtonPressed, state='disabled')
      self.app.balloon.bind( self.numbersToSubButton, _('Subscript numbers'))
    else:
      self.numbersToSubButton = Button( self, text=_('Sub numbers'), command=self._numbersToSubButtonPressed, state='disabled')
    self.numbersToSubButton.pack( side='left')

    # text decoration
    for i in font_decorations:
      pix = self.app.request( 'pixmap', name=i)
      if pix:
        self.__dict__[ i] = Button( self,
                                    image=pix,
                                    command=misc.lazy_apply( self._tag_it, (font_decorations_to_html[i],)),
                                    state='disabled')
        self.app.balloon.bind( self.__dict__[i], i)
      else:
        self.__dict__[ i] = Button( self,
                                    text=i,
                                    command=misc.lazy_apply( self._tag_it, (font_decorations_to_html[i],)),
                                    state='disabled')
      self.__dict__[i].pack( side='left')


  def _interpretButtonPressed( self, *e):
    t = self.editPool.get()
    if string.lower( t) in groups_table:
      self._setText( t)
      #self._setText( groups_table[ string.lower(t)]['text'])
      #self.editPool.insert(0, self.text)
    else:
      self._setText( t)
      self.text = re.sub( "\\\\n", "\n", self.text)
    self._quit()

  def _setButtonPressed( self, *e):
    self._setText( self.editPool.get())
    self._quit()

  def _numbersToSubButtonPressed( self, *e):
    self._setText( re.sub( "\d+", '<sub>\g<0></sub>', self.editPool.get()))
    self._quit()

  def _cancel( self, e):
    self._setText( None)
    self._quit()

  def _quit( self):
    self.grab_release()
    self._disable()
    self._normaly_terminated = 1
    self.quit()

  def _disable( self):
    self.interpretButton.configure( state='disabled')
    self.numbersToSubButton.configure( state='disabled')
    self.setButton.configure( state='disabled')
    self.editPool.configure( state='disabled')
    self.italic.configure( state='disabled')
    self.bold.configure( state='disabled')
    self.superscript.configure( state='disabled')
    self.subscript.configure( state='disabled')
    
  def _enable( self):
    self.interpretButton.configure( state='normal')
    self.numbersToSubButton.configure( state='normal')
    self.setButton.configure( state='normal')
    self.editPool.configure( state='normal')
    self.italic.configure( state='normal')
    self.bold.configure( state='normal')
    self.superscript.configure( state='normal')
    self.subscript.configure( state='normal')

  def _setText( self, text):
    self.text = text
    self._update()

  def _update( self):
    self.editPool.delete(0, last='end')
    if self.text:
      self.editPool.insert(0, self.text)

  def activate( self, text=None, select=1):
    """activates edit_pool and returns inserted value (None if cancel occured),
    if parameter text is None it preserves the old one, use text='' to delete old text"""
    self.focus_set()
    self.grab_set()
    self._enable()
    # this is because I need to distinguish whether the mainloop was terminated "from inside"
    # or from outside (this most of the time means the application was killed and the widgets are no longer available)
    self._normaly_terminated = 0
    if text != None:
      self._setText( text)
    self.editPool.focus_set()
    if select:
      self.editPool.selection_range( 0, 'end')
    self.mainloop()
    if self._normaly_terminated:
      return self.text
    else:
      return None

  def _tag_it( self, tag):
    if self.editPool.selection_present():
      self.editPool.insert( Tkinter.SEL_FIRST, '<%s>' % tag)
      self.editPool.insert( Tkinter.SEL_LAST, '</%s>' % tag)
    else:
      self.editPool.insert( Tkinter.INSERT, '<%s></%s>' % (tag, tag))
      self.editPool.icursor( self.editPool.index( Tkinter.INSERT) - len( tag) - 3)
      

  def _key( self, event):
    from keysymdef import keysyms
    if len(event.keysym) > 1 and event.keysym in keysyms:
      if self.editPool.selection_present():
        self.editPool.delete( "anchor", "insert")
      self.editPool.insert( 'insert', unicode( keysyms[ event.keysym]))
      return "break"
