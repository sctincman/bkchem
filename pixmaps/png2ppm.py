import PIL.Image as Image
import os.path
import os

def w_to_grey( i):
  if i == 0:
    return 200
  elif i == 255:
    return 0
  else:
    return i

for file in os.listdir( os.getcwd()):
  if os.path.isfile( file):
    pth = os.path.splitext( file)
    if pth[1] == '.png':
      img = Image.open( file)
      size = img.size
      bands = img.split()
      if len( bands) == 4:
        r, g, b, a = bands
        img = Image.new( "RGB", size, (200, 200, 200))
        img.paste( Image.merge( "RGB", (r,g,b)), (0, 0, size[0], size[1]), a)

      img.convert('RGB').save( pth[0]+'.ppm','PPM')
      print "converting %s.png to %s.ppm" % (pth[0],pth[0])
