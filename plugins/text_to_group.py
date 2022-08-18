from __future__ import print_function

from group import group
from textatom import textatom
from singleton_store import Store



# if nothing is selected the use all
selected = App.paper.selected or (j for i in [m.vertices for m in App.paper.molecules]
                                        for j in i)
textatoms = [a for a in selected if isinstance(a, textatom)]

i = 0
for atom in textatoms:
    val = atom.occupied_valency
    gr = atom.molecule.create_vertex(vertex_class=group)
    text = atom.symbol
    print(text)
    if gr.set_name(text, occupied_valency=val):
        i += 1
        atom.copy_settings(gr)
        atom.molecule.replace_vertices(atom, gr)
        atom.delete()
        gr.draw()

Store.log(_("%d textatoms were converted to groups") % i)

App.paper.start_new_undo_record()
App.paper.add_bindings()

