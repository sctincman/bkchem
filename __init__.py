

## import sys

## sys.modules['bkchem'] = bkchem


import sys
import os

sys.path.insert( 0, os.path.abspath('./bkchem/bkchem'))

from bkchem import bkchem


