#!/bin/sh

for i in `ls -d ../??`
do
  mkdir -p ${i}/LC_MESSAGES
  msgfmt ${i}/BKChem.po -o ${i}/LC_MESSAGES/BKChem.mo
done
