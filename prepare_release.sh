#! /bin/bash

rm blockers
rm TODO
rm BUGS

find -name "*.pyc" -exec rm -f \{} \;
find -name "*~" -exec rm -f \{} \;
find -name ".xvpics" -exec rm -rf \{} \;
find -name "CVS" -exec rm -rf \{} \;

cd bkchem
rm -fr *.svg
rm -fr *.cml
rm -fr *.cdml
rm -fr *.zip
rm -fr *.sxd

cd ../locale/cs
rm BKchem.mo

cd ../../pixmaps
rm -f *.png

cd ../images
rm -f logo.xcf

cd ..
rm -fr cdml
rm binary-howto.txt
