
import Tkinter
import misc


class context_menu( Tkinter.Menu):

  def __init__( self, app, selected, **kw):
    Tkinter.Menu.__init__( self, app, tearoff=0, **kw)
    self.app = app
    self.selected = selected
    self.changes_made = 0
  
    if len( selected) == 1:
      o = selected[0]
      for attr, vals in configurable[ o.object_type].iteritems():
        if vals:
          casc = Tkinter.Menu( self, tearoff=0)
          self.add_cascade( label=attr, menu=casc)
          for v in vals:
            casc.add_command( label=v, command=misc.lazy_apply( self.callback, (attr,v)))


  def callback( self, command, value):
    for o in self.selected:
      if command in configurable[ o.object_type]:
        for c in o.__class__.mro():
          if command in c.__dict__:
            c.__dict__[ command].fset( o, value)
            o.redraw()
            self.changes_made = 1
            break
    if self.changes_made:
      self.app.paper.start_new_undo_record()
      self.app.paper.add_bindings()



  def close( self, event):
    self.unpost()



  def post( self, x, y):
    Tkinter.Menu.post( self, x, y)
    self.grab_set()



configurable = {'atom': {'show': ('yes','no'),
                         'font_size': (8,10,12,14,16)}
                }
