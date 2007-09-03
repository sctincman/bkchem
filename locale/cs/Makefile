# makefile that updates the current string definitions from BKchem source (make update)
# and after you edit the BKchem.po file it installs it (make || make install)

# source to pot translator
S2POT = pygettext.py

# domain
DOMAIN = BKchem

# recoding options
RECODEBACK = iso2utf.py
RECODE = utf2iso.py

PYDIR = ../../bkchem

PYFILES = *.py

.PHONY: update install prepare


all: install
	echo install complete

install: $(DOMAIN).mo
	cp $(DOMAIN).mo LC_MESSAGES/$(DOMAIN).mo

$(DOMAIN).mo: $(DOMAIN).po
	msgfmt $(DOMAIN).po -o $(DOMAIN).mo

#$(DOMAIN).po: $(DOMAIN).iso.po
#	$(RECODEBACK) $(DOMAIN).iso.po $(DOMAIN).po

update: prepare
#$(RECODE) $(DOMAIN).po $(DOMAIN).iso.po
	echo created $(DOMAIN).po - edit it
#	rm $(DOMAIN).pot

prepare: $(DOMAIN).pot $(DOMAIN).po
	cp $(DOMAIN).po $(DOMAIN).po.backup
	msgmerge $(DOMAIN).po.backup $(DOMAIN).pot > $(DOMAIN).po
	rm $(DOMAIN).po.backup

$(DOMAIN).pot: 
	$(S2POT) -d $(DOMAIN) $(PYDIR)/$(PYFILES) $(PYDIR)/plugins/$(PYFILES) $(PYDIR)/../plugins/$(PYFILES) 