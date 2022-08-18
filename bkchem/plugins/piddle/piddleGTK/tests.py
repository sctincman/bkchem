#! /usr/bin/env python

"""Test script for piddle.GTK.

This script allows all the normal piddle tests to be run as well as a
few specific to piddleGTK.

It isn't really part of the piddleGTK package, in spite of its
location in the filesystem.  As long as piddle and piddleGTK are
importable on the normal path, this should operate regardless of where
its own location.

"""

import string
import sys

import gtk

import piddle
import piddletest

# We import piddleGTK.core to get at the internals of font mapping,
# not to demonstrate normal usage.
#
import piddleGTK
import piddleGTK.core

from piddle import Color, Font


def main():
    top = gtk.GtkWindow()
    bbox = gtk.GtkVButtonBox()
    bbox.set_spacing(0)
    top.add(bbox)
    top.connect("destroy", gtk.mainquit)
    top.connect("delete_event", gtk.mainquit)
    tests = map((lambda test: (string.capitalize(test.__name__), test)),
                piddletest.tests)
    tests.extend(testitems)
    for name, test in tests:
        b = gtk.GtkButton(name)
        b.connect("clicked", Test(test))
        bbox.pack_start(b)
    top.show_all()
    gtk.mainloop()


# These are the test routines; they may make use of various classes and
# helper functions defined below.
#
def gtk_test_1(canvasClass):
    """Test case that exercises the ability to set the background color of
    the piddleGTK.*Canvas classes.  Also tests interactive capability.
    """
    canvas = canvasClass((200, 200))
    #
    canvas.backgroundColor = Color(0.9, 0.9, 0.8)
    canvas.clear()
    canvas.drawLine(10, 10, 190, 190)
    canvas.drawLine(10, 190, 190, 10, Color(1.0,0.0,0.0), 3)
    canvas.drawRect(90, 10, 110, 30, edgeWidth=2,
                    edgeColor=Color(0.0,0.0,0.7))
    canvas.drawRect(90, 170, 110, 190, edgeWidth=2,
                    edgeColor=Color(1.0,0.0,0.0),
                    fillColor=Color(0.0,0.0,0.7))
    canvas.drawLines([(50, 90, 150, 90),
                      (50, 110, 150, 110),
                      (90, 50, 90, 150),
                      (110, 50, 110, 150),
                      ], color=Color(0.0,0.0,1.0), width=2)
    canvas.drawPolygon([(30,10), (51,31), (30,52)],
                       edgeColor=Color(0.0,0.7,0.0), edgeWidth=2)
    canvas.drawPolygon([(130,10), (151,31), (130,52)],
                       edgeColor=Color(0.0,0.6,0.6), edgeWidth=2,
                       fillColor=Color(0.5,0.0,0.0), closed=1)
    canvas.onClick = onClick
    canvas.onOver = onOver
    canvas.onKey = onKey
    return canvas


def standard_fonts(canvasClass):
    """Checks font metrics, and also illustrates the standard fonts."""
    tester = StringTester(canvasClass, "test-standard-fonts")
    tester.centerAndBox("spam, spam, spam, baked beans, and spam!")
    tester.canvas.flush()
    tester.showFonts("times", "courier", "helvetica", "symbol",
                     "monospaced", "serif", "sansserif")
    return tester.canvas


def extra_fonts(canvasClass):
    """Checks font metrics and illustrates some additional X11 fonts.

    Not all X11 installations will have all these fonts, so be prepared
    to edit the list of fonts that get used.
    """
    tester = StringTester(canvasClass, "test-extra-fonts")
    tester.showFonts("avantgarde", "bookman", "charter", "gothic",
                     "helvetica narrow", "lucida", "lucidabright",
                     "mincho", "new century schoolbook", "palatino")
    return tester.canvas


def font_mapping(canvasClass):
    f = TextDisplay("Font Conversion Test")
    fonts = [
        Font(),
        Font(bold=1),
        Font(size=24, italic=1),
        Font(bold=1, italic=1),
        Font(face='courier'),
        Font(face='monospaced'),
        ]
    for font in fonts:
        key = piddleGTK.core._font_to_key(font)
        xlfd = piddleGTK.core._fontkey_to_xlfd(key)
        f.write("%s\n" % font)
        f.write("    %s\n" % repr(key))
        f.write("    %s\n\n" % xlfd)
    # just have to have a .flush() method:
    return f


