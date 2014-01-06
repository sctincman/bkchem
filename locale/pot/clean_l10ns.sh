#!/bin/bash

shopt -s extglob
for i in `ls -d ../?(??|??_??)`
do
  rm -r ${i}/LC_MESSAGES
  rm -f ${i}/BKChem.po~
done
