#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2003, 2004  Beda Kosata <beda@zirael.org>

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


"""This file stores the oldest parents of used classes which are used to provide
mostly the desired meta_behaviour"""


import misc



class simple_parent( object):
  """this class only gives reasonable default values to meta attributes"""
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
  meta__undo_2d_copy = ()
  meta__undo_children_to_record = ()


  def __init__( self):
    pass




class id_enabled( simple_parent):
  """the basic parent that has something to do with the paper, it provides id support"""

  def __init__( self, paper):
    simple_parent.__init__( self)
    self.paper = paper

  def generate_id( self):
    self.id = self._generate_id()


  def _generate_id( self):
    return self.paper.id_manager.generate_id( prefix=self.object_type)

  # id
  def __get_id( self):
    try:
      return self.__id
    except AttributeError:
      self.__id = self._generate_id()
    return self.__id

  def __set_id( self, id):
    self.paper.id_manager.register_id( self, id)
    self.__id = id

  id = property( __get_id, __set_id)
  

  


class meta_enabled( id_enabled):
  """class that has usefull behaviour implemented according to meta infomation"""

  meta__used_standard_values = []

  def __init__( self, paper):
    id_enabled.__init__( self, paper)
    if self.paper:
      self.read_standard_values()

  def read_standard_values( self, old_standard=None):
    """if old_standard is given the recent value is read from standard
    only if it differs from the old one - used for 'inteligent' changes of
    standard properties of existing drawing"""
    for i in self.meta__used_standard_values:
      if old_standard and (self.paper.standard.__dict__[i] == old_standard.__dict__[i]):
        continue
      else:
	# properties
        is_prop = 0
        for p in self.__class__.mro():
          if i in p.__dict__:
            p.__dict__[i].fset( self, self.paper.standard.__dict__[i])
            is_prop = 1
            break
        if not is_prop:
          self.__dict__[i] = self.paper.standard.__dict__[i]








class drawable( simple_parent):
  """basic class for all drawable type - sets the dirty property and the
  move, draw and redraw methods"""

  def __init__( self):
    simple_parent.__init__( self)
    self.dirty = 0


  # public properties

  # dirty
  def __get_dirty( self):
    return self.__dirty

  def __set_dirty( self, dirty):
    self.__dirty = dirty

  dirty = property( __get_dirty, __set_dirty)

  
  # public methods
  def move( self, dx, dy):
    pass

  def draw( self):
    pass

  def redraw( self):
    pass






class point_drawable( drawable):
  """this is a specialized drawable that is of point nature - that is has x,y coords
  that define its position"""

  meta__undo_properties = ("x","y")

  def __init__( self):
    drawable.__init__( self)
    self.x = 0
    self.y = 0

  # public properties

  # x
  def __get_x( self):
    return self.__x

  def __set_x( self, x):
    self.__x = x
    self.dirty = 1

  x = property( __get_x, __set_x)

  # y
  def __get_y( self):
    return self.__y

  def __set_y( self, y):
    self.__y = y
    self.dirty = 1

  y = property( __get_y, __set_y)






class with_line( simple_parent):

  meta__undo_properties = ("line_width",)
  
  # line_width
  def __get_line_width( self):
    return self.__line_width

  def __set_line_width( self, line_width):
    self.__line_width = line_width
    self.dirty = 1

  line_width = property( __get_line_width, __set_line_width)
  





class line_colored( simple_parent):
  """parent for objects having line shape and thus defining only one color -
  the line_color"""

  meta__undo_properties = ("line_color",)
  

  def __init__( self):
    simple_parent.__init__( self)
    self.line_color = '#000'

  # public properties

  # line_color
  def __get_line_color( self):
    return self.__line_color

  def __set_line_color( self, line_color):
    self.__line_color = line_color
    self.dirty = 1

  line_color = property( __get_line_color, __set_line_color)




  


class area_colored( line_colored):

  meta__undo_properties = line_colored.meta__undo_properties + \
                          ("area_color",)
  
  def __init__( self):
    line_colored.__init__( self)
    self.area_color = '#ffffff'

  # public properties

  # area_color
  def __get_area_color( self):
    return self.__area_color

  def __set_area_color( self, area_color):
    self.__area_color = area_color
    self.dirty = 1

  area_color = property( __get_area_color, __set_area_color)








class text_like( simple_parent):
  """for text like objects needing font_size and font_family properties"""

  meta__undo_properties = ("font_size", "font_family", "xml_text")


  def __init__( self):
    simple_parent.__init__( self)
    self.xml_text = ''
    self.font_size = 10
    self.font_family = 'helvetica'


  # font_size
  def __get_font_size( self):
    return self.__font_size

  def __set_font_size( self, font_size):
    self.__font_size = font_size
    self.dirty = 1

  font_size = property( __get_font_size, __set_font_size)


  # font_family
  def __get_font_family( self):
    return self.__font_family

  def __set_font_family( self, font_family):
    self.__font_family = font_family
    self.dirty = 1

  font_family = property( __get_font_family, __set_font_family)


  # xml_text
  def __get_xml_text( self):
    return self.__xml_text

  def __set_xml_text( self, xml_text):
    self.__xml_text = xml_text
    self.dirty = 1

  xml_text = property( __get_xml_text, __set_xml_text)






class interactive( simple_parent):

  def focus( self):
    pass

  def unfocus( self):
    pass

  def select( self):
    pass

  def unselect( self):
    pass




class container( simple_parent):

  # shape_defining_points
  def __get_shape_defining_points( self):
    return []

  shape_defining_points = property( __get_shape_defining_points, None, None,
                                    "should give list of point_drawable instances")


  # children
  def __get_children( self):
    return self.shape_defining_points

  children = property( __get_children, None, None,
                       "should give list of child instances, by default is alias for self.shape_defining_points")

##   # iterator
##   def __iter__( self):
##     return self

##   def next( self):

  



class child( simple_parent):

  # parent
  def __get_parent( self):
    return None

  parent = property( __get_parent, None, None,
                     "should give a container")



class top_level:

  pass

