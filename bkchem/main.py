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

"""the main application class resides here"""

from Tkinter import *
from paper import BKpaper
import Pmw
from xml_writer import SVG_writer, KIL_writer
from tkFileDialog import asksaveasfilename, askopenfilename
import os
import tkMessageBox
import xml.dom.minidom as dom
import data
import dom_extensions
import non_xml_writer
import import_checker
import dialogs
import export
import warnings
import plugins
import misc
from edit_pool import editPool


class BKchem( Tk):

  def __init__( self):
    Tk.__init__( self)

  def initialize( self):
    Pmw.initialise( self)
    import pixmaps
    if os.name == 'posix':
      try:
        self.option_add( "*font", ("-adobe-helvetica-medium-r-normal-*-*-100-*-*-*-*-*-*"))
      except:
        print "cannot init default font"
    else:
      self.option_add( "*font", ("Helvetica",10,"normal"))
    self.title( "BKchem")
    self.stat= StringVar()
    self.stat.set( "Idle")
    self.save_dir = '.'
    self.save_file = None
    self.svg_dir = '.'
    self.svg_file = ''
    self.post_file = ''
    self.kil_file = ''
    self.png_file = ''
    self.pov_file = ''

    self._after = None

    self.balloon = Pmw.Balloon( self)
    mainFrame = Frame( self)
    mainFrame.pack( fill='both', expand=1)

    # main drawing part
    paperFrame = Frame( mainFrame)
    self.paper = BKpaper( paperFrame, app=self, width=640, height=480, scrollregion=(0,0,'210m','297m'), background="grey", closeenough=5)
    self.scroll_y = Scrollbar( paperFrame, orient = VERTICAL, command = self.paper.yview)
    self.scroll_x = Scrollbar( paperFrame, orient = HORIZONTAL, command = self.paper.xview)
    self.paper.focus_set()
    
    # defining menu
    menu = Frame( mainFrame, relief=RAISED, bd=2)
    menu.pack( fill = X)

    helpButton = Menubutton( menu, text=_('Help'))
    helpButton.pack( side = RIGHT)
    
    helpMenu = Menu( helpButton, tearoff=0)
    helpButton['menu'] = helpMenu
    helpMenu.add( 'command', label=_('About'), command = self.about) 

    # file menu
    fileButton = Menubutton( menu, text=_('File'))
    fileButton.pack( side = LEFT)
    fileMenu = Menu( fileButton, tearoff=0)
    fileButton['menu'] = fileMenu
    fileMenu.add( 'command', label=_('New'), command = self._new_file)
    fileMenu.add( 'command', label=_('Save'), command = self.save_CDML, accelerator='(C-x C-s)')
    fileMenu.add( 'command', label=_('Save As...'), command = self.save_as_CDML, accelerator='(C-x C-w)')
    fileMenu.add( 'command', label=_('Load'), command = self.load_CDML, accelerator='(C-x C-f)')
    fileMenu.add( 'separator')
    # export cascade
    export_menu = Menu( fileButton, tearoff=0)
    export_cascade = fileMenu.add( 'cascade', label=_('Export'), menu = export_menu)
    export_menu.add( 'command', label=_('SVG'), command = self.save_SVG)
    # import cascade
    import_menu = Menu( fileButton, tearoff=0)
    import_cascade = fileMenu.add( 'cascade', label=_('Import'), menu = import_menu)
    # file properties
    fileMenu.add( 'separator')
    fileMenu.add( 'command', label=_('File properties'), command=self.change_properties)
    fileMenu.add( 'separator')
    fileMenu.add( 'command', label=_('Exit'), command = self._quit, accelerator='(C-x C-c)')

    # edit menu
    editButton = Menubutton( menu, text=_('Edit'))
    editButton.pack( side = LEFT)
    editMenu = Menu( editButton, tearoff=0)
    editButton['menu'] = editMenu
    editMenu.add( 'command', label=_('Undo'), command = self.paper.undo, accelerator='(C-z)')
    editMenu.add( 'command', label=_('Redo'), command = self.paper.redo, accelerator='(C-S-z)')
    editMenu.add( 'separator')
    editMenu.add( 'command', label=_('Cut'), command = lambda : self.paper.selected_to_clipboard( delete_afterwards=1), accelerator='(C-w)')
    editMenu.add( 'command', label=_('Copy'), command = self.paper.selected_to_clipboard, accelerator='(A-w)')
    editMenu.add( 'command', label=_('Paste'), command = lambda: self.paper.paste_clipboard( None), accelerator='(C-y)')
    editMenu.add( 'separator')
    editMenu.add( 'command', label=_('Selected to clipboard as SVG'), command = self.paper.selected_to_real_clipboard_as_SVG)
    editMenu.add( 'separator')
    editMenu.add( 'command', label=_('Select all'), command = self.paper.select_all, accelerator='(C-S-a)')
    #editMenu.add( 'separator')
    #editMenu.add( 'command', label=_('Sweep junk'), command = self.paper.sweep_junk)
    
    alignButton = Menubutton( menu, text=_('Align'))
    alignButton.pack( side = LEFT)
    alignMenu = Menu( alignButton, tearoff=0)
    alignButton['menu'] = alignMenu
    alignMenu.add( 'command', label=_('Top'), command = lambda : self.paper.align_selected( 't'), accelerator='(C-a t)')
    alignMenu.add( 'command', label=_('Bottom'), command = lambda : self.paper.align_selected( 'b'), accelerator='(C-a b)')
    alignMenu.add( 'separator')
    alignMenu.add( 'command', label=_('Left'), command = lambda : self.paper.align_selected( 'l'), accelerator='(C-a l)')
    alignMenu.add( 'command', label=_('Right'), command = lambda : self.paper.align_selected( 'r'), accelerator='(C-a r)')
    alignMenu.add( 'separator')
    alignMenu.add( 'command', label=_('Center horizontaly'), command = lambda : self.paper.align_selected( 'h'), accelerator='(C-a h)')
    alignMenu.add( 'command', label=_('Center verticaly'), command = lambda : self.paper.align_selected( 'v'), accelerator="(C-a v)")

    scaleButton = Menubutton( menu, text=_('Object'))
    scaleButton.pack( side= 'left')
    scaleMenu = Menu( scaleButton, tearoff=0)
    scaleButton['menu'] = scaleMenu
    scaleMenu.add( 'command', label=_('Scale'), command = self.scale)
    scaleMenu.add( 'separator')
    scaleMenu.add( 'command', label=_('Info'), command = self.paper.display_info_on_selected, accelerator='(C-o i)')
    scaleMenu.add( 'command', label=_('Check chemistry'), command = self.paper.check_chemistry_of_selected, accelerator='(C-o c)')
    scaleMenu.add( 'command', label=_('Expand groups'), command = self.paper.expand_groups, accelerator='(C-o e)')
    scaleMenu.add( 'separator')
    scaleMenu.add( 'command', label=_('Bring to front'), command = self.paper.lift_selected_to_top, accelerator='(C-o f)')
    scaleMenu.add( 'command', label=_('Send back'), command = self.paper.lower_selected_to_bottom, accelerator='(C-o b)')
    scaleMenu.add( 'command', label=_('Swap'), command = self.paper.lower_selected_to_bottom, accelerator='(C-o s)')
    # not done yet
    scaleMenu.add( 'separator')
    scaleMenu.add( 'command', label=_('Vertical'), command = self.paper.swap_sides_of_selected)
    scaleMenu.add( 'command', label=_('Horizontal'), command = lambda: self.paper.swap_sides_of_selected('horizontal') )
