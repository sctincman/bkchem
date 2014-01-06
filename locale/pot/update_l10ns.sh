#!/bin/bash

shopt -s extglob
for i in `ls -d ../?(??|??_??)`
do
  echo ${i}
  msgmerge -v -w 79 --update ${i}/BKChem.po BKChem.pot
done
