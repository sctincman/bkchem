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


import os

env_vars = {'template': 'BKCHEM_TEMPLATE_PATH',
            'pixmap': 'BKCHEM_PIXMAP_PATH',
            'image': 'BKCHEM_IMAGE_PATH',
            'plugin': 'BKCHEM_PLUGIN_PATH'}

std_dirs = {'template': '../templates',
            'pixmap': '../pixmaps',
            'image': '../images',
            'plugin': 'plugins'}

def get_path( filename, file_category):
  dir = None
  if file_category in env_vars:
    if os.name in ('posix', 'nt') and os.getenv( env_vars[ file_category]):
      dir = os.getenv( env_vars[ file_category])
      path = os.path.join( dir, filename)
      if not os.path.isfile( path):
        dir = std_dirs[ file_category]
    else:
      dir = std_dirs[ file_category]

  if dir:
    path = os.path.join( dir, filename)
    if os.path.isfile( path):
      return path
  return None


def get_config_filename( name, level="global", mode="r"):
  dir = None
  if level == "global":
    if os.name in ('posix', 'nt'):
      dir = os.getenv( 'BKCHEM_MODULE_PATH') or '../'
  elif level == "local":
    if os.name in ('posix', 'nt'):
      dir = os.getenv( 'BKCHEM_MODULE_PATH') or None
  if level == "personal":
    if os.name in ('posix', 'nt'):
      dir = os.getenv( 'HOME') or '../'
      dir = os.path.join( dir, ".bkchem/")

  if dir:
    if mode == "w":
      if not os.path.isdir( dir):
        try:
          os.mkdir( dir)
        except:
          return None
      if os.access( dir, os.W_OK):
        return os.path.join( dir, name)
      else:
        return os.path.join( dir, name)
    elif mode == "r":
      path = os.path.join( dir, name)
      if os.access( path, os.R_OK):
        return path
      else:
        return None
  return None


def get_local_templates():
  dir = os.getenv( 'HOME') or None
  if dir:
    dir = os.path.join( dir, '.bkchem/templates')
    if os.path.isdir( dir):
      return [d for d in os.listdir( dir) if os.path.splitext( d)[1] in ('.cdml', '.cdgz', '.svg', '.svgz')] 
  return []


def get_module_path():
  dir = os.getenv( 'BKCHEM_MODULE_PATH') or './'
  return dir



