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

import xml.dom.minidom as dom
import dom_extensions as dom_ext
import os_support
import os
import debug

from singleton_store import Store



class plugin_manager( object):

  def __init__( self):
    self.plugins = {}
    self.descriptions = {}

  def get_available_plugins( self):
    dir = os_support.get_bkchem_private_dir()
    dir = os.path.join( dir, 'plugins')
    if not os.path.isdir( dir):
      return []
    for name in os.listdir( dir):
      base, ext = os.path.splitext( name)
      if ext == ".xml":
        #try:
        self.read_plugin_file( dir, name)
        #except:
        #  debug.log( "could not load plugin file", name)

    return self.plugins.keys()



  def read_plugin_file( self, dir, name):
    doc = dom.parse( os.path.join( dir, name))
    sources = dom_ext.simpleXPathSearch( doc, "/plugin/source")
    if sources:
      source = sources[0]
      files = dom_ext.simpleXPathSearch( source, "file")
      names = dom_ext.simpleXPathSearch( source, "menu-text")
      descs = dom_ext.simpleXPathSearch( source, "/plugin/meta/description")
      if files and names:
        file = dom_ext.getAllTextFromElement( files[0])
        if not os.path.isabs( file):
          file = os.path.normpath( os.path.join( dir, file))
        name = dom_ext.getAllTextFromElement( names[0])

        self.plugins[ name] = file
        self.descriptions[ name] = descs and dom_ext.getAllTextFromElement( descs[0]) or ''



  def run_plugin( self, name):
    filename = self.plugins[ name]

    globals = {'app': Store.app}
    execfile( filename, globals)

    if 'exc' in globals:
      print globals['exc']

##     f = file( filename, 'r')

##     try:
##       for line in f.xreadlines():
##         print line
##         try:
##           eval( line)
##         except SyntaxError:
##           exec line
##     finally:
##       f.close()



  def get_names( self):
    return self.plugins.keys()
    

  def get_description( self, name):
    return self.descriptions.get( name, '')
      
  
