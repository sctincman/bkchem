
from __future__ import print_function

import sys

# Check the command line
if len(sys.argv) <= 1:
  print("You have to supply a filename.")
  sys.exit()

# Import bkchem and threading
import threading

from bkchem.bkchem import bkchem

# Application instance
app = bkchem.myapp

# Set batch mode = 1 to suppress some interactive warnings,
# questions and mouse events
app.in_batch_mode = 1

# Start the application in a separate thread to be able to manipulate it
t = threading.Thread(target=app.mainloop, name='app')
t.setDaemon(1)
t.start()


# The manipulation code follows

# Load the file
app.load_CDML(sys.argv[1])

# Take all molecules from the current paper, find all the double bonds,
# change their color to red
for mol in app.paper.molecules:
  for bond in mol.bonds:
    if bond.order == 2:
      bond.line_color = "#aa0000"
      bond.redraw()

# Save the result and quit
app.save_CDML()
app.destroy()