# for dev only
#    scaleMenu.add( 'separator')
#    scaleMenu.add( 'command', label=_('Flush mol'), command = self.paper.flush_first_selected_mol_to_graph_file)
    
    
    # following 2 lines should be commented in releases 
    #    scaleMenu.add( 'separator')
    #    scaleMenu.add( 'command', label=_('Debug'), command = self.paper._open_debug_console, accelerator='(A-d c)')
    
    optionsButton = Menubutton( menu, text=_('Options'))
    optionsButton.pack( side= 'left')
    optionsMenu = Menu( optionsButton, tearoff=0)
    optionsButton['menu'] = optionsMenu
    optionsMenu.add( 'command', label=_('Standard'), command=self.standard_values)


    # EXPERIMENTAL EXPORTS
    exportButton = Menubutton( menu, text=_('Experimental exports'))
    exportButton.pack( side= 'left')
    exportMenu = Menu( exportButton, tearoff=0)
    exportButton['menu'] = exportMenu
    exportMenu.add( 'command', label=_('Export PNG'), command = self.save_PNG, state=import_checker.PIL_state)
    
    # PLUGINS
    if plugins.__all__:
      self.plugins = []
      for name in plugins.__all__:
        plugin = plugins.__dict__[ name]
        self.plugins.append( plugin)
        if ('importer' in  plugin.__dict__) and plugin.importer:
          import_menu.add( 'command', label=plugin.name, command = misc.lazy_apply( self.plugin_import, [self.plugins.index( plugin)]))
        if ('exporter' in plugin.__dict__) and plugin.exporter:
          export_menu.add( 'command', label=plugin.name, command = misc.lazy_apply( self.plugin_export, [self.plugins.index( plugin)]))

    # mode selection panel     
    radioFrame = Frame( mainFrame)
    radioFrame.pack( fill=X)
    radiobuttons = Pmw.RadioSelect(radioFrame,
                     buttontype = 'button',
                     selectmode = 'single',
                     orient = 'horizontal',
                     command = self.change_mode,
                     hull_borderwidth = 0,
                     padx = 0,
                     pady = 0,
                     hull_relief = 'ridge',
             )
    radiobuttons.pack( side=LEFT)
    # Add some buttons to the radiobutton RadioSelect.
    for m in self.paper.modes_sort:
      if m in pixmaps.images:
        recent = radiobuttons.add( m, image=pixmaps.images[m], text=self.paper.modes[ m].name, activebackground='grey')
        self.balloon.bind( recent, self.paper.modes[ m].name)
      else:
        radiobuttons.add( m, text=self.paper.modes[ m].name)
    #sub-mode support
    self.subFrame = Frame( mainFrame)
    self.subFrame.pack( fill=X)
    self.subbuttons = []
    # the remaining of sub modes support is now in self.change_mode
    # atom name editing support
    self.editPool = editPool( self, mainFrame, width=60)
    self.editPool.pack( anchor=W)
    
    # main drawing part packing
    paperFrame.pack(fill='both', expand=1)
    self.paper.grid( row=0, column=0, sticky="news")
    paperFrame.grid_rowconfigure( 0, weight=1, minsize = 0)
    paperFrame.grid_columnconfigure( 0, weight=1, minsize = 0)
    self.scroll_x.grid( row=1, column=0, sticky='we')
    self.scroll_y.grid( row=0, column=1, sticky='ns')
    self.paper['yscrollcommand'] = self.scroll_y.set
    self.paper['xscrollcommand'] = self.scroll_x.set

    status = Label( mainFrame, relief=SUNKEN, bd=2, textvariable=self.stat, anchor='w')
    status.pack( fill=X, side='bottom')
    radiobuttons.invoke( self.paper.mode)

    # protocol bindings
    self.protocol("WM_DELETE_WINDOW", self._quit)


  def about( self):
    dialog = Pmw.MessageDialog(self,
                               title = _('About BKchem'),
                               defaultbutton = 0,
                               message_text = data.about_text)
    dialog.iconname('BKchem')
    dialog.activate()

  def change_mode( self, tag):
    import pixmaps
    self.paper.switch_to_mode( tag)
    if self.subbuttons:
      for butts in self.subbuttons:
        butts.deleteall()
    m = self.paper.mode
    for i in range( len( m.submodes)):
      if i >= len( self.subbuttons):
        self.subbuttons.append( Pmw.RadioSelect( self.subFrame,
                                                 buttontype = 'button',
                                                 selectmode = 'single',
                                                 orient = 'horizontal',
                                                 command = self.change_submode,
                                                 hull_borderwidth = 0,
                                                 padx = 0,
                                                 pady = 0,
                                                 hull_relief = 'ridge',
                                                 ))
        if i % 2:
          self.subbuttons[i].pack( side=LEFT, padx=10)
        else:
          self.subbuttons[i].pack( side=LEFT)
      for sub in m.submodes[i]:
        if sub in pixmaps.images:
          recent = self.subbuttons[i].add( sub, image=pixmaps.images[sub], activebackground='grey')
          self.balloon.bind( recent, m.submodes_names[i][m.submodes[i].index(sub)])
        else:
          self.subbuttons[i].add( sub, text=m.submodes_names[i][m.submodes[i].index(sub)])
      # black magic???
      j = m.submodes[i][ m.submode[i]]
      self.subbuttons[i].invoke( j)
    self.update_status( _('mode changed to ')+self.paper.modes[ tag].name)

  def change_submode( self, tag):
    self.paper.switch_to_submode( tag)

  def update_status( self, signal):
    self.stat.set( signal)
    if self._after:
      self.after_cancel( self._after)
    self._after = self.after( 4000, func=self.clear_status)

  def clear_status( self):
    self.stat.set( '')

  def save_CDML( self):
    if not self.save_file:
      self.save_as_CDML()
    else:
      a = os.path.join( self.save_dir, self.save_file)
      self._save_according_to_extension( a)

  def save_as_CDML( self):
    if not self.save_file:
      self.save_file = self._get_file_name()
    a = asksaveasfilename( defaultextension = ".svg", initialdir = self.save_dir, initialfile = self.save_file,
                           title = _("Save As..."), parent = self,
                           filetypes=((_("CD-SVG file"),".svg"),
                                      (_("Gzipped CD-SVG file"),".svgz"),
                                      (_("CDML file"),".cdml"),
                                      (_("Gzipped CDML file"),".cdgz")))
    if a != '':
      if self._save_according_to_extension( a):
        self.title( 'BKchem - %s' % self.save_file)
      else:
        self.save_file = None
    else:
      self.save_file = None

  def _save_according_to_extension( self, filename):
    self.save_dir, self.save_file = os.path.split( filename)
    ext = os.path.splitext( filename)[1]
    if ext == '.cdgz':
      type = _('gzipped CDML')
      success = export.export_CDML( self.paper, filename, gzipped=1)
    elif ext == '.cdml':
      type = _('CDML')
      success = export.export_CDML( self.paper, filename, gzipped=0)        
    elif ext == '.svgz':
      type = _('gzipped CD-SVG')
      success = export.export_CD_SVG( self.paper, filename, gzipped=1)
    else:
      type = _('CD-SVG')
      success = export.export_CD_SVG( self.paper, filename, gzipped=0)
    if success:
      self.update_status( _("saved to %s file: %s") % (type, self.save_file))
      self.paper.changes_made = 0
      return 1
    else:
      self.update_status( _("failed to save to %s file: %s") % (type, self.save_file))
      return 0

  def set_file_name( self, name, check_ext=0):
    """if check_ext is true append a .svg extension if no is present"""
    if check_ext and not os.path.splitext( name)[1]:
      self.save_file = name + ".svg"
    else:
      self.save_file = name
    self.title( 'BKchem - %s' % self.save_file)

  def load_CDML( self, file=None):
    if not self._load_CDML( file=file):
      self.save_file = None
    else:
      self.title( 'BKchem - %s' % self.save_file)

  def _load_CDML( self, file=None):
    if not file:
      if self.paper.changes_made:
        if tkMessageBox.askyesno( _("Forget changes?"),_("Forget changes in currently visiting file?"), default='yes') == 0:
          return 0
      a = askopenfilename( defaultextension = "",
                           initialdir = self.save_dir,
                           initialfile = self.save_file,
                           title = _("Load"),
                           parent = self,
                           filetypes=((_("All native formats"), (".svg", ".svgz", ".cdml", ".cdgz")),
                                      (_("CD-SVG file"), ".svg"),
                                      (_("Gzipped CD-SVG file"), ".svgz"),
                                      (_("CDML file"),".cdml"),
                                      (_("CDGZ file"),".cdgz"),
                                      (_("Gzipped files"), ".gz"),
                                      (_("All files"),"*")))
    else:
      a = file
    return self._load_CDML_file( a)

  def _load_CDML_file( self, a):
    if a != '':
      self.save_dir, self.save_file = os.path.split( a)
      ## try if the file is gzipped
      # try to open the file
      try:
        import gzip
        inp = gzip.open( a, "rb")
      except IOError:
        # can't read the file
        self.update_status( _("cannot open file ") + a)
        return None
      # is it a gzip file?
      it_is_gzip = 1
      try:
        str = inp.read()
      except IOError:
        # not a gzip file
        it_is_gzip = 0
      # if it's gzip file parse it
      if it_is_gzip:
        try:
          doc = dom.parseString( str)
        except:
          self.update_status( _("error reading file"))
          inp.close()
          return None
        inp.close()
        del gzip
        doc = doc.childNodes[0]
      else:
      ## otherwise it should be normal xml file
        ## try to parse it
        try:
          doc = dom.parse( a)
        except: 
          self.update_status( _("error reading file"))
          return None
        ## if it works check if its CDML of CD-SVG file
        doc = doc.childNodes[0]
      ## check if its CD-SVG or CDML
      if doc.nodeName == 'svg':
        ## first try if there is the right namespace
        docs = doc.getElementsByTagNameNS( data.cdml_namespace, 'cdml')
        if docs:
          doc = docs[0]
        else:
          # if not, try it without it
          docs = doc.getElementsByTagName( 'cdml')
          if docs:
            # ask if we should proceed with incorrect namespace
            proceed = tkMessageBox.askyesno( _("Proceed?"),
                                             _("CDML data seem present in SVG but have wrong namespace. Proceed?"),
                                             default='yes')
            if proceed:
              doc = docs[0]
            else:
              self.update_status(_("file not loaded"))
              return None
          else:
            ## sorry but there is no cdml in the svg file
            self.update_status(_("cdml data are not present in SVG or are corrupted!"))
            return None
      self.paper.clean_paper()
      self.paper.read_package( doc)
      self.update_status( _("loaded file: ")+a)
      return 1

  def save_SVG( self):
    if not self.svg_file:
      self.svg_file = self._get_file_name()+".svg"
    a = asksaveasfilename( defaultextension = ".svg", initialdir = self.svg_dir, initialfile = self.svg_file,
                         title = _("Export SVG"), parent = self, filetypes=((_("SVG file"),"*.svg"),))
    if a != '':
      self.svg_dir, self.svg_file = os.path.split( a)
      try:
        inp = open( a, "w")
      except IOError, x:
        raise "unable to open to file ", x
      exporter = SVG_writer( self.paper)
      exporter.construct_dom_tree( self.paper.get_all_containers())
      dom_extensions.safe_indent( exporter.document.childNodes[0])
      inp.write( exporter.document.toxml())
      inp.close()
      self.update_status( _("exported to SVG file: ")+self.svg_file)

  def save_PNG( self):
    if not self.png_file:
      self.png_file = self._get_file_name()+".png"
    a = asksaveasfilename( defaultextension = ".png", initialdir = self.svg_dir, initialfile = self.png_file,
                         title = _("Export PNG"), parent = self, filetypes=((_("PNG file"),"*.png"),))
    if a != '':
      self.svg_dir, self.png_file = os.path.split( a)
      try:
        non_xml_writer.Bitmap_writer( self.paper).write_image( a)
      except IOError, x:
        raise "unable to open to file ", x
      self.update_status( _("exported to PNG file: ")+self.png_file)


  def _update_geometry( self, e):
    pass

  def scale( self):
    dialog = dialogs.scale_dialog( self)
    if dialog.result:
      x, y = dialog.result
      self.paper.scale_selected( x/100, y/100)
    
  def _get_file_name( self):
    if self.save_file:
      return os.path.splitext( self.save_file)[0]
    else:
      return 'untitled'

  def _quit( self):
    if self.paper.changes_made:
      if tkMessageBox.askyesno( _("Really quit?"), _("There are unsaved changes, do you really want to quit?"),
                                parent=self, default='yes'):
        self.quit()
    else:
      self.quit()
      
  def plugin_import( self, pl_id):
    plugin = self.plugins[ pl_id]
    if self.paper.changes_made:
      if tkMessageBox.askyesno( _("Forget changes?"),_("Forget changes in currently visiting file?"), default='yes', parent=self) == 0:
        return 0
    types = []
    if 'extensions' in plugin.__dict__ and plugin.extensions:
      for e in plugin.extensions:
        types.append( (plugin.name+" "+_("file"), e))
    types.append( (_("All files"),"*"))
    a = askopenfilename( defaultextension = "",
                         initialdir = self.save_dir,
                         initialfile = self.save_file,
                         title = _("Load")+" "+plugin.name,
                         parent = self,
                         filetypes=types)
    if a != '':
      importer = plugin.importer()
      if importer.on_begin():
        import plugins.plugin
        try:
          doc = importer.get_cdml_dom( a)
        except plugins.plugin.import_exception, detail:
          tkMessageBox.showerror( _("Import error"), _("Plugin failed to import with following error:\n %s") % detail) 
          return
