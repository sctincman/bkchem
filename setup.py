#! /usr/bin/python

from distutils.core import setup
import glob
import os
import sys

if os.name != 'posix':
  print "Sorry, but install is not available for non-posix OSes, yet"
  sys.exit()

set = setup(
  name = 'bkchem',
  version = '0.7.0',
  description = "BKchem is a chemical drawing program written in Python",
  author = "Beda Kosata",
  author_email = "beda@zirael.org",
  url = "http://savannah.nongnu.org/projects/bkchem",
  license = "GNU GPL",
  platforms = ["Unix", "Windows", "hopefully other OSes able to run Python"],
  long_description = "BKchem is a chemical drawing program written in Python",
  
  packages=[ 'bkchem', 'bkchem/plugins', 'bkchem/oasa', 'bkchem/oasa/oasa', 'bkchem/oasa/oasa/graph'],

  data_files=[ ('share/bkchem/templates', glob.glob( 'templates/*.cdml')+['templates/oo_manifest.xml']),
               ('share/bkchem/images', ['images/logo.ppm']),
               ('share/bkchem/pixmaps', glob.glob( 'pixmaps/*.gif')),
               ('share/bkchem/dtd', glob.glob( 'dtd/*.dtd') + glob.glob( 'dtd/*.xsd')),
               ('share/doc/bkchem', glob.glob( 'doc/*.xml') + ['README', 'RELEASE', 'INSTALL', 'INSTALL.binary', 'progress.log']),
               ('share/doc/bkchem/ps', glob.glob( 'doc/ps/*')),
               ('share/doc/bkchem/pdf', glob.glob( 'doc/pdf/*')),
               ('share/doc/bkchem/html', glob.glob( 'doc/html/*')),
               ('share/locale/cs/LC_MESSAGES', ['locale/cs/LC_MESSAGES/BKchem.mo']),
               ('share/locale/pl/LC_MESSAGES', ['locale/pl/LC_MESSAGES/BKchem.mo']),
               ('share/locale/fr/LC_MESSAGES', ['locale/fr/LC_MESSAGES/BKchem.mo'])
               ]
  )



if len( sys.argv) > 1 and sys.argv[1] == 'install' and '--help' not in sys.argv:
  data_dir = set.command_obj['install'].install_data
  py_dir = set.command_obj['install'].install_lib
  bin_dir = set.command_obj['install'].install_scripts

  try:
    file = open( os.path.join( bin_dir, 'bkchem'), 'w')
  except:
    print "ERROR: couldn't open the file %s for write" %  os.path.join( bin_dir, 'bkchem')
    sys.exit()
  file.write( "#!/bin/sh\n")
  file.write( "export BKCHEM_MODULE_PATH=%s\n" % os.path.join( py_dir, "bkchem"))
  file.write( "export BKCHEM_TEMPLATE_PATH=%s\n" % os.path.join( data_dir, "share/bkchem/templates"))
  file.write( "export BKCHEM_PIXMAP_PATH=%s\n" % os.path.join( data_dir, "share/bkchem/pixmaps"))
  file.write( "export BKCHEM_IMAGE_PATH=%s\n" % os.path.join( data_dir, "share/bkchem/images"))
  file.write( "export BKCHEM_PLUGIN_PATH=%s\n" % os.path.join( py_dir, "bkchem/plugins"))
  file.write( "python %s $1\n" % os.path.join( py_dir, "bkchem", "bkchem.py"))
  file.close()
  print "file %s created" % os.path.join( bin_dir, 'bkchem')
  try:
    os.chmod( os.path.join( bin_dir, 'bkchem'), 5+5*8+7*8*8)
  except:
    print "failed to make %s executable" % os.path.join( bin_dir, 'bkchem')
    sys.exit()
  print "file %s made executable" % os.path.join( bin_dir, 'bkchem')
  

