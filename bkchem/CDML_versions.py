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
# Last edited: $Date: 2003/09/26 18:14:55 $
#
#--------------------------------------------------------------------------

"""support for backward compatible CDML reading"""

import dom_extensions as dom_ext      


class CDML_transformer_06_07:

  output_version = '0.7'
  input_version = '0.6'

  def tranform_dom( self, dom):
    for b in dom.getElementsByTagName( 'bond'):
      type = b.getAttribute( 'type')
      if type == 'forth':
        b.setAttribute( 'type', 'up')


class CDML_transformer_07_08:

  output_version = '0.8'
  input_version = '0.7'

  def tranform_dom( self, dom):
    types = { 'single': 's', 'double': 'd', 'triple': 't', 'up': 'w', 'back': 'h'}
    for b in dom.getElementsByTagName( 'bond'):
      type = b.getAttribute( 'type')
      if type in types:
        t = types[ type]
        b.setAttribute( 'type', t)

class CDML_transformer_08_09:

  output_version = '0.9'
  input_version = '0.8'

  def tranform_dom( self, dom):
    pass


class CDML_transformer_09_10:

  output_version = '0.10'
  input_version = '0.9'

  def tranform_dom( self, dom):
    if dom.nodeName == 'cdml':
      cdml = dom
    else:
      cdml = dom.getElementsByTagName('cdml')[0]
    if cdml.getElementsByTagName( 'standard'):
      return
    standard = dom_ext.elementUnder( cdml, 'standard',
                                     (('font_family','helvetica'),
                                      ('font_size','12'),
                                      ('line_width','1.0px')))
    dom_ext.elementUnder( standard, 'bond',
                          (('double-ratio','1'),
                           ('length','1.0cm'),
                           ('width','6.0px'),
                           ('wedge-width','2.0px')))
    dom_ext.elementUnder( standard, 'arrow',
                          (('length','1.6cm'),))



# LIST OF AVAILABLE TRANSFORMERS

transformers = { '0.6': CDML_transformer_06_07,
                 '0.7': CDML_transformer_07_08,
                 '0.8': CDML_transformer_08_09,
                 '0.9': CDML_transformer_09_10}


# TRANSFORMING FUNCTION

def transform_dom_to_version( dom, version):
  """does inplace transformation of the dom tree to requested version, returns 1 on success"""
  in_ver = dom.getAttribute( 'version')
  if not in_ver:
    return 0
  out_ver = version
  trans = []
  while in_ver != out_ver:
    if in_ver in transformers:
      trans.append( transformers[ in_ver]())
      in_ver = trans[-1].output_version
    else:
      return 0
  for tr in trans:
    tr.tranform_dom( dom)
  return 1