#        except:
#          import sys
#          tkMessageBox.showerror( "Import error", "Plugin crashed with error:\n %s" % sys.exc_info()[1])
#          return
        self.paper.clean_paper()
        self.paper.read_package( doc)
        self.update_status( _("loaded file: ")+a)

  def plugin_export( self, pl_id):
    plugin = self.plugins[ pl_id]
    exporter = plugin.exporter( self.paper)
    if not exporter.on_begin():
      return
    file_name = self._get_file_name()
    types = []
    if 'extensions' in plugin.__dict__ and plugin.extensions:
      file_name += plugin.extensions[0]
      for e in plugin.extensions:
        types.append( (plugin.name+" "+_("file"), e))
    types.append( (_("All files"),"*"))
    a = asksaveasfilename( defaultextension = types[0][1],
                           initialdir = self.save_dir,
                           initialfile = file_name,
                           title = _("Export")+" "+plugin.name,
                           parent = self,
                           filetypes=types)
    if a != '':
      try:
        doc = exporter.write_to_file( a)
      except plugins.plugin.export_exception, detail:
        tkMessageBox.showerror( _("Export error"), _("Plugin failed to export with following error:\n %s") % detail)
        return
#      except:
#        tkMessageBox.showerror( _("Export error"), _("Plugin failed to export with an unknown error"))
#        return

      self.update_status( _("exported file: ")+a)
  
  def _new_file( self):
    if self.paper.changes_made:
      if tkMessageBox.askyesno( _("Forget changes?"),_("Forget changes in currently visiting file?"), default='yes', parent=self) == 0:
        return 0
    self.paper.clean_paper()
    self.paper.set_paper_properties( type='A4', orientation='portrait')
    self.save_file = None
    self.title( "BKchem")


  def change_properties( self):
    dial = dialogs.file_properties_dialog( self, self.paper)

  def standard_values( self):
    dial = dialogs.standard_values_dialog( self, self.paper.standard)
    if dial.change:
      old_standard = self.paper.standard
      self.paper.standard = dial.standard
      # apply all values or only the changed ones
      if dial.apply_all:
        old_standard = None
      if not dial.apply:
        return
      elif dial.apply == 2:
        [o.redraw() for o in self.paper.apply_current_standard( old_standard=old_standard)]
      elif dial.apply == 1:
        [o.redraw() for o in self.paper.apply_current_standard( objects=self.paper.selected, old_standard=old_standard)]
      self.paper.add_bindings()
      self.paper.start_new_undo_record()
  

  def request( self, type, **options):
    """used by submodules etc. for requests of application wide resources such as pixmaps etc."""
    import pixmaps
    if type == 'pixmap':
      if 'name' in options:
        name = options['name']
        if name in pixmaps.images:
          return pixmaps.images[ name]
        else:
          return None
      return None
    
