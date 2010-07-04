#!/bin/bash

cd doc
mkdir html
docbook2html doc.xml -o html 2>/dev/null
docbook2pdf doc.xml 2>/dev/null
cd ..

cp -v locale/pot/BKChem.pot locale/

echo "Compiling *.po files..."
cd locale/pot
./compile_l10ns.sh
cd ../..

echo "convert the logo to ppm"
echo "release number in:"
echo "images/logo.xcf"
echo "bkchem/config.py"
echo "setup.py"
echo "RELEASE"
echo
echo "set config.debug to 0"
