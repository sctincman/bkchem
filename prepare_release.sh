#! /bin/bash

cd doc
mkdir html
docbook2html doc.xml -o html 2>/dev/null
docbook2pdf doc.xml 2>/dev/null
docbook2ps doc.xml 2>/dev/null
cd ..

echo "convert the logo to ppm"
echo "release number in:"
echo "setup.py"
echo "bkchem/data.py"
echo "RELEASE"
echo
echo "set config.debug to 0"



