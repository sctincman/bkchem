#--------------------------------------------------------------------------
#     This file is part of BKchem - a chemical drawing program
#     Copyright (C) 2002-2004 Beda Kosata <beda@zirael.org>

#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     Complete text of GNU GPL can be found in the file gpl.txt in the
#     main directory of the program

#--------------------------------------------------------------------------


"""support module for some geometric mesurements ( geometric tramforms are in transform.py)"""

from __future__ import division
from math import sqrt, atan2, pi, cos, sin
from misc import signum, normalize_coords
import operator



def find_parallel( x1, y1, x2, y2, d):
  "returns tuple of coordinates for parallel abscissa in distance d"
  # following is here to ensure that signum of "d" clearly determines
  # the side of line on whitch the parallel is drawn  
  if round( y2, 3) -round( y1, 3) != 0:
    if y2 < y1:
      d = -d 
    k = -(x2-x1)/(y2-y1)
    x = ( d + sqrt( k**2 +1)*x1)/ sqrt( k**2 +1)
    y = y1 + k*( x -x1)
    x0 = ( d + sqrt( k**2 +1)*x2)/ sqrt( k**2 +1)
    y0 = y2 + k*( x0 -x2)
  else:
    if x1 > x2:
      d = -d
    x, x0 = x1, x2
    y = y1 - d
    y0 = y2 - d
  return (x, y, x0, y0)

def get_parallel_distance( l1, l2):
  "returns distance of two parallels - does not check whether the two are really parallels"
  x1a, y1a, x2a, y2a = l1
  x1b, y1b, x2b, y2b = l2
  if x1a == x2a:
    return y1a-y2a
  elif y1a == y2a:
    return x1a-x2a
  else:
    ka = (y2a - y1a)/(x2a - x1a)
    qa = y1a - ka*x1a
    kb = ka
    qb = y1b - kb*x1b
    k_rev = -1/ka
    q_rev = y1a - k_rev*x1a
    x0 = (qb - q_rev)/(k_rev - kb)
    y0 = k_rev*x0 + q_rev
    d = sqrt( (x1a-x0)**2 + (y1a-y0)**2)
    if qa < qb:
      d = -d
    return d
  

def get_parallel_signum( l1, l2):
  x1a, y1a, x2a, y2a = l1
  x1b, y1b, x2b, y2b = l2
  if x1a == x2a:
    return signum( -x1a + x1b)
  elif y1a == y2a:
    return signum( -y1a+y1b)
  else:
    return signum( -x2a+x2b)

def on_which_side_is_point( line, point):
  """tells whether a point is on one side of a line or on the other (1,0,-1) - 0 is for point on line.
  line is given as sequence of four coordinates, point as sequence of two coords"""
  x1, y1, x2, y2 = line
  x, y = point
  a = atan2( y-y1, x-x1)
  b = atan2( y2-y1, x2-x1)
  if a*b < 0 and abs(a-b) > pi:
    if a < 0:
      a += 2*pi
    else:
      b += 2*pi
  if a-b < 0:
    return 1
  elif a-b == 0:
    return 0
  else:
    return -1

def point_on_circle( center_x, center_y, radius, direction = (), resolution = 15):
  """finds point on circle in direction of (dx, dy), optionaly rounds the angle
  according to resolution"""
  dx, dy = direction
  angle = round( atan2( dy, dx)/(pi*resolution/180.0))*(pi*resolution/180.0)
  x = center_x + round( cos( angle) *radius, 2)
  y = center_y + round( sin( angle) *radius, 2)
  return x,y


def angle_between_lines( l1, l2):
  """returns angle between two lines"""
  pass


def clockwise_angle_from_east( dx, dy):
  """returns the angle in clockwise direction between the center-east line and direction"""
  angle = atan2( dy, dx)
  if angle < 0:
    angle = 2*pi + angle
  return angle


def intersection_of_line_and_rect( line, rect, round_edges=0):
  """finds a point where a line and a rectangle intersect,
  both are given as lists of len == 4"""
  lx0, ly0, lx1, ly1 = line
  rx0, ry0, rx1, ry1 = normalize_coords( rect)

  # find which end of line is in the rect and reverse the line if needed
  if (lx0 > rx0) and (lx0 < rx1) and (ly0 > ry0) and (ly0 < ry1):
    lx0, lx1 = lx1, lx0
    ly0, ly1 = ly1, ly0

  # the computation itself
  ldx = lx1 - lx0
  ldy = ly1 - ly0

  # when ldx and ldy are close apply the rounding of edges
  if not ldy == 0 and abs( abs( ldx) / abs( ldy) - 1) < 0.1:
    modifier = (round_edges, round_edges, -round_edges, -round_edges)
    rx0, ry0, rx1, ry1 = map( operator.add, normalize_coords( rect), modifier)
  
  if ldy == 0 or (abs( ldx) /  abs( ldy)) > (abs( rx0 -rx1) / abs( ry0 -ry1)):
    k = ldy/ldx
    q = ly0 - k*lx0
    if ldx < 0:
      x = rx1
    else:
      x = rx0
    y = k*x + q
  else:
    k = ldx/ldy
    q = lx0 - k*ly0
    if ldy < 0:
      y = ry1
    else:
      y = ry0
    x = k*y + q
  return (x, y)

