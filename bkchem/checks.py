#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2005 Beda Kosata <beda@zirael.org>

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


"""this module contains functions used for various checks and maintanence
throughout bkchem - mainly from paper and modules"""


from sets import Set
import interactors


def check_linear_fragments( paper):
  """checks the state of linear fragments present on the paper and resets their appearance"""

  for mol in paper.molecules:
    to_del = Set()
    for f in mol.fragments:
      if f.type == "linear_form":
        if f.edges - mol.edges or f.vertices - Set( mol.vertices):
          # something from the fragment was deleted
          es = f.edges & mol.edges
          vs = f.vertices & Set( mol.vertices)
          if es and mol.defines_connected_subgraph_e( es):
            f.edges = es
            f.vertices = Set()
          elif vs and mol.defines_connected_subgraph_v( vs):
            f.edges = Set()
            f.vertices = vs
          else:
            to_del.add( f)
            continue
          
        # the fragment should be redrawn
        vs = mol.edge_subgraph_to_vertex_subgraph( f.edges)
        interactors.atoms_to_linear_fragment( mol, vs)

    for f in to_del:
      mol.delete_fragment( f)
