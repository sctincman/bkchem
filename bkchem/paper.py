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

"""BKpaper - the main drawing part for BKchem resides here"""

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
import modes
import dom_extensions
import xml.dom.minidom as dom
import operator
from warnings import warn
import undo
import math
import xml_writer
import periodic_table as PT
import Pmw
import graphics
import types
import os_support
import copy

class BKpaper( Canvas):

  def __init__( self, master = None, app = None, **kw):
    Canvas.__init__( self, master, kw)
    
    self.app = app
    self.clipboard = None

    self.standard = self.get_personal_standard()
    self.molecules = []     # list of molecules present in the drawing
    self.submode = None
    self.selected = []    # selected item
    self.__in = 1
    self.arrows = []
    self.pluses = []
    self.texts = []
    self.vectors = []
    self._id_2_object = {}
    self.stack = []

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
    self.bind( "<Motion>", self._move)
    self.bind( "<Leave>", self._leave)
#    self.bind( "<Enter>", self._enter) # enable this and you will get mysterious error
                                        # when adding 'N' to an atom and then hitting "Return" - the app will immediately close
                                        # I found it to be caused by Pmw mechanism of catching errors; PmwBase.py:1667 gets called 

    self.set_viewport()

    # template manager
    self.tm = template_manager( self)
    self.tm.add_template_from_CDML( "templates.cdml")
    #self.tm.add_template_from_CDML( "../templates/groups.cdml")
    
    # groups manager (for group expansions)
    self.gm = template_manager( self)
    self.gm.add_template_from_CDML( "groups.cdml")
    self.gm.add_template_from_CDML( "groups2.cdml")
    
    self.modes = { 'draw': modes.draw_mode( self),
                   'edit': modes.edit_mode( self),
                   'arrow': modes.arrow_mode( self),
                   'plus': modes.plus_mode( self),
                   'template': modes.template_mode( self),
                   'text': modes.text_mode( self),
                   'rotate': modes.rotate_mode( self),
                   'bondalign': modes.bond_align_mode( self),
                   'name': modes.name_mode( self),
                   'vector': modes.vector_mode( self),
                   'mark': modes.mark_mode( self)}
    self.modes_sort = [ 'edit', 'draw', 'template', 'text', 'arrow', 'plus', 'rotate', 'bondalign', 'name', 'vector', 'mark']
    self.mode = 'draw' # this is normaly not a string but it makes things easier on startup
    self.um = undo.undo_manager( self)  # undo manager

    # paper sizes etc.
    self._paper_properties = {}
    self.set_paper_properties()

    #
    self.changes_made = 0



  def add_bindings( self):
    self.lower( self.background)
    [o.lift() for o in self.stack]
    self.tag_bind( 'atom', '<Enter>', self.enter_item)
    self.tag_bind( 'bond', '<Enter>', self.enter_item)
    self.tag_bind( 'atom', '<Leave>', self.leave_item)
    self.tag_bind( 'bond', '<Leave>', self.leave_item)
    self.tag_bind( 'arrow', "<Enter>", self.enter_item)
    self.tag_bind( 'arrow', "<Leave>", self.leave_item)
    self.tag_bind( 'point', "<Enter>", self.enter_item)
    self.tag_bind( 'point', "<Leave>", self.leave_item)
    self.tag_bind( 'plus', "<Enter>", self.enter_item)
    self.tag_bind( 'plus', "<Leave>", self.leave_item)
    self.tag_bind( 'text', "<Enter>", self.enter_item)
    self.tag_bind( 'text', "<Leave>", self.leave_item)
    self.tag_bind( 'vector', "<Enter>", self.enter_item)
    self.tag_bind( 'vector', "<Leave>", self.leave_item)
    self.tag_bind( 'helper_rect', "<Enter>", self.enter_item)
    self.tag_bind( 'helper_rect', "<Leave>", self.leave_item)
    
  ## event bound methods

  ## overall
  
  def _s_pressed1( self, event):
    "button 1 with shift"
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_down( event, modifiers=['shift'])

  def _n_pressed1( self, event):
    "button 1 without anything"
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_down( event)

  def _release1( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_up( event)
    
  def _drag1( self, event):
    # unfortunately we need to simulate "enter" and "leave" in this way because
    # when B1 is down such events does not occur
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_drag( event) 
    b = self.find_enclosed( event.x-2, event.y-2, event.x+2, event.y+2)
    if b:
      a = self.id_to_object( b[0])
    else:
      a = None
    if a:
      if not self.__in:
        self.__in = a
        self.mode.enter_object( self.__in, event)
      elif a != self.__in:
        self.__in = a
        self.mode.leave_object( event)
        self.mode.enter_object( self.__in, event)
    else:
      if self.__in:
        self.__in = None
        self.mode.leave_object( event)

  def _n_pressed3( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_down3( event, modifiers=[])

  def _move( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    self.mode.mouse_move( event)

  def _enter( self, event):
    self.mode.clean_key_query()

  def _leave( self, event):
    self.mode.clean_key_query()

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
      self.mode.enter_object( self.__in, event)

  def leave_item( self, event):
    event.x = self.canvasx( event.x)
    event.y = self.canvasy( event.y)
    if self.__in:
      self.__in = None
      self.mode.leave_object( event)

  def key_pressed( self, event):
    self.mode.key_pressed( event)

  def key_released( self, event):
    self.mode.key_released( event)

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
    map( self.arrows.remove, to_delete)
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # PLUS
    to_delete = filter( lambda o: o.object_type == 'plus', self.selected)
    map( lambda o: o.delete(), to_delete)
    map( self.pluses.remove, to_delete)
    map( self.stack.remove, to_delete)
    # TEXT
    to_delete = filter( lambda o: o.object_type == 'text', self.selected)
    for t in to_delete:
      t.delete()
      self.texts.remove( t)
      self.stack.remove( t)
    # VECTOR GRAPHICS
    for o in [obj for obj in self.selected if obj.object_type == 'rect' or obj.object_type == 'oval']:
      o.delete()
      self.vectors.remove( o)
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
    map( self.vectors.remove, to_delete)
    map( self.stack.remove, to_delete)
    [o.delete() for o in to_delete]
    # BOND AND ATOM
    bonds = [o for o in self.selected if o.object_type == 'bond']
    atoms = [o for o in self.selected if o.object_type == 'atom']
    deleted, new, mols_to_delete = [], [], []
    for mol in self.molecules:
      items = [o for o in bonds+atoms if o.molecule == mol]
      now_deleted, new_mols = mol.delete_items( items)
      deleted += now_deleted
      new += new_mols
      if new_mols:
        mols_to_delete.append( mol)
    if new:
      map( self.molecules.remove, mols_to_delete)
      map( self.stack.remove, mols_to_delete)
      self.molecules.extend( new)
      self.stack.extend( new)
    empty_mols = filter( lambda o: o.is_empty(), self.molecules)
    [self.stack.remove( o) for o in empty_mols]
    [self.molecules.remove( o) for o in empty_mols]
    if self.selected:
      self.start_new_undo_record()
    self.selected = []
    #return deleted
      
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
        a1, a2 = b.get_atoms()
        if (a1 in s_atoms) or (a2 in s_atoms):
          a.append( b)
    # if bond is also selected then it moves with and should not be updated
    return [b for b in a if b not in self.selected]

  def atoms_to_update( self):
    a = []
    for o in self.selected:
      if o.object_type == 'bond':
        a.extend( o.get_atoms())
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
    import CDML_versions
    success = CDML_versions.transform_dom_to_version( CDML, data.current_CDML_version)
    if not success:
      if not tkMessageBox.askyesno( _('Proceed'),
                                    _('''This CDML document does not seem to have supported version.
                                    \n Do you want to proceed reading this document?'''),
                                    default = 'yes'):
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
        o.draw()
    # now check if the old standard differs
    if new_standard and old_standard != self.standard:
      if not tkMessageBox.askyesno( _('Replace standard values'),
                                    data.standards_differ_text,
                                    default = 'yes'):
        self.standard = old_standard
    # finish
    self.add_bindings()
    self.um.start_new_record()

  def get_package( self):
    doc = dom.Document()
    root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', data.current_CDML_version),
                                                                   ( 'xmlns', data.cdml_namespace)))
    info = dom_extensions.elementUnder( root, 'info')
    dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKchem', attributes = (('version',data.current_BKchem_version),))
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
    return doc
    
  def clean_paper( self):
    "removes all items from paper and deletes them from molecules and items"
    self.delete( 'all')
    self.background = None
    self.unselect_all()
    del self.arrows[:]
    del self.pluses[:]
    del self._id_2_object
    self._id_2_object = {}
    del self.molecules[:]
    del self.texts[:]
    del self.vectors[:]
    del self.stack[:]
    self.um.clean()
    self.changes_made = 0
    
  def del_container( self, container):
    container.delete()
    if container.object_type == 'molecule':
      self.molecules.remove( container)
    elif container.object_type == 'arrow':
      self.arrows.remove( container)
    elif container.object_type == 'plus':
      self.pluses.remove( container)
    elif container.object_type == 'text':
      self.texts.remove( container)

  def handle_overlap( self):
    "puts overlaping molecules together to one and then calles handle_overlap(a1, a2) for that molecule"
    overlap = []
    for a in self.find_withtag('atom'):
      x, y = self.id_to_object( a).get_xy()
      for b in self.find_overlapping( x-2, y-2, x+2, y+2):
        if (a != b) and ( 'atom' in self.gettags( b)):
          a1 = self.id_to_object( a)
          a2 = self.id_to_object( b)
          if ( abs( a1.get_x() - a2.get_x()) < 2) and ( abs( a1.get_y() - a2.get_y()) < 2): 
            if (not [a2,a1] in overlap) and a1.z == a2.z:
              overlap.append( [a1,a2])
    if overlap:
      mols = misc.filter_unique( map( lambda a: map( lambda b: b.molecule, a), overlap))
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
          self.molecules.remove( mol2)
          self.stack.remove( mol2)
        else:
          mol.handle_overlap()
      deleted = reduce( operator.add, [mol.handle_overlap() for mol in misc.difference( a_eatenby_b2, a_eatenby_b1)], [])
      self.selected = misc.difference( self.selected, deleted)
      self.add_bindings()
      self.signal_to_app( _('concatenated overlaping atoms'))
      
  def set_name_to_selected( self, name, interpret=1):
    """sets name to all selected atoms and texts,
    also records it in an undo !!!"""
    for item in self.selected[:]:
      if item.object_type == 'atom':
        if name:
          item.set_name( name, interpret=interpret)
          item.decide_pos()
          item.redraw()
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
      warn( 'trying to unregister not registered id', UserWarning, 2)

  def id_to_object( self, id):
    try:
      return self._id_2_object[ id]
    except KeyError:
      return None

  def is_registered_object( self, o):
    """has this object a registered id?"""
    return o in self._id_2_object.values()

  def switch_to_mode( self, name):
    # this is necessary because at first the mode is a string
    if type( self.mode) != types.StringType:
      self.mode.cleanup()
    self.mode = self.modes[ name]


  def switch_to_submode( self, name):
    self.mode.set_submode( name)

  def new_molecule( self):
    mol = molecule( self)
    self.molecules.append( mol)
    self.stack.append( mol)
    return mol

  def add_molecule( self, mol):
    self.molecules.append( mol)
    self.stack.append( mol)

  def new_arrow( self, points=[], spline=0):
    arr = classes.arrow( self, points=points, spline=spline)
    self.arrows.append( arr)
    self.stack.append( arr)
    arr.draw()
    return arr

  def new_plus( self, x, y):
    pl = classes.plus( self, xy = (x,y))
    self.pluses.append( pl)
    self.stack.append( pl)
    pl.draw()
    return pl

  def new_text( self, x, y, text=''):
    txt = classes.text( self, xy=(x,y), text=text)
    self.texts.append( txt)
    self.stack.append( txt)
    return txt

  def new_rect( self, coords):
    rec = graphics.rect( self, coords=coords)
    self.vectors.append( rec)
    self.stack.append( rec)
    return rec

  def new_oval( self, coords):
    ovl = graphics.oval( self, coords=coords)
    self.vectors.append( ovl)
    self.stack.append( ovl)
    return ovl

  def new_square( self, coords):
    rec = graphics.square( self, coords=coords)
    self.vectors.append( rec)
    self.stack.append( rec)
    return rec

  def new_circle( self, coords):
    ovl = graphics.circle( self, coords=coords)
    self.vectors.append( ovl)
    self.stack.append( ovl)
    return ovl

  def new_polygon( self, coords):
    p = graphics.polygon( self, coords=coords)
    self.stack.append( p)
    self.vectors.append( p)
    return p

  def list_bbox( self, items):
    """extension of Canvas.bbox to provide support for lists of items"""
    self.dtag( 'bbox', 'bbox') # just to be sure
    for i in items:
      self.addtag_withtag( 'bbox', i)
    ret = self.bbox( 'bbox')
    self.dtag( 'bbox', 'bbox')
    return ret

  def selected_to_clipboard( self, delete_afterwards=0):
    if self.selected:
      cp, unique = self.selected_to_unique_containers()
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
      self.clipboard = dom_extensions.elementUnder( clipboard_doc, 'clipboard')
      for o in cp:
        self.clipboard.appendChild( o.get_package( clipboard_doc))
      self.clipboard_pos = xy
      if delete_afterwards:
        [self.del_container(o) for o in cp]
        self.signal_to_app( _("killed %s object(s) to clipboard") % str( len( cp)))
      else:
        self.signal_to_app( _("copied %s object(s) to clipboard") % str( len( cp)))
      self.start_new_undo_record()

  def paste_clipboard( self, xy):
    """pastes items from clipboard to position xy"""
    if self.clipboard:
      new = []
      self.unselect_all()
      if xy:
        dx = xy[0] - self.clipboard_pos[0]
        dy = xy[1] - self.clipboard_pos[1]
      else:
        dx, dy = 20, 20
      for p in self.clipboard.childNodes:
        o = self.add_object_from_package( p)
        o.draw()
        o.move( dx, dy)
        if o.object_type == 'molecule':
          self.select( o)
        elif o.object_type == 'arrow':
          self.select( o.points)
        else:
          self.select( [o])
      self.add_bindings()
      #self.select( new)
      self.signal_to_app( _("pasted from clipboard"))
      self.handle_overlap()
      self.start_new_undo_record()
      
  def add_object_from_package( self, package):
    if package.nodeName == 'molecule':
      o = molecule( self, package=package)
      self.molecules.append( o)
    elif package.nodeName == 'arrow':
      o = classes.arrow( self, package=package)
      self.arrows.append( o)
    elif package.nodeName == 'plus':
      o = classes.plus( self, package=package)
      self.pluses.append( o)
    elif package.nodeName == 'text':
      o = classes.text( self, package=package)
      self.texts.append( o)
    elif package.nodeName == 'rect':
      o = graphics.rect( self, package=package)
      self.vectors.append( o)
    elif package.nodeName == 'oval':
      o = graphics.oval( self, package=package)
      self.vectors.append( o)
    elif package.nodeName == 'square':
      o = graphics.square( self, package=package)
      self.vectors.append( o)
    elif package.nodeName == 'circle':
      o = graphics.circle( self, package=package)
      self.vectors.append( o)
    elif package.nodeName == 'polygon':
      o = graphics.polygon( self, package=package)
      self.vectors.append( o)
    else:
      o = None
    if o:
      self.stack.append( o)
    return o
    
  def align_selected( self, mode):
    """aligns selected items according to mode - t=top, b=bottom,
    l=left, r=right, h=horizontal center, v=vertical center"""
    # locate all selected containers, filter them to be unique
    to_align, unique = self.selected_to_unique_containers()
    # check if there is anything to align
    if len( to_align) < 2:
      return None
    bboxes = []
    if not unique:
      # if not unique align is done according to bboxes of containers
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

  def selected_to_unique_containers( self):
    """maps all items in self.selected to their containers (atoms->molecule etc.),
    filters them to be unique and returns tuple of (unique_containers, unique)
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
      self.signal_to_app( _("undo (%d further undos available)") % i)
    else:
      self.signal_to_app( _("no further undo"))
    
  def redo( self):
    self.unselect_all()
    i = self.um.redo()
    self.changes_made = 1
    if i > 0:
      self.signal_to_app( _("redo (%d further redos available)") % i)
    else:
      self.signal_to_app( _("no further redo"))
    
  def scale_selected( self, ratio_x, ratio_y, scale_font=1):
    containers, unique = self.selected_to_unique_containers()
    ratio = math.sqrt( ratio_x*ratio_y) # ratio for operations where x and y can't be distinguished (font size etc.)
    tr = transform()
    tr.set_scaling_xy( ratio_x, ratio_y)
    for o in containers:
      if o.object_type == 'molecule':
        for i in o.atoms_map:
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
    if containers:
      self.add_bindings()
      self.start_new_undo_record()

  def get_all_containers( self):
    return self.molecules + self.arrows + self.pluses + self.texts + self.vectors

  def selected_to_real_clipboard_as_SVG( self):
    """exports selected containers as SVG to system clipboard"""
    cont, unique = self.selected_to_unique_containers()
    exporter = xml_writer.SVG_writer( self)
    exporter.construct_dom_tree( cont)
    self.clipboard_clear()
    self.clipboard_append( exporter.get_nicely_formated_document())
    self.signal_to_app( _("selected containers were exported to clipboard in SVG"))

  def start_new_undo_record( self, name=''):
    if not self.changes_made:
      self.changes_made = 1
    self.um.start_new_record( name=name)

  def display_weight_of_selected( self):
    s_mols = [m for m in self.selected_to_unique_containers()[0] if m.object_type == 'molecule']
    w = 0
    for m in s_mols:
      w += m.get_formula_dict().get_molecular_weight()
    self.app.update_status( str( w))

  def display_info_on_selected( self):
    s_mols = [m for m in self.selected_to_unique_containers()[0] if m.object_type == 'molecule']
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
    s_mols = [m for m in self.selected_to_unique_containers()[0] if m.object_type == 'molecule']
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
      mols = [o for o in self.selected_to_unique_containers()[0] if o.object_type == 'molecule']
      atoms = [o for o in self.selected if (o.object_type == 'atom' and o.type in ('group','chain'))]
      self.unselect_all()
      for mol in mols:
        this_atoms = misc.intersection( atoms, mol.atoms_map)
        mol.expand_groups( atoms = this_atoms)
    else:
      self.unselect_all()
      [m.expand_groups() for m in self.molecules]
    self.add_bindings()
    self.start_new_undo_record()

  def lift_selected_to_top( self):
    os = self.selected_to_unique_containers()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.append( o)
    self.signal_to_app( _("selected items were lifted"))
    self.add_bindings()
    self.start_new_undo_record()

  def lower_selected_to_bottom( self):
    os = self.selected_to_unique_containers()[0]
    for o in os:
      self.stack.remove( o)
      self.stack.insert( 0, o)
    self.signal_to_app( _("selected items were put back"))
    self.add_bindings()
    self.start_new_undo_record()

  def swap_selected_on_stack( self):
    os = self.selected_to_unique_containers()[0]
    indxs = [self.stack.index( o) for o in os]
    indxs.sort()
    for i in range( len( indxs) // 2):
      self.stack[ indxs[i]], self.stack[ indxs[-1-i]] =  self.stack[ indxs[-1-i]], self.stack[ indxs[i]]
    self.signal_to_app( _("selected items were swapped"))
    self.add_bindings()
    self.start_new_undo_record()

  def _open_debug_console( self):
    m = self.mode
    for i in m.__dict__:
      print i, ' : ', m.__dict__[i]


  def any_color_to_rgb_string( self, color):
    r, g, b = map( lambda x: (x < 256 and x) or (x >= 256 and x//256),  self.winfo_rgb( color))
    return "#%02x%02x%02x" % (r,g,b)
  

  def set_paper_properties( self, type=None, orientation=None, x=None, y=None, crop_svg=None, all=None):
    if all:
      self._paper_properties = copy.copy( all)
      return
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
                              
    if not 'background' in self.__dict__ or not self.background:
      self.background = self.create_rectangle( 0, 0, '%dm'%sx, '%dm'%sy, fill='white', outline='black')
    else:
      self.coords( self.background, 0, 0, '%dm'%sx, '%dm'%sy)

    # crop svg
    self._paper_properties['crop_svg'] = crop_svg or self.standard.paper_crop_svg


  def get_paper_property( self, name):
    if name in self._paper_properties:
      return self._paper_properties[ name]
    else:
      return None

    
##   def coords( self, item, *args, **keyargs):
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

  def apply_current_standard( self, objects=[], old_standard=None):
    """if no objects are given all are used, if old_standard is given only the values
    that have changed are applied"""
    self.set_paper_properties()
    objs = objects or self.get_all_containers()
    to_redraw = []
    st = self.standard
    for m in objs:
      if m.object_type == 'molecule':
        for b in m.bonds:
          b.read_standard_values( old_standard=old_standard)
          to_redraw.append( b)
        for a in m.atoms_map:
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
      root = dom_extensions.elementUnder( doc, 'cdml', attributes = (('version', data.current_CDML_version),
                                                                     ( 'xmlns', data.cdml_namespace)))
      info = dom_extensions.elementUnder( root, 'info')
      dom_extensions.textOnlyElementUnder( info, 'author_program', 'BKchem', attributes = (('version',data.current_BKchem_version),))
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
    # locate all selected containers, filter them to be unique
    to_align, unique = self.selected_to_unique_containers()
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
        if o.meta__is_container:
          tr = transform()
          tr.set_move( -x0, 0)
          tr.set_scaling_xy( -1, 1)
          tr.set_move( x0, 0)
          o.transform( tr)
        else:
          print "fuck"
    # horizontal (rotate around x axis)
    if mode == 'horizontal':
      ys = [bboxes[i] for i in range( 1, len( bboxes), 2)]
      y0 = (max( ys) + min( ys)) / 2.0
      for o in to_align:
        if o.meta__is_container:
          tr = transform()
          tr.set_move( 0, -y0)
          tr.set_scaling_xy( 1, -1)
          tr.set_move( 0, y0)
          o.transform( tr)
        else:
          print "fuck"

    self.start_new_undo_record()

  def add_new_container( self, o):
    if o.object_type == 'plus':
      self.paper.pluses.append( o)
    elif o.object_type == 'arrow':
      self.paper.arrows.append( o)
    elif o.object_type == 'text':
      self.paper.texts.append( o)
    elif o.object_type == 'molecule':
      self.paper.molecules.append( o)        
    elif o.object_type in data.vector_graphics_types:
      self.paper.vectors.append( o)

  def flush_first_selected_mol_to_graph_file( self):
    mols, u = self.selected_to_unique_containers()
    for m in mols:
      if m in self.molecules:
        m.flush_graph_to_file()
        return
    
