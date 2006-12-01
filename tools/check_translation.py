
import os

locale_dir = "../locale"

for lang in os.listdir( locale_dir):
    print "-- language:", lang
    filename = os.path.join( locale_dir, lang, 'BKchem.po')
    try:
        f = file( filename, 'r')
    except:
        print "I could not open the file %s" % filename
        continue
    msgid = ""
    msgstr = ""
    i = 0
    for line in f:
        if line.startswith( "msgid"):
            msgid = line
        elif line.startswith( "msgstr"):
            msgstr = line
            if msgstr != 'msgstr ""\n' and msgid.count("%") != msgstr.count("%"):
                # if msgstr == 'msgstr ""\n', it is not translated
                print "!! line %d: %s vs. %s" % (i, msgid, msgstr)
        i += 1

    f.close()