# List of (description, function) pairs that should be used to create the
# test selection dialog.  Similar to the piddletest.tests list, but allows
# more human-friendly names for the tests.
#
testitems = [
    ("Background Color", gtk_test_1),
    ("Non-rotated Text", standard_fonts),
    ("X11 Fonts", extra_fonts),
    ("Font Mapping", font_mapping),
    ]


def onClick(canvas, x, y):
    canvas.setInfoLine("onClick(%s, %s)" % (x, y))

def onOver(canvas, x, y):
    canvas.setInfoLine("onOver(%s, %s)" % (x, y))

def onKey(canvas, key, modifiers):
    canvas.setInfoLine("onKey(%s, %s)" % (repr(key), modifiers))



class StringTester(object):
    def __init__(self, canvasClass, name):
        self.canvas = canvasClass(size=(560,400), name=name, infoline=0)
        self.curs = [10, 10]

    def showFonts(self, *fontlist):
        self.canvas.defaultLineColor = piddle.black
        for size in (12, 18):
            for fontname in fontlist:
                self.curs = [10, (self.curs[1] + size*1.5)]
                self.write("%s %d" % (fontname,size),
                           Font(face=fontname, size=size))
                self.write(" bold",
                           Font(face=fontname, size=size, bold=1))
                self.write(" italic",
                           Font(face=fontname, size=size, italic=1))
                self.write(" bold+italic",
                           Font(face=fontname, size=size, bold=1, italic=1))
                self.write(" underlining",
                           Font(face=fontname, size=size, underline=1))

    def write(self, s, font):
        if font:
            self.canvas.defaultFont = font
        text = s
        while text and text[-1] == '\n':
            text = text[:-1]
        curs = self.curs
        self.canvas.drawString(text, x=curs[0], y=curs[1])
        if s[-1] == '\n':
            curs[0] = 10
            curs[1] = (curs[1] + self.canvas.fontHeight()
                       + self.canvas.fontDescent())
        else:
            curs[0] = curs[0] + self.canvas.stringWidth(s)

    def centerAndBox(self, s, cx=None, y=None):
        "tests string positioning, stringWidth, fontAscent, and fontDescent"
        canvas = self.canvas
        if cx is None:
            cx = canvas.size[0] / 2
        if y is None:
            y = self.curs[1] + 30
            self.curs[1] = y + 30
        canvas.drawLine(cx,y-30, cx,y+30, color=piddle.yellow)
        w = canvas.stringWidth(s)

        canvas.drawLine(cx-w/2, y, cx+w/2, y, color=piddle.red)
        canvas.drawString(s, cx-w/2, y)
        canvas.defaultLineColor = Color(0.7,0.7,1.0)          # light blue
        canvas.drawLine(cx-w/2, y-20, cx-w/2, y+20)           # left
        canvas.drawLine(cx+w/2, y-20, cx+w/2, y+20)           # right
        asc, desc = canvas.fontAscent(), canvas.fontDescent()
        canvas.drawLine(cx-w/2-20, y-asc, cx+w/2+20, y-asc)   # top
        canvas.drawLine(cx-w/2-20, y+desc, cx+w/2+20, y+desc) # bottom


class TextDisplay(object):
    def __init__(self, title):
        top = gtk.GtkDialog()
        top.set_title(title)
        # set up the text widget at the top:
        scrwin = gtk.GtkScrolledWindow()
        scrwin.set_border_width(10)
        scrwin.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        text = self.__text = gtk.GtkText(vadj=scrwin.get_vadjustment())
        text.freeze()
        scrwin.add(text)
        top.vbox.pack_start(scrwin)
        # set up the dismiss button:
        button = gtk.GtkButton("Dismiss")
        button.connect("clicked",
                       lambda button, top=top: top.destroy())
        bbox = gtk.GtkHButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.pack_end(button)
        top.action_area.pack_end(bbox)
        # all done!
        top.set_default_size(500, 300)
        top.show_all()

    def write(self, s):
        self.__text.insert_defaults(s)

    def flush(self):
        self.__text.thaw()


class Test(object):
    def __init__(self, test):
        self.test = test

    def __call__(self, button):
        canvas = self.test(piddleGTK.GTKCanvas)
        canvas.flush()


if __name__ == "__main__":
    main()
