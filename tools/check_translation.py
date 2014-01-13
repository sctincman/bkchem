
from __future__ import print_function

import os

locale_dir = "../locale"

for lang in os.listdir( locale_dir):
    print("-- language:", lang)
    filename = os.path.join( locale_dir, lang, 'BKChem.po')
    try:
        f = open(filename, 'r')
    except:
        print("Could not open the file %s" % filename)
        continue
    msgid = ""
    msgstr = ""
    i = 0
    with f:
        for line in f:
            if line.startswith( "msgid"):
                msgid = line
            elif line.startswith( "msgstr"):
                msgstr = line
                if msgstr != 'msgstr ""\n' and msgid.count("%") != msgstr.count("%"):
                    # if msgstr == 'msgstr ""\n', it is not translated
                    print("!! line %d: %s vs. %s" % (i, msgid, msgstr))
            i += 1

