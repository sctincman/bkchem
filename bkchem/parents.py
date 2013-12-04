#--------------------------------------------------------------------------
#     This file is part of BKChem - a chemical drawing program
#     Copyright (C) 2002-2009 Beda Kosata <beda@zirael.org>

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

"""This file stores the oldest parents of used classes.

Used to provide mostly the desired meta_behaviour.
"""

import xml.dom.minidom as dom

import misc
import ftext
import dom_extensions

from singleton_store import Store



class simple_parent(object):
  """This class only gives reasonable default values to meta attributes.

  """
  object_type = "object"
  # if a class is a container in paper meaning (is not part of bigger structure)
  meta__is_container = 0

  # class is not made up from smaller parts that define the structure (points etc.)
  # if non zero then specifies the number of coordinate pairs
  meta__has_simple_coords = 1
  # undo related
  meta__undo_fake = () # fakes serve only to force redraw in some cases however do not perform any undo
  meta__undo_simple = ()
  meta__undo_properties = ()
  meta__undo_copy = ()
  meta__undo_children_to_record = ()


  def __init__( self):
    pass


  def copy_settings( self, other):
    pass



class id_enabled(simple_parent):
  """Basic parent that has something to do with the paper, provides id support.

  """
  def __init__( self):
    simple_parent.__init__( self)


  def generate_id( self):
    self.id = self._generate_id()


  def _generate_id( self):
    return Store.id_manager.generate_and_register_id( self, prefix=self.object_type)


  @property
  def id(self):
    try:
      return self.__id
    except AttributeError:
      self.__id = self._generate_id()
    return self.__id


  @id.setter
  def id(self, id):
    if Store.id_manager.is_registered_object( self):
      Store.id_manager.unregister_object( self)
    Store.id_manager.register_id( self, id)
    self.__id = id


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it."""
    pass



class meta_enabled(id_enabled):
  """Class that has usefull behaviour implemented according to meta infomation.

  """
  meta__used_standard_values = []

  def __init__( self, standard=None):
    id_enabled.__init__( self)
    if standard:
      self.read_standard_values( standard)


  def read_standard_values(self, standard, old_standard=None):
    """Intelligent changes of standard properties of existing drawing.

    If old_standard is given the recent value is read from standard
    only if it differs from the old one.
    """
    for i in self.meta__used_standard_values:
      if old_standard and (standard.__dict__[i] == old_standard.__dict__[i]):
        continue
      else:
	# properties
        is_prop = 0
        for p in self.__class__.mro():
          if i in p.__dict__:
            p.__dict__[i].fset( self, standard.__dict__[i])
            is_prop = 1
            break
        if not is_prop:
          self.__dict__[i] = standard.__dict__[i]



class drawable(simple_parent):
  """Basic class for all drawable type.

  Sets the dirty property and the move, draw and redraw methods.
  """
  def __init__( self):
    simple_parent.__init__( self)
    self.dirty = 0


  @property
  def dirty(self):
    return self.__dirty


  @dirty.setter
  def dirty(self, dirty):
    self.__dirty = dirty


  # public methods
  def move( self, dx, dy):
    pass


  def draw( self):
    pass


  def redraw( self):
    pass



class point_drawable(drawable):
  """Specialized drawable that is of point nature.

  Has x, y coordinates that define its position.
  """
  meta__undo_properties = ("x","y")

  def __init__( self):
    drawable.__init__( self)
    self.x = 0
    self.y = 0


  @property
  def x(self):
    return self.__x


  @x.setter
  def x(self, x):
    self.__x = x
    self.dirty = 1


  @property
  def y(self):
    return self.__y


  @y.setter
  def y(self, y):
    self.__y = y
    self.dirty = 1


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    drawable.copy_settings(self, other)
    other.x = self.x
    other.y = self.y



class with_line(simple_parent):

  meta__undo_properties = ("line_width",)

  @property
  def line_width(self):
    return self.__line_width


  @line_width.setter
  def line_width(self, line_width):
    self.__line_width = line_width
    self.dirty = 1


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    simple_parent.copy_settings(self, other)
    other.line_width = self.line_width



class line_colored(simple_parent):
  """Parent for objects having line shape and thus defining only one color.

  """
  meta__undo_properties = ("line_color",)

  def __init__( self):
    simple_parent.__init__( self)
    self.line_color = '#000'


  @property
  def line_color(self):
    return self.__line_color


  @line_color.setter
  def line_color(self, line_color):
    self.__line_color = line_color
    self.dirty = 1


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    simple_parent.copy_settings(self, other)
    other.line_color = self.line_color



class area_colored(line_colored):

  meta__undo_properties = line_colored.meta__undo_properties + \
                          ("area_color",)

  def __init__( self):
    line_colored.__init__( self)
    self.area_color = '#ffffff'


  @property
  def area_color(self):
    return self._area_color


  @area_color.setter
  def area_color(self, area_color):
    self._area_color = area_color
    self.dirty = 1


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    line_colored.copy_settings( self, other)
    other.area_color = self.area_color



class with_font(simple_parent):
  """For text like objects needing font_size and font_family properties.

  But not variable text.
  """
  meta__undo_properties = ("font_size", "font_family")

  def __init__( self):
    simple_parent.__init__( self)
    self.font_size = 10
    self.font_family = 'helvetica'


  @property
  def font_size(self):
    return self.__font_size

  @font_size.setter
  def font_size(self, font_size):
    self.__font_size = font_size
    self.dirty = 1


  @property
  def font_family(self):
    return self.__font_family


  @font_family.setter
  def font_family(self, font_family):
    self.__font_family = font_family
    self.dirty = 1


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    simple_parent.copy_settings(self, other)
    other.font_family = self.font_family
    other.font_size = self.font_size



class text_like(with_font):
  """For text like objects with font_size, font_family properties, variable text, xml_ftext.

  """
  def __init__(self):
    with_font.__init__(self)


  @property
  def text(self):
    """Unmarked plain-text representing the object.

    Taken from xml_ftext and the markup is stripped.
    """
    doc = dom.parseString( ftext.ftext.sanitize_text(self.xml_ftext))
    return dom_extensions.getAllTextFromElement(doc)


  @property
  def xml_ftext(self):
    """Text used for rendering using the ftext class.

    """
    return ""



class interactive(simple_parent):

  def focus(self):
    pass


  def unfocus(self):
    pass


  def select(self):
    pass


  def unselect(self):
    pass



class container(simple_parent):

  @property
  def shape_defining_points(self):
    """List of point_drawable instances.

    """
    return []


  @property
  def children(self):
    """List of child instances.

    By default is alias for self.shape_defining_points.
    """
    return self.shape_defining_points



class child(simple_parent):

  @property
  def parent(self):
    """Container.

    """
    return None

  @parent.setter
  def parent(self, par):
    pass


  def copy_settings(self, other):
    """Copy settings of self to other.

    Does not check if other is capable of receiving it.
    """
    simple_parent.copy_settings(self, other)
    other.parent = self.parent



class top_level(object):

  pass



class with_paper(object):

  @property
  def paper(self):
    """Paper that the object is drawn onto.

    """
    return self._paper


  @paper.setter
  def paper(self, paper):
    self._paper = paper



class child_with_paper(child, with_paper):

  @property
  def paper(self):
    """Paper that the object is drawn onto.

    """
    if self.parent:
      return self.parent.paper
    else:
      return None


  @paper.setter
  def paper(self, paper):
    raise KeyError("Trying to set paper in a child - set it in parent instead.")

