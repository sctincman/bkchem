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


"""chem_paper - the main drawing part for BKchem resides here"""

from __future__ import division

from Tkinter import Canvas
import tkFont, tkMessageBox
import classes
from molecule import molecule
from transform import transform 
from transform3d import transform3d
import misc
from temp_manager import template_manager
import string
import data
import config
import messages
import dom_extensions
import xml.dom.minidom as dom
import operator
from warnings import warn
import undo
import math
import xml_writer
from oasa import periodic_table as PT
import Pmw
import graphics
import types
import os_support
import copy
import dialogs
import CDML_versions
import os
from id_manager import id_manager
import parents
from reaction import reaction
import debug
import oasa
from external_data import external_data_manager
from group import group
import oasa
import geometry
from sets import Set
      



class chem_paper( Canvas, object):

  object_type = 'paper'
  all_names_to_bind = ('atom','bond','arrow','point','plus','text','vector','helper_rect')


  def __init__( self, master = None, app = None, file_name={}, **kw):
    Canvas.__init__( self, master, kw)
    
    self.app = app
    self.clipboard = None
    self.id_manager = id_manager()

    self.standard = self.get_personal_standard()
    self.submode = None
    self.selected = []    # selected item
    self.__in = 1
    self._id_2_object = {}
    self.stack = []
    
    # bindings to input events
    self.set_bindings()

    self.set_viewport()


    # undo manages
    self.um = undo.undo_manager( self)  # undo manager

    # external data management
    self.edm = external_data_manager()
    print "loaded definitions for classes:", self.edm.load_available_definitions()

    # file name
    self.file_name = file_name

    # paper sizes etc.
    self._paper_properties = {}
    self.set_default_paper_properties()

    self.changes_made = 0



  def set_bindings( self):
    if not self.app.in_batch_mode:
      self.bind( "<B1-Motion>", self._drag1)
      self.bind( "<ButtonRelease-1>", self._release1)
      self.bind( "<Button-1>", self._n_pressed1)
      self.bind( "<Shift-Button-1>", self._s_pressed1)
      self.bind( "<Shift-B1-Motion>", self._drag1)
      self.bind( "<Delete>", self.key_pressed)
      self.bind( "<Key>", self.key_pressed)
      self.bind( "<KeyRelease>", self.key_released)
      self.bind( "<Enter>", self.take_focus)
      self.bind( "<Button-3>", self._n_pressed3)
      self.bind( "<Button-2>", self._n_pressed2)
      self.bind( "<Motion>", self._move)
      self.bind( "<Leave>", self._leave)



  ### PROPERTIES


  # molecules
  def _get_molecules( self):
    return [o for o in self.stack if isinstance( o, molecule)]

  molecules = property( _get_molecules)


  # arrows
  def _get_arrows( self):
    return [o for o in self.stack if isinstance( o, classes.arrow)]

  arrows = property( _get_arrows)


  # pluses
  def _get_pluses( self):
    return [o for o in self.stack if isinstance( o, classes.plus)]

  pluses = property( _get_pluses)



  # texts
  def _get_texts( self):
    return [o for o in self.stack if isinstance( o, classes.text)]

  texts = property( _get_texts)


  # vectors
  def _get_vectors( self):
    return [o for o in self.stack if isinstance( o, graphics.vector_graphics_item)]

  vectors = property( _get_vectors)


  # top_levels
  def _get_top_levels( self):
    #print [o for o in self.stack if not isinstance( o, graphics.top_level)]
    return self.stack
    #return [o for o in self.stack if isinstance( o, graphics.top_level)]

  top_levels = property( _get_top_levels)


  ### // PROPERTIES




  def initialise( self):
    # template manager
    self.tm = self.app.tm
    # groups manager (for group expansions)
    self.gm = self.app.gm





  def add_bindings( self, active_names=()):
    self.lower( self.background)
    [o.lift() for o in self.stack]
    if not self.app.in_batch_mode:
      if not active_names:
        names = self.all_names_to_bind
      else:
        names = active_names
      for name in names:
        self.tag_bind( name, '<Enter>', self.enter_item)
        self.tag_bind( name, '<Leave>', self.leave_item)


  def remove_bindings( self):
    for tag in self.all_names_to_bind + ("mark",):
      self.tag_unbind( tag, '<Enter>')
      self.tag_unbind( tag, '<Leave>')
    
    
  ## event bound methods

  ## overall


  def _s_pressed1( self, event):
    "button 1 with shift"
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.mode.mouse_down( event, modifiers=['shift'])





  def _n_pressed1( self, event):
    "button 1 without anything"
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.mode.mouse_down( event)





  def _release1( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.mode.mouse_up( event)
    




  def _drag1( self, event):
    # unfortunately we need to simulate "enter" and "leave" in this way because
    # when B1 is down such events do not occur
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.update_cursor_position( event.x, event.y)
    self.app.mode.mouse_drag( event) 
    b = self.find_enclosed( event.x-2, event.y-2, event.x+2, event.y+2)
    if b:
      a = self.id_to_object( b[0])
    else:
      a = None
    if a:
      if not self.__in:
        self.__in = a
        self.app.mode.enter_object( self.__in, event)
      elif a != self.__in:
        self.__in = a
        self.app.mode.leave_object( event)
        self.app.mode.enter_object( self.__in, event)
    else:
      if self.__in:
        self.__in = None
        self.app.mode.leave_object( event)





  def _n_pressed3( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.mode.mouse_down3( event, modifiers=[])



  def _n_pressed2( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.mode.mouse_down2( event, modifiers=[])





  def _move( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.app.update_cursor_position( event.x, event.y)
    self.app.mode.mouse_move( event)





  def _enter( self, event):
    self.app.mode.clean_key_query()





  def _leave( self, event):
    self.app.mode.clean_key_query()

  # item bound methods





  def enter_item( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    try:
      a = self.id_to_object( self.find_withtag( 'current')[0])
    except IndexError:
      a = None
    if a and a != self.__in:
      self.__in = a
      self.app.mode.enter_object( self.__in, event)





  def leave_item( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    if self.__in:
      self.__in = None
      self.app.mode.leave_object( event)





  def key_pressed( self, event):
    self.app.mode.key_pressed( event)





  def key_released( self, event):
    self.app.mode.key_released( event)

  ## end of event bound methods





  def select( self, items):
    "adds an object to the list of other selected objects and calls their select() method"
    for o in items:
      if o.object_type == 'arrow' or o.object_type == 'polygon':
        # we cannot allow arrows or polygons to be selected because selection of arrow and its points
        # doubles some actions (moving etc.) and this couldn't be easily solved other way
        self.select( o.points)
      elif o.object_type == 'selection_rect' or o.object_type == 'selection_square':
        return
      elif o not in self.selected:
        self.selected.append( o)
        o.select()
    #print [o.object_type for o in self.selected]




  def unselect( self, items):
    "reverse of select()"
    for item in items:
      try:
        self.selected.remove( item)
        item.unselect()
      except ValueError:
        pass #warn( 'trying to unselect not selected object '+id( item))





  def unselect_all( self):
    map( lambda o: o.unselect(), self.selected)
    self.selected = []





  def delete_selected( self):
    # ARROW
    to_delete = [o for o in self.selected if o.object_type == 'arrow']
    [a.arrow.delete_point( a) for a in self.selected if a.object_type == 'point' and (a.arrow not in to_delete)]
    for a in self.arrows:
      if a.is_empty_or_single_point():
        if a not in to_delete:
          to_delete += [a]
      else:
        a.redraw()
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # PLUS
    to_delete = filter( lambda o: o.object_type == 'plus', self.selected)
    map( lambda o: o.delete(), to_delete)
    map( self.stack.remove, to_delete)
    # TEXT
    to_delete = filter( lambda o: o.object_type == 'text', self.selected)
    for t in to_delete:
      t.delete()
      self.stack.remove( t)
    # VECTOR GRAPHICS
    for o in [obj for obj in self.selected if obj.object_type == 'rect' or obj.object_type == 'oval']:
      o.delete()
      self.stack.remove( o)
    # polygon is special (points were removed on begining together with arrow points)
    to_delete = [o for o in self.selected if o.object_type == 'polygon']
    for a in self.vectors:
      if a.object_type == 'polygon':
        if a.is_empty_or_single_point():
          if a not in to_delete:
            to_delete += [a]
        else:
          a.redraw()
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # BOND AND ATOM
    bonds = [o for o in self.selected if o.object_type == 'bond']
    atoms = [o for o in self.selected if o.object_type == 'atom']
    deleted, new, mols_to_delete = [], [], []
    changed_mols = []
    for mol in self.molecules:
      items = [o for o in bonds+atoms if o.molecule == mol]
      if items:
        changed_mols.append( mol)
      now_deleted, new_mols = mol.delete_items( items)
      deleted += now_deleted
      new += new_mols
      if new_mols:
        mols_to_delete.append( mol)
    if new:
      map( self.stack.remove, mols_to_delete)
      self.stack.extend( new)
    empty_mols = filter( lambda o: o.is_empty(), self.molecules)
    [self.stack.remove( o) for o in empty_mols]
    # start new undo
    if self.selected:
      self.start_new_undo_record()
    self.selected = []
    #return deleted

    ## check reactions
    [a.reaction.check_the_references( self.stack) for a in self.arrows]
      

      




  def bonds_to_update2( self):
    a = map( lambda o: o.molecule.atoms_bonds( o), filter( lambda o: o.object_type == 'atom', self.selected))
    if a:
      return misc.filter_unique( reduce( operator.add, a))
    else:
      return []
    




  def bonds_to_update3( self):
    a = []
    for o in self.selected:
      if o.object_type == 'atom':
        for b in o.molecule.atoms_bonds( o):
          if (b not in a):
            a.append( b)
    return a





  def bonds_to_update( self):
    a = []
    s_atoms = [o for o in self.selected if o.object_type == 'atom'] # selected atoms
    for m in misc.filter_unique( [o.molecule for o in s_atoms]):
      for b in m.bonds:
        a1, a2 = b.atoms
        if (a1 in s_atoms) or (a2 in s_atoms):
          a.append( b)
    # if bond is also selected then it moves with and should not be updated
    return [b for b in a if b not in self.selected]





  def atoms_to_update( self):
    a = []
    for o in self.selected:
      if o.object_type == 'bond':
        a.extend( o.atoms)
    if a:
      return misc.difference( misc.filter_unique( a), self.selected)
    else:
      return []





  def arrows_to_update( self):
    a = map( lambda o: o.arrow, filter( lambda p: p.object_type == 'point', self.selected))
    return misc.filter_unique( a)





  def signal_to_app( self, signal, time=4):
    self.app.update_status( signal, time=time)





  def read_package( self, CDML):
    self.onread_id_sandbox_activate() # to sandbox the ids 

    original_version = CDML.getAttribute( 'version')
    success = CDML_versions.transform_dom_to_version( CDML, config.current_CDML_version)
    if not success:
      if not tkMessageBox.askokcancel( _('Proceed'),
				       _('''This CDML document does not seem to have supported version.
				       \n Do you want to proceed reading this document?'''),
				



       default = 'ok',
				       parent=self):
        return None
    # paper properties
    paper = [o for o in CDML.childNodes if (not o.nodeValue) and (o.localName == 'paper')]
    if paper:
      paper = paper[0]
      t = paper.getAttribute( 'type')
      o = paper.getAttribute( 'orientation')
      sx = paper.getAttribute( 'size_x')
      sy = paper.getAttribute( 'size_y')
      if paper.getAttribute( 'crop_svg'):
        cr = int( paper.getAttribute( 'crop_svg'))
      else:
        cr = 1
      self.set_paper_properties( type=t, orientation=o, x=sx, y=sy, crop_svg=cr)
    else:
      self.set_paper_properties( type='A4', orientation='portrait', crop_svg=1)
    # viewport
    viewport = dom_extensions.getFirstChildNamed( CDML, 'viewport')
    if viewport:
      viewport = viewport.getAttribute( 'viewport')
      self.set_viewport( view= map( float, viewport.split(' ')))
    else:
      self.set_viewport()
    # standard must be read before all items
    new_standard = self.read_standard_from_dom( CDML)
    old_standard = self.standard
    if new_standard:
      self.standard = new_standard
    for p in CDML.childNodes:
      if p.nodeName in data.loadable_types:
        o = self.add_object_from_package( p)
        if not o:
          continue
        if o.object_type == 'molecule':
          if float( original_version) < 0.12:
            # we need to know if the bond is positioned according to the rules or the other way
            # it is however very expensive for large molecules with many double bonds and therefore
            # it was in version '0.12' of CDML moved to the saved package and does not have to be
            # checked on start anymore
            [b.post_read_analysis() for b in o.bonds]
          o.draw( automatic="none")
        else:
          o.draw()
    # now check if the old standard differs
    if new_standard and old_standard != self.standard and not self.app.in_batch_mode:
      if not tkMessageBox.askokcancel( _('Replace standard values'),
				       messages.standards_differ_text,
                                       default = 'ok',
				       parent=self):
        self.standard = old_standard

    # external data
    ees = CDML.getElementsByTagName( "external-data")
    if ees:
      [self.edm.read_package( ee, self.id_manager) for ee in ees]

    # finish
    # we close the sandbox and generate new ids for everything
    self.onread_id_sandbox_finish()
    
    self.add_bindings()
    self.um.start_new_record()


  def onread_id_sandbox_activate( self):
    """For reading we provide a new, clean id_manager as a sandbox to prevent
    clashes between ids that might be already on the paper and ids that are in the file.
    This is especialy needed for copying and template addition (although this is done somewhere else)"""
    self.__old_id_manager = self.id_manager
    self.id_manager = id_manager()
    

  def onread_id_sandbox_finish( self, apply_to=None):
    self.id_manager = self.__old_id_manager
    del self.__old_id_manager
    if apply_to == None:
      os = self.stack
    else:
      os = apply_to
    for o in os:
      o.generate_id()
      if isinstance( o, molecule):
        [ch.generate_id() for ch in o.children]


  def get_package( self):
    doc = dom.Document()
    root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', config.current_CDML_version),
                                                                   ( 'xmlns', data.cdml_namespace)))
    info = dom_extensions.elementUnder( root, 'info')
    dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKchem', attributes = (('version',config.current_BKchem_version),))
    paper = dom_extensions.elementUnder( root, 'paper', attributes = (('type', self._paper_properties['type']),
                                                                      ('orientation', self._paper_properties['orientation']),
                                                                      ('crop_svg', '%d' % self._paper_properties['crop_svg'])))
    if self._paper_properties['type'] == 'custom':
      dom_extensions.setAttributes( paper, (('size_x', '%d' % self._paper_properties['size_x']),
                                            ('size_y', '%d' % self._paper_properties['size_y'])))
    dom_extensions.elementUnder( root, 'viewport', attributes = (('viewport','%f %f %f %f' % self._view),))
    root.appendChild( self.standard.get_package( doc))
    for o in self.stack:
      root.appendChild( o.get_package( doc))
    for a in self.arrows:
      if not a.reaction.is_empty():
        root.appendChild( a.reaction.get_package( doc))

    # external data
    root.appendChild( self.edm.get_package( doc))
    return doc
    

  def mrproper( self):
    self.unselect_all()
    
    import parents
    for a in self.stack:
      if isinstance( a, parents.container):
        for ch in a.children:
          del ch.paper
      del a.paper

    self.clean_paper()
    self.um.mrproper()

    del self.app
    del self.clipboard
    del self.id_manager
    del self.standard
    del self.submode
    self.mode = None
    self.gm = None
    self.tm = None
    del self.selected
    del self._id_2_object
    del self.um
    del self.file_name




  def clean_paper( self):
    "removes all items from paper and deletes them from molecules and items"
    self.delete( 'all')
    self.background = None
    self.unselect_all()
    del self._id_2_object
    self._id_2_object = {}
    del self.stack[:]
    self.um.clean()
    self.changes_made = 0
    




  def del_container( self, container):
    container.delete()
    self.stack.remove( container)





  def handle_overlap( self):
    "puts overlaping molecules together to one and then calles handle_overlap(a1, a2) for that molecule"
    #import time
    #ttt = time.time()
    overlap = []
    for a in self.find_withtag('atom'):
      x, y = self.id_to_object( a).get_xy()
      for b in self.find_overlapping( x-2, y-2, x+2, y+2):
        if (a != b) and ( 'atom' in self.gettags( b)):
          a1 = self.id_to_object( a)
          a2 = self.id_to_object( b)
          if ( abs( a1.x - a2.x) < 2) and ( abs( a1.y - a2.y) < 2): 
            if (not [a2,a1] in overlap) and a1.z == a2.z:
              overlap.append( [a1,a2])

    deleted = []
    if overlap:
      mols = misc.filter_unique( map( lambda a: map( lambda b: b.molecule, a), overlap))
      #print 3, time.time() - ttt
      a_eatenby_b1 = []
      a_eatenby_b2 = []
      for (mol, mol2) in mols:
        while (mol in a_eatenby_b1):
          mol = a_eatenby_b2[ a_eatenby_b1.index( mol)]
        while (mol2 in a_eatenby_b1):
          mol2 = a_eatenby_b2[ a_eatenby_b1.index( mol2)]
        if mol != mol2 and (mol2 not in a_eatenby_b1):
          mol.eat_molecule( mol2)
          a_eatenby_b1.append( mol2)
          a_eatenby_b2.append( mol)
          self.stack.remove( mol2)
        else:
          deleted.extend( mol.handle_overlap())
      #print 4, time.time() - ttt
      deleted.extend( reduce( operator.add, [mol.handle_overlap() for mol in misc.difference( a_eatenby_b2, a_eatenby_b1)], []))
      self.selected = misc.difference( self.selected, deleted)
      self.add_bindings()
      self.app.log( _('concatenated overlaping atoms'))
    #print 5, time.time() - ttt
      




  def set_name_to_selected( self, name, interpret=1):
    """sets name to all selected atoms and texts,
    also records it in an undo !!!"""
    for item in self.selected[:]:
      if isinstance( item, oasa.graph.vertex):
        if name:
          self.unselect( [item])
          v = item.molecule.create_vertex_according_to_text( item, name, interpret=self.app.editPool.interpret)
          item.copy_settings( v)
          item.molecule.replace_vertices( item, v)
          item.delete()
          v.draw()
          self.select( [v])
          debug.log( type( v))
      if item.object_type == 'text':
        if name:
          item.set_text( name)
          item.redraw()
    if self.selected:
      self.start_new_undo_record()





  def take_focus( self, event):
    self.focus_set()





  def register_id( self, id, object):
    self._id_2_object[ id] = object





  def unregister_id( self, id):
    try:
      del self._id_2_object[ id]
    except KeyError:
      warn( 'trying to unregister not registered id', UserWarning, 3)





  def id_to_object( self, id):
    try:
      return self._id_2_object[ id]
    except KeyError:
      return None





  def is_registered_object( self, o):
    """has this object a registered id?"""
    return o in self._id_2_object.values()



  def is_registered_id( self, id):
    return id in self._id_2_object.keys()




  def new_molecule( self):
    mol = molecule( self)
    self.stack.append( mol)
    return mol





  def add_molecule( self, mol):
    self.stack.append( mol)





  def new_arrow( self, points=[], spline=0):
    arr = classes.arrow( self, points=points, spline=spline)
    self.stack.append( arr)
    arr.draw()
    return arr





  def new_plus( self, x, y):
    pl = classes.plus( self, xy = (x,y))
    self.stack.append( pl)
    pl.draw()
    return pl





  def new_text( self, x, y, text=''):
    txt = classes.text( self, xy=(x,y), text=text)
    self.stack.append( txt)
    return txt





  def new_rect( self, coords):
    rec = graphics.rect( self, coords=coords)
    self.stack.append( rec)
    return rec





  def new_oval( self, coords):
    ovl = graphics.oval( self, coords=coords)
    self.stack.append( ovl)
    return ovl





  def new_square( self, coords):
    rec = graphics.square( self, coords=coords)
    self.stack.append( rec)
    return rec





  def new_circle( self, coords):
    ovl = graphics.circle( self, coords=coords)
    self.stack.append( ovl)
    return ovl





  def new_polygon( self, coords):
    p = graphics.polygon( self, coords=coords)
    self.stack.append( p)
    return p





  def list_bbox( self, items):
    """extension of Canvas.bbox to provide support for lists of items"""
    self.dtag( 'bbox', 'bbox') # just to be sure
    for i in items:
      self.addtag_withtag( 'bbox', i)
    ret = self.bbox( 'bbox')
    self.dtag( 'bbox', 'bbox')
    return ret





  def selected_to_clipboard( self, delete_afterwards=0, strict=0):
    """strict means that only what is selected is copied, not the whole molecule"""
    if self.selected:
      cp, unique = self.selected_to_unique_top_levels()
      # now find center of bbox of all objects in cp
      bboxs = []
      xmin, ymin, xmax, ymax = cp[0].bbox()
      for o in cp:
        x0, y0, x1, y1 = o.bbox()
      if x0 < xmin:
        xmin = x0
      if y0 < ymin:
        ymin = y0
      if x1 > xmax:
        xmax = x1
      if ymax < y1:
        ymax = y1
      xy = ( xmin+(xmax-xmin)/2, ymin+(ymax-ymin)/2)
      clipboard_doc = dom.Document()
      clipboard = dom_extensions.elementUnder( clipboard_doc, 'clipboard')
      for o in cp:
        if strict and isinstance( o, oasa.graph.graph):
          clipboard.appendChild( o.get_package( clipboard_doc, items=misc.intersection( o.children, self.selected)))
        else:
          clipboard.appendChild( o.get_package( clipboard_doc))
      self.app.put_to_clipboard( clipboard, xy)
      if delete_afterwards:
        [self.del_container(o) for o in cp]
        self.app.log( _("killed %s object(s) to clipboard") % str( len( cp)))
	self.start_new_undo_record()
      else:
        self.app.log( _("copied %s object(s) to clipboard") % str( len( cp)))
      return [xmin, ymin, xmax, ymax]






  def paste_clipboard( self, xy):
    """pastes items from clipboard to position xy"""
    clipboard = self.app.get_clipboard()
    clipboard_pos = self.app.get_clipboard_pos()
    if clipboard:
      new = []
      self.unselect_all()
      if xy:
        dx = xy[0] - clipboard_pos[0]
        dy = xy[1] - clipboard_pos[1]
      else:
        dx, dy = 20, 20
      # the same trick as in reading of files
      self.onread_id_sandbox_activate()

      os = []
      for p in clipboard.childNodes:
        o = self.add_object_from_package( p)
        os.append( o)
        o.draw()
        o.move( dx, dy)
        if o.object_type == 'molecule':
          self.select( o)
        elif o.object_type == 'arrow':
          self.select( o.points)
        else:
          self.select( [o])
      self.add_bindings()
      self.app.log( _("pasted from clipboard"))

      # put the id_manager back
      self.onread_id_sandbox_finish( apply_to=os)
      
      self.handle_overlap()
      self.start_new_undo_record()
      




  def add_object_from_package( self, package):
    if package.nodeName == 'molecule':
      o = molecule( self, package=package)
    elif package.nodeName == 'arrow':
      o = classes.arrow( self, package=package)
    elif package.nodeName == 'plus':
      o = classes.plus( self, package=package)
    elif package.nodeName == 'text':
      o = classes.text( self, package=package)
    elif package.nodeName == 'rect':
      o = graphics.rect( self, package=package)
    elif package.nodeName == 'oval':
      o = graphics.oval( self, package=package)
    elif package.nodeName == 'square':
      o = graphics.square( self, package=package)
    elif package.nodeName == 'circle':
      o = graphics.circle( self, package=package)
    elif package.nodeName == 'polygon':
      o = graphics.polygon( self, package=package)
    elif package.nodeName == 'reaction':
      react = reaction()
      react.read_package( package, self.id_manager)
      if react.arrows:
        react.arrows[0].reaction = react
      o = None
    else:
      o = None
    if o:
      self.stack.append( o)
    return o
    




  def align_selected( self, mode):
    """aligns selected items according to mode - t=top, b=bottom,
    l=left, r=right, h=horizontal center, v=vertical center"""
    # locate all selected top_levels, filter them to be unique
    to_align, unique = self.selected_to_unique_top_levels()
    # check if there is anything to align
    if len( to_align) < 2:
      return None
    bboxes = []
    if not unique:
      # if not unique align is done according to bboxes of top_levels
      for o in to_align:
        bboxes.extend( o.bbox())
    else:
      # otherwise align according to bboxes of items
      for o in self.selected:
        if o.object_type == 'atom':
          if o.show:
            bboxes.extend( o.ftext.bbox())
          else:
            x, y = o.get_xy()
            bboxes.extend( (x,y,x,y))
        elif o.object_type == 'point':
          x, y = o.get_xy()
          bboxes.extend( (x,y,x,y))
        elif o.object_type == 'bond':
          x1, y1, x2, y2 = o.bbox()
          x = (x1+x2)/2
          y = (y1+y2)/2
          bboxes.extend( (x,y,x,y))
        else:
          bboxes.extend( o.bbox())
    # now the align itself
    # modes dealing with x
    if mode in 'lrv':
      if mode == 'l':
        xs = [bboxes[i] for i in range( 0, len( bboxes), 4)] 
        x = min( xs)
      elif mode == 'r':
        xs = [bboxes[i] for i in range( 2, len( bboxes), 4)] 
        x = max( xs)
      else:
        xmaxs = [bboxes[i] for i in range( 0, len( bboxes), 4)] 
        xmins = [bboxes[i] for i in range( 2, len( bboxes), 4)]
        xs = map( operator.add, xmaxs, xmins)
        xs = map( operator.div, xs, len(xs)*[2])
        x = (max( xs) + min( xs)) / 2 # reduce( operator.add, xs) / len( xs) # this makes mean value rather then center 
      for i in range( len( xs)):
        to_align[i].move( x-xs[i], 0)
    # modes dealing with y
    elif mode in 'tbh':
      if mode == 'b':
        ys = [bboxes[i] for i in range( 3, len( bboxes), 4)] 
        y = max( ys)
      elif mode == 't':
        ys = [bboxes[i] for i in range( 1, len( bboxes), 4)] 
        y = min( ys)
      else:
        ymaxs = [bboxes[i] for i in range( 1, len( bboxes), 4)] 
        ymins = [bboxes[i] for i in range( 3, len( bboxes), 4)]
        ys = map( operator.add, ymaxs, ymins)
        ys = map( operator.div, ys, len(ys)*[2])
        y = (max( ys) + min( ys)) /2 # reduce( operator.add, ys) / len( ys) 
      for i in range( len( ys)):
        to_align[i].move( 0, y-ys[i])
    self.start_new_undo_record()





  def toggle_center_for_selected( self):
    for o in self.selected:
      if o.object_type == 'atom' and o.show:
        o.toggle_center()





  def selected_to_unique_top_levels( self):
    """maps all items in self.selected to their top_levels (atoms->molecule etc.),
    filters them to be unique and returns tuple of (unique_top_levels, unique)
    where unique is true when there was only one item from each container"""
    filtrate = []
    unique = 1
    for o in self.selected:
      if o.object_type == 'atom' or o.object_type == 'bond':
        if o.molecule not in filtrate:
          filtrate.append( o.molecule)
        else:
          unique = 0
      elif o.object_type == 'point':
        if o.arrow not in filtrate:
          filtrate.append( o.arrow)
        else:
          unique = 0
      else:
        if o not in filtrate:
          filtrate.append( o)
        else:
          unique = 0
    return (filtrate, unique)
          




  def undo( self):
    self.unselect_all()
    i = self.um.undo()
    self.changes_made = 1
    if i > 0:
      self.app.log( _("undo (%d further undos available)") % i)
    else:
      self.app.log( _("no further undo"))
    




  def redo( self):
    self.unselect_all()
    i = self.um.redo()
    self.changes_made = 1
    if i > 0:
      self.app.log( _("redo (%d further redos available)") % i)
    else:
      self.app.log( _("no further redo"))
    




  def scale_selected( self, ratio_x, ratio_y, scale_font=1):
    top_levels, unique = self.selected_to_unique_top_levels()
    ratio = math.sqrt( ratio_x*ratio_y) # ratio for operations where x and y can't be distinguished (font size etc.)
    tr = transform()
    tr.set_scaling_xy( ratio_x, ratio_y)
    for o in top_levels:
      if o.object_type == 'molecule':
        for i in o.atoms:
          x, y = tr.transform_xy( i.x, i.y)
          i.move_to( x, y)
          if scale_font:
            i.scale_font( ratio)
          if i.show:
            i.redraw()
        for i in o.bonds:
          i.bond_width *= ratio
          i.redraw()
      if o.object_type == 'arrow' or o.object_type == 'polygon':
        for i in o.points:
          x, y = tr.transform_xy( i.x, i.y)
          i.move_to( x, y)
        o.redraw()
      if o.object_type == 'text':
        x, y = tr.transform_xy( o.x, o.y)
        o.move_to( x, y)
        if scale_font:
          o.scale_font( ratio)
        o.redraw()
      if o.object_type == 'plus':
        x, y = tr.transform_xy( o.x, o.y)
        o.move_to( x, y)
        if scale_font:
          o.scale_font( ratio)
        o.redraw()
      elif o.object_type in ('rect', 'oval'):
        coords = tr.transform_4( o.coords)
        o.resize( coords)
        o.redraw()
        o.unselect()
        o.select()
    if top_levels:
      self.add_bindings()
      self.start_new_undo_record()






  def selected_to_real_clipboard_as_SVG( self):
    """exports selected top_levels as SVG to system clipboard"""
    cont, unique = self.selected_to_unique_top_levels()
    exporter = xml_writer.SVG_writer( self)
    exporter.construct_dom_tree( cont)
    self.clipboard_clear()
    self.clipboard_append( exporter.get_nicely_formated_document())
    self.app.log( _("selected top_levels were exported to clipboard in SVG"))





  def start_new_undo_record( self, name=''):
    if not self.changes_made:
      self.changes_made = 1
    self.um.start_new_record( name=name)





  def display_weight_of_selected( self):
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    w = 0
    for m in s_mols:
      w += m.get_formula_dict().get_molecular_weight()
    self.app.update_status( str( w))





  def display_info_on_selected( self):
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    if not s_mols:
      return

    dialog = Pmw.TextDialog( self, title=_("Info on selected molecules"))
    dialog.withdraw()

    ws = 0
    comps = PT.formula_dict()
    for m in s_mols:
      comp = m.get_formula_dict()
      comps += comp
      dialog.insert( 'end', _("Name: %s") % m.name)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Id: %s") % m.id)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Formula: %s") % comp)
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Weight: %4.3f") % comp.get_molecular_weight())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Composition: %s") % PT.dict_to_composition( comp))
      dialog.insert( 'end', "\n\n")
    if len( s_mols) > 1:
      dialog.insert( '1.0', "\n")
      dialog.insert( "1.0", _("Individual molecules:"), 'headline')
      dialog.insert( '1.end', "\n")      
      dialog.insert( 'end', "\n")
      dialog.insert( "end", _("Summary for all selected molecules:"), 'headline')
      dialog.insert( 'end', "\n\n")
      dialog.insert( "end", _("Formula: %s") % comps)
      dialog.insert( 'end', "\n")
      dialog.insert( "end", _("Weight: %4.3f") % comps.get_molecular_weight())
      dialog.insert( 'end', "\n")
      dialog.insert( 'end', _("Composition: %s") % PT.dict_to_composition( comps))
    dialog.tag_config( 'headline', underline=1)
    dialog.activate()






  def check_chemistry_of_selected( self):
    import validator
    val = validator.validator()
    s_mols = [m for m in self.selected_to_unique_top_levels()[0] if m.object_type == 'molecule']
    if not s_mols:
      return

    dialog = Pmw.TextDialog( self, title=_("Chemistry check of selected molecules"))
    dialog.withdraw()

    val.validate( s_mols)
    dialog.insert( 'end', val.report.get_summary())

    dialog.activate()






  def select_all( self):
    self.unselect_all()
    self.select( [o for o in map( self.id_to_object, self.find_all()) if o and o.object_type != 'arrow']) 
    self.add_bindings()
    




  def set_viewport( self, view=(0,0,640,480)):
    x1, y1, x2, y2 = view
    self._view = tuple( view)
    
    self._real2screen = transform()
    self._real2screen.set_move( -x1, -y1)
    ratiox, ratioy = 640/(x2-x1), 480/(y2-y1)
    self._real2screen.set_scaling_xy( ratiox, ratioy)
    self._ratio = math.sqrt( ratioy*ratiox)

    self._screen2real = transform()
    ratiox, ratioy = (x2-x1)/640, (y2-y1)/480
    self._screen2real.set_scaling_xy( ratiox, ratioy)
    self._screen2real.set_move( x1, y1)
  




  def screen_to_real_coords( self, coords):
    """transforms set of x,y coordinates to real coordinates, input list must have even length"""
    if len( coords) % 2:
      raise "only even number of coordinates could be transformed"
    out = []
    for i in range( 0, len( coords), 2):
      out.extend( self._screen2real.transform_xy( coords[i], coords[i+1]))
    return out





  def real_to_screen_coords( self, coords):
    """transforms set of x,y coordinates to screen coordinates, input list must have even length"""
    if len( coords) % 2:
      raise "only even number of coordinates could be transformed"
    out = []
    for i in range( 0, len( coords), 2):
      out.extend( self._real2screen.transform_xy( coords[i], coords[i+1]))
    return out





  def screen_to_real_ratio( self):
    return 1.0/self._ratio





  def real_to_screen_ratio( self):
    return self._ratio





  def expand_groups( self, selected=1):
    """expands groups, if selected==1 only for selected, otherwise for all"""
    if selected:
      mols = [o for o in self.selected_to_unique_top_levels()[0] if o.object_type == 'molecule']
      atoms = [o for o in self.selected if isinstance( o, group)]
      self.unselect_all()
      for mol in mols:
        this_atoms = misc.intersection( atoms, mol.atoms)
        mol.expand_groups( atoms = this_atoms)
    else:
      self.unselect_all()
      [m.expand_groups() for m in self.molecules]
    self.add_bindings()
    self.start_new_undo_record()





  def lift_selected_to_top( self):
    os = self.selected_to_unique_top_levels()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.append( o)
    self.app.log( _("selected items were lifted"))
    self.add_bindings()
    self.start_new_undo_record()





  def lower_selected_to_bottom( self):
    os = self.selected_to_unique_top_levels()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.insert( 0, o)
    self.app.log( _("selected items were put back"))
    self.add_bindings()
    self.start_new_undo_record()





  def swap_selected_on_stack( self):
    os = self.selected_to_unique_top_levels()[0]
    indxs = [self.stack.index( o) for o in os]
    indxs.sort()
    for i in range( len( indxs) // 2):
      self.stack[ indxs[i]], self.stack[ indxs[-1-i]] =  self.stack[ indxs[-1-i]], self.stack[ indxs[i]]
    self.app.log( _("selected items were swapped"))
    self.add_bindings()
    self.start_new_undo_record()





  def _open_debug_console( self):
    m = self.app.mode
    for i in m.__dict__:
      print i, ' : ', m.__dict__[i]






  def any_color_to_rgb_string( self, color):
    r, g, b = map( lambda x: (x < 256 and x) or (x >= 256 and x//256),  self.winfo_rgb( color))
    return "#%02x%02x%02x" % (r,g,b)
  


  def set_default_paper_properties( self):
    t = self.standard.paper_type
    o = self.standard.paper_orientation
    if o == 'portrait':
      sy, sx = data.paper_types[t]
    else:
      sx, sy = data.paper_types[t]

    self._paper_properties = {'type': t,
                              'orientation': o,
                              'size_x': sx,
                              'size_y': sy}
                              
    if not 'background' in self.__dict__ or not self.background:
      self.background = self.create_rectangle( 0, 0, '%dm'%sx, '%dm'%sy, fill='white', outline='black', tags="no_export")
    else:
      self.coords( self.background, 0, 0, '%dm'%sx, '%dm'%sy)

    # crop svg
    self._paper_properties['crop_svg'] = self.standard.paper_crop_svg
    

  def create_background( self):
    sx = self._paper_properties['size_x']
    sy = self._paper_properties['size_y']

    if not 'background' in self.__dict__ or not self.background:
      self.background = self.create_rectangle( 0, 0, '%dm'%sx, '%dm'%sy, fill='white', outline='black', tags="no_export")
    else:
      self.coords( self.background, 0, 0, '%dm'%sx, '%dm'%sy)
    


  def set_paper_properties( self, type=None, orientation=None, x=None, y=None, crop_svg=None, all=None):
    if all:
      self._paper_properties = copy.copy( all)
      return
    if type:
      if type != 'custom':
        t = type or self.standard.paper_type
        o = orientation or self.standard.paper_orientation
        if o == 'portrait':
          sy, sx = data.paper_types[t]
        else:
          sx, sy = data.paper_types[t]
      else:
        t = 'custom'
        o = orientation or self._paper_properties['orientation']
        sx, sy = x, y
      self._paper_properties = {'type': t,
                                'orientation': o,
                                'size_x': sx,
                                'size_y': sy}
                              
    # crop svg
    if crop_svg != None:
      self._paper_properties['crop_svg'] = crop_svg

    self.create_background()





  def get_paper_property( self, name):
    if name in self._paper_properties:
      return self._paper_properties[ name]
    else:
      return None

    
## def coords( self, item, *args, **keyargs):
##     if 'unit' in keyargs:
##       u = keyargs['unit']
##       if u == 'cm':
##         if args:
##           return map( self.px_to_cm, Canvas.coords( self, item, args))
##         else:
##           return map( self.px_to_cm, Canvas.coords( self, item))
##     if args:
##       return Canvas.coords( self, item, *args)
##     else:
##       return Canvas.coords( self, item)





  def px_to_cm( self, px):
    """transforms coord from px to cm"""
    return self.px_to_unit( px, unit='cm')





  def cm_to_px( self, cm):
    """transforms coord from cm to px"""
    return self.winfo_fpixels( '%fm' % (cm*10))





  def mm_to_px( self, mm):
    """transforms coord from mm to px"""
    return self.winfo_fpixels( '%fm' % mm)





  def read_xml_point( self, point):
    x = point.getAttribute( 'x')
    y = point.getAttribute( 'y')
    z = point.getAttribute( 'z')
    return map( self.any_to_px, (x,y,z))
    




  def any_to_px( self, xyz):
    if type( xyz) == types.TupleType or type( xyz) == types.ListType:
      return [self.any_to_px( i) for i in xyz]
    a, au = misc.split_number_and_unit( xyz)
    if au:
      if au == 'cm':
        a = self.cm_to_px( a)
      elif au == 'mm':
        a = self.mm_to_px( a)
      if au == 'px':
        return a
    return a





  def px_to_unit( self, xyz, unit='cm', round_to=3):
    # handle sets of values
    if type( xyz) == types.TupleType or type( xyz) == types.ListType:
      return [self.px_to_unit( i, unit=unit, round_to=round_to) for i in xyz]
    # handle empty queries
    if xyz == None:
      return None
    # different units
    if unit == 'cm':
      dots_per_unit = self.winfo_fpixels( '100m')/10.0
    elif unit == 'mm':
      dots_per_unit = self.winfo_fpixels( '100m')/100.0
    elif unit == 'in':
      dots_per_unit = self.winfo_fpixels( '254m')/10.0
    else:
      warn( "unknown unit passed to paper.px_to_unit")
      return None
    # round or not round and return
    if round_to == None:
      return xyz/dots_per_unit
    else:
      return round( xyz/dots_per_unit, round_to)
  
    




  def px_to_text_with_unit( self, xyz, unit='cm', round_to=3):
    # handle sets of values
    if type( xyz) == types.TupleType or type( xyz) == types.ListType:    
      return [self.px_to_text_with_unit( i, unit=unit, round_to=round_to) for i in xyz]
    # round or not round and return
    if round_to == None:
      return '%f%s' % (self.px_to_unit( xyz, unit=unit, round_to=round_to), unit)
    else:
      return ('%.'+str( round_to)+'f%s') % (self.px_to_unit( xyz, unit=unit, round_to=round_to), unit)
    




  def read_standard_from_dom( self, d):
    std = dom_extensions.getFirstChildNamed( d, 'standard')
    if std:
      st = classes.standard()
      st.read_package( std)
      return st
    return None





  def apply_current_standard( self, objects=[], old_standard=None, template_mode=0):
    """if no objects are given all are used, if old_standard is given only the values
    that have changed are applied; in template mode no changes of paper format are made"""
    if not template_mode:
      self.create_background()
    objs = objects or self.top_levels
    to_redraw = []
    st = self.standard
    for m in objs:
      if m.object_type == 'molecule':
        for b in m.bonds:
          b.read_standard_values( old_standard=old_standard)
          to_redraw.append( b)
        for a in m.atoms:
          a.read_standard_values( old_standard=old_standard)
          to_redraw.append( a)
      else:
        m.read_standard_values( old_standard=old_standard)
        to_redraw.append( m)
    return to_redraw
          




  def get_personal_standard( self):
    name = os_support.get_config_filename( 'standard.cdml', level="personal", mode="r")
    if name:
      try:
        cdml = dom.parse( name).childNodes[0]
      except:
        return classes.standard()
      return self.read_standard_from_dom( cdml)
    return classes.standard()





  def save_personal_standard( self, st):
    name = os_support.get_config_filename( 'standard.cdml', level="personal", mode="w")
    if name:
      doc = dom.Document()
      root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', config.current_CDML_version),
                                                                     ( 'xmlns', data.cdml_namespace)))
      info = dom_extensions.elementUnder( root, 'info')
      dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKchem', attributes = (('version',config.current_BKchem_version),))
      root.appendChild( st.get_package( doc))
      dom_extensions.safe_indent( root)
      try:
        f = file( name, 'w')
      except IOError:
        return 0
      try:
        f.write( doc.toxml().encode('utf-8'))
      except IOError:
        f.close()
        return 0
      f.close()
      return name
    return 0






  def swap_sides_of_selected( self, mode="vertical"):
    """mirrors the selected things, vertical uses y-axis as a mirror plane,
    horizontal x-axis"""
    # locate all selected top_levels, filter them to be unique
    to_align, unique = self.selected_to_unique_top_levels()
    to_select_then = copy.copy( self.selected)
    self.unselect_all()
    # check if there is anything to align
    if len( to_align) < 1:
      return None
    bboxes = []
    for o in to_align:
      bboxes.extend( o.bbox())
    # vertical (rotate around y axis)
    if mode == 'vertical':
      xs = [bboxes[i] for i in range( 0, len( bboxes), 2)]
      x0 = (max( xs) + min( xs)) / 2.0
      for o in to_align:
        if o.object_type == 'molecule':
          tr = transform()
          tr.set_move( -x0, 0)
          tr.set_scaling_xy( -1, 1)
          tr.set_move( x0, 0)
          o.transform( tr)
        else:
          pass
    # horizontal (rotate around x axis)
    if mode == 'horizontal':
      ys = [bboxes[i] for i in range( 1, len( bboxes), 2)]
      y0 = (max( ys) + min( ys)) / 2.0
      for o in to_align:
        if o.object_type == 'molecule':
          tr = transform()
          tr.set_move( 0, -y0)
          tr.set_scaling_xy( 1, -1)
          tr.set_move( 0, y0)
          o.transform( tr)
        else:
          pass

    self.select( to_select_then)
    self.add_bindings()
    self.start_new_undo_record()






  def flush_first_selected_mol_to_graph_file( self):
    mols, u = self.selected_to_unique_top_levels()
    for m in mols:
      if m in self.molecules:
        m.flush_graph_to_file()
        return
    




  def config_selected( self):
    if self.selected:
      dialog = dialogs.config_dialog( self.app, self.selected[:])
      if dialog.changes_made:
        self.start_new_undo_record()
      self.add_bindings()





  def get_base_name( self):
    return os.path.splitext( self.file_name['name'])[0]






  def _get_full_path( self):
    return os.path.abspath( os.path.join( self.file_name['dir'], self.file_name['name']))

  full_path = property( _get_full_path)
    




  def _get_window_name( self):
    return self.create_window_name( self.file_name)

  window_name = property( _get_window_name)




  def create_window_name( name_dict):
    if name_dict['ord'] == 0:
      return name_dict['name']
    else:
      return name_dict['name'] + '<%d>' % name_dict['ord']
    
  create_window_name = staticmethod( create_window_name)



  def clean_selected( self):
    """cleans the geomerty of all selected molecules, the position of atoms that are selected will not be changed.
    The selection must define a continuos subgraph of the molecule(s) otherwise the coords generation would not be possible,
    at least two atoms (one bond) must be selected for the program to give some meaningfull result"""
    # normalization of selection
    for item in self.selected:
      if item.object_type == 'bond':
        for a in item.atoms:
          if a not in self.selected:
            self.select( [a])

    mols, u = self.selected_to_unique_top_levels()
    for mol in mols:
      if isinstance( mol, molecule):
        notselected = Set( mol.atoms) - Set( self.selected)
        selected = Set( mol.atoms) & Set( self.selected)
        # we must check if the selection defines one connected subgraph of the molecule
        # otherwise the coordinate generation will not work
        if len( selected) == 1:
          print "sorry, but the selection must contain at least two atoms (one bond)"
          return
        else:
          sub = mol.get_new_induced_subgraph( selected, mol.vertex_subgraph_to_edge_subgraph( selected))
          subs = [comp for comp in sub.get_connected_components()]
          if len( subs) != 1:
            print "sorry, but the selection must define a continuos block in the molecule"
            return

        # now we check what has been selected
        side = None
        if len( selected) == 2:
          # if only two atoms are selected we need the information about positioning to guess
          # how to mirror the molecule at the end
          atom1, atom2 = selected
          side = sum( [geometry.on_which_side_is_point( (atom1.x, atom1.y, atom2.x, atom2.y), (a.x,a.y)) for a in notselected])
          
        for a in notselected:
          a.x = None
          a.y = None
          
        oasa.coords_generator.calculate_coords( mol, force=0, bond_length=-1)

        if len( selected) == 2:
          side2 = sum( [geometry.on_which_side_is_point( (atom1.x, atom1.y, atom2.x, atom2.y), (a.x,a.y)) for a in notselected])
          if side * side2 < 0:
            x1, y1, x2, y2 = (atom1.x, atom1.y, atom2.x, atom2.y)
            centerx = ( x1 + x2) / 2
            centery = ( y1 + y2) / 2
            angle0 = geometry.clockwise_angle_from_east( x2 - x1, y2 - y1)
            if angle0 >= math.pi :
              angle0 = angle0 - math.pi
            tr = transform()
            tr.set_move( -centerx, -centery)
            tr.set_rotation( -angle0)
            tr.set_scaling_xy( 1, -1)
            tr.set_rotation( angle0)
            tr.set_move(centerx, centery)

            mol.transform( tr)

      mol.redraw( reposition_double=1)
      self.start_new_undo_record()
