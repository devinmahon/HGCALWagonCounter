# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 12:53:46 2021

@author: Troilus D'Troy'
"""

from PIL import Image, ImageDraw, ImageFont
import math
import numpy as np

# =============================================================================
# Functions

# drawfunctions

font = ImageFont.load_default()

def hexdraw(bow, x, y, des, rot, mb, eng, maxLinks = 0,EW = 1):
    cx = x
    cy = y
    rot = float(rot)
    maxLinksType = type(maxLinks)
    #if des == 'F' or des == 'FI' or des == 'FIe' or des == 'FMI' or des == 'FO'\
            #or des == 'FOe' or des == 'FM' or des == 'FMe':
    if 'F' in des:
        # draw full hex
        if rot == 0 or rot == 1 or rot == 2 or rot == 3 or rot == 4 or rot == 5:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r), (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx-0.2*r,cy-0.5*r), str(maxLinks), font = font,fill='black')
        # orientation
        draworfull(cx, cy, r, rot)
        # draw engine
        if eng == 'True' and EW and rot == 0:
            draw.polygon(((cx+.866*r, cy+r/4), (cx+.7*r, cy+r/4), (cx+.7*r, cy-r/4),
                          (cx+.866*r, cy-r/4)), fill=(255, 51, 51), outline=(0, 0, 0))
        elif eng == 'True' and not EW and rot == 0:
            draw.polygon(((cx-.866*r, cy+r/4), (cx-.7*r, cy+r/4), (cx-.7*r, cy-r/4),
                          (cx-.866*r, cy-r/4)), fill=(255, 51, 51), outline=(0, 0, 0))
        # looks a little off
        elif eng == 'True' and rot == 1:
            if EW:
              draw.polygon(((cx+r*.213, cy-r*.875), (cx+.663*r, cy-r*.613), (cx+.575*r, cy-r*.475),
                            (cx+r*.125, cy-r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
            else:
              draw.polygon(((cx-r*.213, cy+r*.875), (cx-.663*r, cy+r*.613), (cx-.575*r, cy+r*.475),
                            (cx-r*.125, cy+r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
        elif eng == 'True' and rot == 2:
            if EW:
              draw.polygon(((cx-r*.213, cy-r*.875), (cx-.663*r, cy-r*.613), (cx-.575*r, cy-r*.475),
                            (cx-r*.125, cy-r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
            else:
              draw.polygon(((cx+r*.213, cy+r*.875), (cx+.663*r, cy+r*.613), (cx+.575*r, cy+r*.475),
                            (cx+r*.125, cy+r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
        elif eng == 'True' and rot == 3:
            if EW:
              draw.polygon(((cx-.866*r, cy+r/4), (cx-.7*r, cy+r/4), (cx-.7*r, cy-r/4),
                            (cx-.866*r, cy-r/4)), fill=(255, 51, 51), outline=(0, 0, 0))
            else:
              draw.polygon(((cx+.866*r, cy-r/4), (cx+.7*r, cy-r/4), (cx+.7*r, cy+r/4),
                            (cx+.866*r, cy+r/4)), fill=(255, 51, 51), outline=(0, 0, 0))
        elif eng == 'True' and rot == 4:
            if EW:
              draw.polygon(((cx-r*.213, cy+r*.875), (cx-.663*r, cy+r*.613), (cx-.575*r, cy+r*.475),
                            (cx-r*.125, cy+r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
            else:
              draw.polygon(((cx+r*.213, cy-r*.875), (cx+.663*r, cy-r*.613), (cx+.575*r, cy-r*.475),
                            (cx+r*.125, cy-r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
        elif eng == 'True' and rot == 5:
            if EW:
              draw.polygon(((cx+r*.213, cy+r*.875), (cx+.663*r, cy+r*.613), (cx+.575*r, cy+r*.475),
                            (cx+r*.125, cy+r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))
            else:
              draw.polygon(((cx-r*.213, cy-r*.875), (cx-.663*r, cy-r*.613), (cx-.575*r, cy-r*.475),
                            (cx-r*.125, cy-r*.737)), fill=(255, 51, 51), outline=(0, 0, 0))

    #elif des == 'aIe' or des == 'aOe' or des == 'aM' or des == 'aOe' or des == 'aMe':
    elif 'a' in des:
        rot = (rot+4)%6
        if rot == 4:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            # draw.polygon(((cx,cy+r),(cx-.433*r,cy+3/4*r),(cx,cy+3/4*r)),\
            #                 fill=(0,0,0),outline=(0,0,0))
            if maxLinksType == int:
                draw.text((cx - 0.425*r, cy - 0.05*r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.575*r, cy - 0.05*r), str(maxLinks), font = font) 
        elif rot == 5:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx+.866*r, cy+r/2)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.20*r, cy + 0.25 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.35*r, cy + 0.25 * r), str(maxLinks), font = font)
        elif rot == 0:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx+.866*r, cy-r/2),
                          (cx+.866*r, cy+r/2)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx + 0.10*r, cy + 0.25*r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.05*r, cy + 0.25*r), str(maxLinks), font = font)
        elif rot == 1:
            draw.polygon(((cx, cy+r), (cx, cy-r), (cx+.866*r, cy-r/2),
                          (cx+.866*r, cy+r/2)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            # draw.polygon(((cx,cy+r),(cx,cy+3/4*r),(cx+.433*r,cy+3/4*r)),\
            #                 fill=(0,0,0),outline=(0,0,0))
            if maxLinksType == int:
                draw.text((cx + 0.325*r, cy - 0.05*r), str(maxLinks), font = font)
            else:
                draw.text((cx + 0.175*r, cy - 0.05*r), str(maxLinks), font = font)
        elif rot == 2:
            draw.polygon(((cx-.866*r, cy-r/2), (cx, cy-r), (cx+.866*r, cy-r/2),
                          (cx+.866*r, cy+r/2)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            # the 2nd coord is still wrong a bit
            # draw.polygon(((cx+.866*r,cy+r/2),(cx+r*.70,cy+.4*r),(cx+.866*r,cy)),\
            #             fill=(0,0,0),outline=(0,0,0))
            if maxLinksType == int:
                draw.text((cx + 0.10*r, cy - 0.45 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.05*r, cy - 0.45 * r), str(maxLinks), font = font)
        elif rot == 3:
            draw.polygon(((cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2), (cx, cy-r),
                          (cx+.866*r, cy-r/2)), fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.20*r, cy - 0.45 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.35*r, cy - 0.45 * r), str(maxLinks), font = font)
    #elif des == 'bI' or des == 'bIe' or des == 'bMe' or des == 'bOe':
    elif 'b' in des:
        rot = (rot+4)%6
        if rot == 4:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r), (cx+.866*r, cy-r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
        elif rot == 5:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
        elif rot == 0:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            # draw.polygon(((cx,cy+r),(cx-.433*r,cy+3/4*r),(cx+.433*r,cy+3/4*r)),\
            #                 fill=(0,0,0),outline=(0,0,0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
        elif rot == 1:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx, cy-r),
                          (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
        elif rot == 2:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy-r/2), (cx, cy-r),
                          (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
        elif rot == 3:
            draw.polygon(((cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2), (cx, cy-r),
                          (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            if maxLinksType == int:
                draw.text((cx - 0.05 * r, cy - 0.05 * r), str(maxLinks), font = font)
            else:
                draw.text((cx - 0.20 * r, cy - 0.05 * r), str(maxLinks), font = font)
    #elif des == 'cOe':
    elif 'c' in des:
        rot = (rot+2)%6
        if rot == 2:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx - 0.425*r, cy - 0.05*r), str(maxLinks), font = font)
        elif rot == 3:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx - 0.20*r, cy + 0.25 * r), str(maxLinks), font = font)
        elif rot == 4:
            draw.polygon(((cx, cy+r), (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx + 0.10*r, cy + 0.25*r), str(maxLinks), font = font)
        elif rot == 5:
            draw.polygon(((cx+.866*r, cy+r/2), (cx+.866*r, cy-r/2), (cx, cy-r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx + 0.325*r, cy - 0.05*r), str(maxLinks), font = font)
        elif rot == 0:
            draw.polygon(((cx, cy-r), (cx-.866*r, cy-r/2), (cx+.866*r, cy-r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx + 0.10*r, cy - 0.45 * r), str(maxLinks), font = font)
        elif rot == 1:
            draw.polygon(((cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2), (cx, cy-r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            draw.text((cx - 0.20*r, cy - 0.45 * r), str(maxLinks), font = font)
    #elif des == 'dIe' or des == 'dOe':
    elif 'd' in des:
        rot = (rot+0)%6
        if rot == 5:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx-.433*r, cy-3/4*r), (cx+.433*r, cy+3/4*r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx - 0.425*r, cy - 0.05*r), str(maxLinks), font = font)
        elif rot == 0:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy),
                          (cx+.866*r, cy), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx - 0.20*r, cy + 0.25 * r), str(maxLinks), font = font)
        elif rot == 1:
            draw.polygon(((cx, cy+r), (cx+.866*r, cy+r/2), (cx+.866*r, cy-r/2),
                          (cx+.433*r, cy-3/4*r), (cx-.433*r, cy+3/4*r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx + 0.10*r, cy + 0.25*r), str(maxLinks), font = font)
        elif rot == 2:
            draw.polygon(((cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2), (cx+.433*r, cy+3/4*r),
                          (cx-.433*r, cy-3/4*r), (cx, cy-r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx - 0.325*r, cy - 0.05*r), str(maxLinks), font = font)
        elif rot == 3:
            draw.polygon(((cx, cy-r), (cx-.866*r, cy-r/2), (cx-.866*r, cy),
                          (cx+.866*r, cy), (cx+.866*r, cy-r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx + 0.10*r, cy - 0.45 * r), str(maxLinks), font = font)
        elif rot == 4:
            draw.polygon(((cx-.433*r, cy+3/4*r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r), (cx+.433*r, cy-r*3/4)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
            #draw.text((cx - 0.20*r, cy - 0.45 * r), str(maxLinks), font = font)
        draw.text((cx-0.2*r,cy-0.5*r), str(maxLinks), font = font,fill='black')
    #elif des == 'gIe':
    elif 'g' in des:
        rot = (rot+4)%6
        if rot == 2:
            draw.polygon(((cx, cy+r), (cx-r/2, cy+r*.71), (cx-r/2, cy-r*.71),
                          (cx, cy-r), (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
        elif rot == 0:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          ((cx-r/2), cy-.866*r), (cx+.866*r, cy), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
        elif rot == 1:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy),
                          ((cx+r/2), cy-.866*r), (cx+.866*r, cy-r/2), (cx+.866*r, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
        elif rot == 3:
            draw.polygon(((cx-.866*r, cy), (cx-.866*r, cy-r/2), (cx, cy-r),
                          ((cx+r*.866), cy-r/2), (cx+.866*r, cy+r/2), (cx+r/2, cy+.866*r)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
        elif rot == 4:
            draw.polygon(((cx, cy+r), (cx-.866*r, cy+r/2), (cx-.866*r, cy-r/2),
                          (cx, cy-r), (cx+r/2, cy-r/2), (cx+r/2, cy+r/2)),
                         fill=MBColor(bow, mb, des), outline=(0, 0, 0))
        draw.text((cx-0.2*r,cy-0.5*r), str(maxLinks), font = font,fill='black')
        # orientation
        # draworfull(cx,cy,r,rot)

# =============================================================================
# draws orientation arrow on hex in irot direction for full black arrowhead


def draworfull(cx, cy, r, rot):
    if rot == 0 or rot == 6:
        draw.polygon(((cx, cy+r), (cx-.433*r, cy+3/4*r), (cx+.433*r, cy+3/4*r)),
                     fill=(0, 0, 0), outline=(0, 0, 0))
    elif rot == 1:
        draw.polygon(((cx+.866*r, cy+r/2), (cx+r/2, cy+.71*r), (cx+.866*r, cy)),
                     fill=(0, 0, 0), outline=(0, 0, 0))
    elif rot == 2:
        draw.polygon(((cx+.866*r, cy), (cx+r/2, cy-.71*r), (cx+.866*r, cy-r/2)),
                     fill=(0, 0, 0), outline=(0, 0, 0))
    elif rot == 3:
        draw.polygon(((cx, cy-r), (cx-.433*r, cy-3/4*r), (cx+.433*r, cy-3/4*r)),
                     fill=(0, 0, 0), outline=(0, 0, 0))
    elif rot == 4:
        draw.polygon(((cx-.866*r, cy), (cx-.866*r, cy-r/2), (cx-r/2, cy-.71*r)),
                     fill=(0, 0, 0), outline=(0, 0, 0))
    elif rot == 5:
        draw.polygon(((cx-.866*r, cy+r/2), (cx-.866*r, cy), (cx-r/2, cy+.71*r)),
                     fill=(0, 0, 0), outline=(0, 0, 0))

# =============================================================================


def MBColor(bow, MB, des):
    colorsld = [(153, 255, 255), (255, 153, 153), (153, 204, 255), (255, 204, 153),
                (153, 153, 255), (255, 255, 153), (204,
                                                   153, 255), (204, 255, 153), (204, 102, 0),
                (255, 153, 255), (153, 255, 153), (255, 153,
                                                   204), (153, 255, 204), (224, 224, 224),
                (153, 255, 255), (255, 153, 153), (153, 204, 255), (255, 204, 153),
                (153, 153, 255), (255, 255, 153), (204,
                                                   153, 255), (204, 255, 153), (204, 102, 0),
                (255, 153, 255), (153, 255, 153), (255, 153,
                                                   204), (153, 255, 204), (224, 224, 224),
                (153, 255, 255), (255, 153, 153), (153, 204, 255), (255, 204, 153),
                (153, 153, 255), (255, 255, 153), (204,
                                                   153, 255), (204, 255, 153), (204, 102, 0),
                (255, 153, 255), (153, 255, 153), (255, 153, 204), (153, 255, 204), (224, 224, 224)]
    colorshd = [(53, 155, 155), (155, 53, 53), (53, 104, 155), (155, 104, 53),
                (53, 53, 155), (155, 155, 53), (104,
                                                53, 155), (104, 155, 53), (104, 2, 0),
                (155, 53, 155), (53, 155, 53), (155, 53,
                                                104), (53, 155, 104), (124, 124, 124),
                (53, 155, 155), (155, 53, 53), (53, 104, 155), (155, 104, 53),
                (53, 53, 155), (155, 155, 53), (104,
                                                53, 155), (104, 155, 53), (104, 2, 0),
                (155, 53, 155), (53, 155, 53), (155, 53,
                                                104), (53, 155, 104), (124, 124, 124),
                (53, 155, 155), (155, 53, 53), (53, 104, 155), (155, 104, 53),
                (53, 53, 155), (155, 155, 53), (104,
                                                53, 155), (104, 155, 53), (104, 2, 0),
                (155, 53, 155), (53, 155, 53), (155, 53, 104), (53, 155, 104), (124, 124, 124)]
    # the data has some weird namings with MBs that jump from ~15 to restart at 100
    # they start at 100 for the section between 60-120 deg that they duplicated
    # the first 28 layers used to only be 60 deg drawings
    if bow == 0:
        mb = int(MB)
        while mb > 41:
            mb -= 41
        if des == 'FI' or des == 'FIe' or des == 'aIe' or des == 'bI' or des == 'bIe' or des == 'dIe' or des == 'gIe':
            pick = colorshd[mb]
        else:
            pick = colorsld[mb]
    elif bow == 1:
        pick = (0, 200, 0)
    elif bow == 2:
        pick = (220, 220, 220)
    elif bow == 3:
        pick = (0, 100, 0)
    return pick
# =============================================================================
# Repositioning Wagon for evaluation

# Function to move wagon to (0,0) coordinates before evaluating shape


def ToOrigin(list1):
    #list1.sort(key=lambda i:i[1])
    dis = 1000
    for hx in list1:
        if (hx[1]**2+hx[2]**2)**.5 < dis:
            xo = hx[1]
            yo = hx[2]
            dis = (hx[1]**2+hx[2]**2)**.5

    for hx in list1:
        # move x to 0
        hx[1] = hx[1]-xo
        # move y to 0
        hx[2] = hx[2]-yo


def Slope(wagon):
    slope = []

    i = 0
    for i in range(0, len(wagon)-1, 1):
        if (wagon[i+1][1]-wagon[i][1]) == 0:
            if wagon[i+1][2] > wagon[i][2]:
                s = float('inf')
            elif wagon[i+1][2] < wagon[i][2]:
                s = float('-inf')
        else:
            s = (wagon[i+1][2]-wagon[i][2])/(wagon[i+1][1]-wagon[i][1])
            if wagon[i+1][1] < wagon[i][1] and wagon[i+1][2] < wagon[i][2]:
                s = -1*s
        slope.append(s)

    return slope

# Rotate to be flat


def Rotate(wagon):
    # changing rotation check to work off engine piece irot instead of slope for nontriangles
    erot = ''
    for line in wagon:
        if line[8] == 'True':
            erot = line[4]
            # fix for negative rots
            # if erot==-1:
            #    erot=5
            # elif erot==-2:
            #    erot=4
            # elif erot==-3:
            #    erot=3
            # elif erot==-4:
            #    erot=2
            # elif erot==-5:
            #    erot=1

    # categorize based off slope.
    # determine slopes
    slope = Slope(wagon)

    # want to rotate things like triangle into a default orientation to make it easier to see which are same
    r2s = ''

    # catch single hex pieces from breaking code
    if slope == []:
        slope = []
    # Catching Triangles to rotate to uniform orientation
    elif slope == [0.0, float('inf')]:
        r2s = 'T'
    elif slope == [1.0, float('-inf')]:
        wagon.sort(key=lambda i: (i[1], i[2]))
        slope = [0.0, float('inf')]
        r2s = 'T'
    elif slope == [float('-inf'), 1.0]:
        wagon[1][1] = 1
        wagon[1][2] = 0
        wagon[2][1] = 1
        wagon[2][2] = 1
        slope = [0.0, float('inf')]
        r2s = 'T'
        for hx in wagon:
            hx[4] += 1
    elif slope == [0.0, -1.0]:
        wagon[1][1] = 1
        wagon[1][2] = 1
        wagon[2][1] = 1
        wagon[2][2] = 0
        wagon.sort(key=lambda i: (i[1], i[2]))
        slope = [0.0, float('inf')]
        r2s = 'T'
        for hx in wagon:
            hx[4] += 1
    elif slope == [float('inf'), 0.0]:
        wagon[1][1] = 1
        wagon[1][2] = 1
        wagon[2][1] = 1
        wagon[2][2] = 0
        wagon.sort(key=lambda i: (i[1], i[2]))
        slope = [0.0, float('inf')]
        r2s = 'T'
        for hx in wagon:
            hx[4] -= 1
    elif slope == [-1.0, 0.0]:
        wagon[1][1] = 1
        wagon[1][2] = 0
        wagon[2][1] = 1
        wagon[2][2] = 1
        wagon.sort(key=lambda i: (i[1], i[2]))
        slope = [0.0, float('inf')]
        r2s = 'T'
        for hx in wagon:
            hx[4] += 2
    # special catch for U pieces with 3rd in R2.  Something changed and broke this from
    # processing correctly, so adding this to fix.  Probably an extra sort?
    # I sort by u then v, which is fine, but when you go negative y the order is kind of wrong
    # to try and process semi-linearly
    elif slope == [-1.0, float('inf')]:
        wagon.sort(key=lambda i: (i[1], -i[2]))
        slope = [0.0, float('-inf')]
    elif slope == [float('inf'), -1.0]:
        wagon.sort(key=lambda i: (i[1], -i[2]))
        slope = [0.0, 1.0]
    # correction for U pieces that bend on first hex instead of engine hex
    elif slope == [float('-inf'), 0.0] and erot == 0:
        for i in range(0, len(wagon), 1):
            u = wagon[i][1]
            v = wagon[i][2]
            # change u,v
            wagon[i][1] = u-v
            wagon[i][2] = u
            # change irot
            wagon[i][4] += 1
        # change slopes
        for i in range(0, len(wagon)-1, 1):
            if slope[i] == float('-inf'):
                slope[i] = 0.0
            elif slope[i] == 0.0:
                slope[i] = 1.0
                # 0 can go forwars or backwards... need to account for
            elif slope[i] == 1.0:
                slope[i] = float('inf')
    # everything else
    # if wagon has engine, rotate based on that erot value first
    # for non engine wagons, still need to rotate slopes based on slopes
    # Rotate 1, slope 45deg
    elif erot == 1:
        for i in range(0, len(wagon), 1):
            u = wagon[i][1]
            v = wagon[i][2]
            # change u,v
            wagon[i][1] = v
            wagon[i][2] = v-u
            # change rotation values
            wagon[i][4] = wagon[i][4]-1
        # change slopes
        for i in range(0, len(wagon)-1, 1):
            if slope[i] == 1.0:
                slope[i] = 0.0
            elif slope[i] == 0.0:
                slope[i] = float('-inf')
            elif slope[i] == float('inf'):
                slope[i] = 1.0
            elif slope[i] == float('-inf'):
                slope[i] = -1.0
        erot = 0
        print("triggered erot 1")
    # Rotate inf, slope 90deg
    elif erot == 2:
        for i in range(0, len(wagon), 1):
            u = wagon[i][1]
            v = wagon[i][2]
            # change u,v
            wagon[i][1] = v-u
            wagon[i][2] = -1*u
            # change irot
            wagon[i][4] -= 2
        # change slopes
        for i in range(0, len(wagon)-1, 1):
            if slope[i] == float('inf'):
                slope[i] = 0.0
            elif slope[i] == 0.0:
                slope[i] = -1.0
                # 0 can go forwards or backwards... need to account for
            elif slope[i] == 1.0:
                slope[i] = float('-inf')
        erot = 0
    elif erot == 4:
        for i in range(0, len(wagon), 1):
            u = wagon[i][1]
            v = wagon[i][2]
            # change u,v
            wagon[i][1] = -1*v
            wagon[i][2] = u-v
            # change irot
            wagon[i][4] += 2
        # change slopes
        for i in range(0, len(wagon)-1, 1):
            if slope[i] == float('inf'):
                slope[i] = -1.0
            elif slope[i] == 0.0:
                slope[i] = float('-inf')
                # 0 can go forwards or backwards... need to account for
            elif slope[i] == 1.0:
                slope[i] = 0.0
        erot = 0
    elif erot == -1 or erot == 5:
        for i in range(0, len(wagon), 1):
            u = wagon[i][1]
            v = wagon[i][2]
            # change u,v
            wagon[i][1] = v
            wagon[i][2] = u
            # change irot
            wagon[i][4] -= 2
        # change slopes
        for i in range(0, len(wagon)-1, 1):
            if slope[i] == float('-inf'):
                slope[i] = 0.0
            elif slope[i] == 0.0:
                slope[i] = 1.0
                # 0 can go forwards or backwards... need to account for
            elif slope[i] == 1.0:
                slope[i] = float('inf')
        erot = 0
    elif erot == 0 and r2s != 'T':
        #wagon.sort(key=lambda i:(i[1],i[2]))
        # print(wagon)
        # slope=Slope(wagon)
        # print(slope)
        # there was an engine piece with rot0 but had piece coming out at slope 1, need to lay flat
        # there might be other occurances where I need to add additional slope checks

        if slope[0] == 1.0:
            for i in range(0, len(wagon), 1):
                u = wagon[i][1]
                v = wagon[i][2]
                # change u,v
                wagon[i][1] = v
                wagon[i][2] = v-u
                # change rotation values
                wagon[i][4] = wagon[i][4]-1
            # change slopes
            for i in range(0, len(wagon)-1, 1):
                if slope[i] == 1.0:
                    slope[i] = 0.0
                elif slope[i] == 0.0:
                    slope[i] = float('-inf')
                elif slope[i] == float('inf'):
                    slope[i] = 1.0
        elif slope[0] == float('-inf'):
            for i in range(0, len(wagon), 1):
                u = wagon[i][1]
                v = wagon[i][2]
                # change u,v
                wagon[i][1] = u-v
                wagon[i][2] = u
                # change irot
                wagon[i][4] += 1
                # change slopes
            for i in range(0, len(wagon)-1, 1):
                if slope[i] == float('-inf'):
                    slope[i] = 0.0
                elif slope[i] == 0.0:
                    slope[i] = 1.0
                    # 0 can go forwards or backwards... need to account for
                elif slope[i] == 1.0:
                    slope[i] = float('inf')
    elif erot == '':
        if slope[0] == 1.0:
            for i in range(0, len(wagon), 1):
                u = wagon[i][1]
                v = wagon[i][2]
                # change u,v
                wagon[i][1] = v
                wagon[i][2] = v-u
                # change rotation values
                wagon[i][4] = wagon[i][4]-1
            # change slopes
            for i in range(0, len(wagon)-1, 1):
                if slope[i] == 1.0:
                    slope[i] = 0.0
                elif slope[i] == 0.0:
                    slope[i] = -1.0
                elif slope[i] == float('inf'):
                    slope[i] = float('inf')
        # Rotate inf, slope 90deg
        elif slope[0] == float('inf'):
            for i in range(0, len(wagon), 1):
                u = wagon[i][1]
                v = wagon[i][2]
                # change u,v
                wagon[i][1] = v-u
                wagon[i][2] = -1*u
                # change irot
                wagon[i][4] -= 2
            # change slopes
            for i in range(0, len(wagon)-1, 1):
                if slope[i] == float('inf'):
                    slope[i] = 0.0
                elif slope[i] == 0.0:
                    slope[i] = -1.0
                    # 0 can go forwars or backwards... need to account for
                elif slope[i] == 1.0:
                    slope[i] = float('-inf')
        elif slope[0] == float('-inf'):
            for i in range(0, len(wagon), 1):
                u = wagon[i][1]
                v = wagon[i][2]
                # change u,v
                wagon[i][1] = u-v
                wagon[i][2] = u
                # change irot
                wagon[i][4] += 1
            # change slopes
            for i in range(0, len(wagon)-1, 1):
                if slope[i] == float('-inf'):
                    slope[i] = 0.0
                elif slope[i] == 0.0:
                    slope[i] = 1.0
                    # 0 can go forwars or backwards... need to account for
                elif slope[i] == 1.0:
                    slope[i] = float('inf')

    # print(slope)

    # trying to catch the 6 piece triangle MBs.  Proving hard to separate
    if len(slope) == 5:
        r2s = 'B'

    # rotate triangles again, putting engine in spot (1,0)
    if r2s == 'T' and (wagon[0][8] == 'True' or wagon[1][8] == 'True' or wagon[2][8] == 'True'):
        t = 0
        for line in wagon:
            if line[8] == 'True':
                t = t
                break
            else:
                t += 1

        #print('t rotate 2 triggered')
        # print(wagon)
        owagon = wagon
        wagon = []
        if t == 0:
            owagon[0][1] = 1
            owagon[0][2] = 0
            owagon[1][1] = 1
            owagon[1][2] = 1
            owagon[2][1] = 0
            owagon[2][2] = 0
            owagon.sort(key=lambda i: (i[1], i[2]))
            for hx in owagon:
                hx[4] += 2
            wagon = owagon
        elif t == 1:
            wagon = owagon
        elif t == 2:
            owagon[0][1] = 1
            owagon[0][2] = 1
            owagon[1][1] = 0
            owagon[1][2] = 0
            owagon[2][1] = 1
            owagon[2][2] = 0
            owagon.sort(key=lambda i: (i[1], i[2]))
            for hx in owagon:
                hx[4] -= 2
            wagon = owagon
        # print(wagon)

    return wagon, slope

# =============================================================================
# Generate wagon names


def wname(MB, slope):
    name = ''
    shape = ''

    #HD or LD
    if MB[0][9] == 0:
        name += 'LD'
    elif MB[0][9] == 1:
        name += 'HD'

    # Triangles need some sort to evaluate equally.  Read them either
    # (0,0)->(1,0)->(1,1) or (0,0)->(0,1)->(1,1)
    # additional sort, to catch after the split
    #MB.sort(key=lambda i:(i[1],i[2]))

    # Linear, Triangle, or Unusual
    if len(set(slope)) == 1 and slope[0] == 0:
        name += 'L'
    elif slope == []:
        name += 'L'
        shape = 'L'
    elif len(set(slope)) == 2 and (slope == [0.0, float('inf')]):
        name += 'T'
    else:
        shape = 'U'
        name += 'U'

    # number of hexes in wagon
    name += str(len(MB))

    # hex designations
    i = 0
    for line in MB:
        # describing rotation of odd pieces
        # R1=NE, R2=SE, add more if needed
        if shape == 'U' and i > 1 and slope[i-1] != 0.0:
            name += 'R'
            if slope[i-1] == 1.0:
                name += str(1)
            elif slope[i-1] == float('-inf'):
                name += str(2)
            else:
                name += str(9)
        i += 1

        # including b as F's here
        if line[3] == 'FO' or line[3] == 'FI' or line[3] == 'FM' or line[3] == 'FIe' or line[3] == 'FOe'\
                or line[3] == 'bOe' or line[3] == 'F' or line[3] == 'FMI' or line[3] == 'bMe' \
                or line[3] == 'FMe' or line[3] == 'bIe':
            name += 'F'
        elif line[3] == 'aOe' or line[3] == 'aIe' or line[3] == 'aM' or line[3] == 'aMe':
            name += 'a'
        elif line[3] == 'dOe' or line[3] == 'dIe':
            name += 'd'
        elif line[3] == 'gIe' or line[3] == 'gOe':
            name += 'g'

        # Rotation values
        if shape == 'L' and len(MB) == 1 and\
            (line[3] == 'FO' or line[3] == 'FI' or line[3] == 'FM' or line[3] == 'FIe' or line[3] == 'FOe'
             or line[3] == 'bOe' or line[3] == 'F' or line[3] == 'FMI' or line[3] == 'bMe'
             or line[3] == 'FMe' or line[3] == 'bIe'):
            name += str(0)
            # this catches any stray single pieces with odd rotations and makes 0 for naming
        # correct negative rotations
        elif line[4] == -1:
            name += str(5)
        elif line[4] == -2:
            name += str(4)
        elif line[4] == -3:
            name += str(3)
        elif line[4] == -4:
            name += str(2)
        elif line[4] == -5:
            name += str(1)
        elif line[4] == 6:
            name += str(0)
        else:
            name += str(line[4])

        # isEngine
        if line[8] == 'True':
            name += 'E'

    return name

# =============================================================================
# lets move all wagon drawing functions here and call as needed
# into dynamic spaces


def wagondraw(x, y, wname):

    xf = x
    yf = y
    diag = 0

    wname = wname[2:]

    shape = wname[0]
    wname = wname[2:]

    wl = 0
    n = 0

    while n < len(wname):

        # draw triangle wagons, need a counter that draws their placement fixed
        if shape == 'T':
            # hexshape
            if wname[n] == 'F':
                des = 'FO'
            elif wname[n] == 'a':
                des = 'aOe'
            elif wname[n] == 'b':
                des = 'bOe'
            elif wname[n] == 'd':
                des = 'dOe'
            elif wname[n] == 'g':
                des = 'gOe'

            rot = wname[n+1]

            # Need exception for if indexes for E/R dont exist for last hex
            if n+2 < len(wname):
                # engine check
                if wname[n+2] == 'E':
                    eng = 'True'
                    n += 1
                else:
                    eng = 'False'
            else:
                eng = 'False'

            if wl == 0:
                x = xf
                y = yf
            elif wl == 1:
                x = xf+70
                y = yf
            elif wl == 2:
                x = xf+35
                y = yf-60

        # draw linear wagons.  placement is dynamic
        elif shape == 'L' or shape == 'U':

            # hexshape
            if wname[n] == 'F':
                des = 'FO'
            elif wname[n] == 'a':
                des = 'aOe'
            elif wname[n] == 'b':
                des = 'bOe'
            elif wname[n] == 'd':
                des = 'dOe'
            elif wname[n] == 'g':
                des = 'gOe'

            rot = wname[n+1]

            if diag == 0:
                x = xf+70*wl
            elif diag == 1:
                x = xf+70*wl-35
                y = yf-60
            elif diag == 2:
                x = xf+70*wl-35
                y = yf+60

            # Need exception for if indexes for E/R dont exist for last hex
            if n+2 < len(wname):
                # engine check
                if wname[n+2] == 'E':
                    eng = 'True'
                    n += 1
                    if n+2 < len(wname) and wname[n+2] == 'R':
                        diag = int(wname[n+3])
                        n += 2
                # offlinear
                elif wname[n+2] == 'R':
                    diag = int(wname[n+3])
                    eng = 'False'
                    n += 2
                else:
                    eng = 'False'
                    diag = 0
            else:
                eng = 'False'
                diag = 0

        # print(des,rot,eng,diag,x,y)

        hexdraw(x, y, des, rot, 1, eng)
        # increase wagon length count to offset new hexes
        wl += 1

        n += 2
        if n >= len(wname):
            break


# =============================================================================
def VertToiRot(ls):
    # correct irot for partials only
    vslopes = []
    des = ls[3]
    tol = .035

    if des == 'F' or des == 'FI' or des == 'FIe' or des == 'FMI' or des == 'FO'\
            or des == 'FOe' or des == 'FM' or des == 'FMe':
        pass
    else:
        # save slopes between vertices
        for v in range(0, int(ls[7])*2-1, 2):
            # some pixels dont actually subtract to 0, so giving it space
            if math.isclose(0, (round(float(ls[8+v+2]))-round(float(ls[8+v]))), abs_tol=2.1):
                if round(float(ls[8+v+3])) > round(float(ls[8+v+1])):
                    vs = float('inf')
                elif round(float(ls[8+v+3])) < round(float(ls[8+v+1])):
                    vs = float('-inf')
            else:
                vs = (round(float(ls[8+v+3]))-round(float(ls[8+v+1]))) /\
                    (round(float(ls[8+v+2]))-round(float(ls[8+v])))
                vs = round(vs, 2)
            vslopes.append(vs)

        # print('orot',ls[6])
        # evaluate irot value from slopes for each shape
        # using figure 13 from the baseline report 1/20 as a standard for irot values
        if des == 'aIe' or des == 'aOe' or des == 'aM' or des == 'aOe' or des == 'aMe':
            if math.isclose(0.58, vslopes[0], abs_tol=tol):
                if vslopes[3] == float('inf'):
                    ls[6] = 0
                elif vslopes[3] == float('-inf'):
                    ls[6] = 3
            elif math.isclose(-0.58, vslopes[0], abs_tol=tol):
                if vslopes[1] == float('inf'):
                    ls[6] = 2
                elif vslopes[1] == float('-inf'):
                    ls[6] = 5
            elif vslopes[0] == float('-inf'):
                ls[6] = 1
            elif vslopes[0] == float('inf'):
                ls[6] = 4
        elif des == 'bI' or des == 'bIe' or des == 'bMe' or des == 'bOe':
            if vslopes[0] == 0.0:
                if vslopes[1] == float('-inf'):
                    ls[6] = 0
                elif vslopes[1] == float('inf'):
                    ls[6] = 3
            elif math.isclose(1.74, vslopes[0], abs_tol=tol):
                if vslopes[3] == float('inf'):
                    ls[6] = 1
                elif vslopes[3] == float('-inf'):
                    ls[6] = 4
            elif math.isclose(-1.74, vslopes[0], abs_tol=tol):
                if vslopes[2] == float('inf'):
                    ls[6] = 2
                elif vslopes[2] == float('-inf'):
                    ls[6] = 5
        elif des == 'cOe':
            if vslopes[0] == -0.0:
                ls[6] = 3
            # python doesn't actually differentiate the -0 and 0, so this doesn't trigger
            # i fixed it for b's, but c's slopes for 0 and 3 are the same, no way to differentiate
            # but at least rotation 0 is never used in the drawings.
            # some method to differentiate will be needed in future if it gets used
            elif vslopes[0] == 0.0:
                ls[6] = 0
            elif math.isclose(1.74, vslopes[0], abs_tol=tol):
                if vslopes[2] == float('inf'):
                    ls[6] = 4
                elif vslopes[2] == float('-inf'):
                    ls[6] = 1
            elif math.isclose(-1.74, vslopes[0], abs_tol=tol):
                if vslopes[1] == float('inf'):
                    ls[6] = 5
                elif vslopes[1] == float('-inf'):
                    ls[6] = 2
        elif des == 'dIe' or des == 'dOe':
            if vslopes[0] == float('inf'):
                ls[6] = 0
            elif vslopes[0] == float('-inf'):
                ls[6] = 3
            elif math.isclose(0.58, vslopes[0], abs_tol=tol):
                if vslopes[3] == float('inf'):
                    ls[6] = 2
                elif vslopes[3] == float('-inf'):
                    ls[6] = 5
            elif math.isclose(-0.58, vslopes[0], abs_tol=tol):
                if vslopes[4] == float('inf'):
                    ls[6] = 1
                elif vslopes[4] == float('-inf'):
                    ls[6] = 4
        elif des == 'gIe':
            if vslopes[0] == float('inf'):
                ls[6] = 0
            elif vslopes[0] == float('-inf'):
                ls[6] = 3
            elif math.isclose(0.59, vslopes[0], abs_tol=tol):
                if vslopes[1] == float('inf'):
                    ls[6] = 5
                elif vslopes[1] == float('-inf'):
                    ls[6] = 2
            elif math.isclose(-0.59, vslopes[0], abs_tol=tol):
                if vslopes[2] == float('inf'):
                    ls[6] = 4
                elif vslopes[2] == float('-inf'):
                    ls[6] = 1

    # if vslopes!=[]:
    #    print(des,ls[6],vslopes)

    # des=ls[3]

    # if des=='aIe' or des=='aOe' or des=='aM' or des=='aOe' or des=='aMe':

    return ls
# =============================================================================
# =============================================================================
# =========================Main Program========================================
# =============================================================================
# =============================================================================

layerstart = 1
layerend = 2
xmax = 5000#2000
ymax = 3000#2000
# radius
r = 40
d = r * math.cos(math.pi/6)
# board drawing or wagon drawing
#bow = 0
im2 = Image.new('RGB', (xmax, ymax), (256, 256, 256))
draw = ImageDraw.Draw(im2)
font = ImageFont.truetype('Keyboard.ttf',30)
#font = ImageFont.load_default()


# Draw Summary
# counters
i = 0
# maxcol=5
col = 0
# maxrow=7,7,7,8
row = 0
t = 0
maxrows = 20
x0 = 200
y0 = 120
colSpacing = 500
rowSpacing = 110

def wagonDrawer(wagonCounter, geomVersion, maxLinksDict = {}):
  
  row, col = 0, 0
  ySpaces = 0
  ySpaceExtra = 1.5 * r #1.5 * r #120
  nCharsPerGroup = 5
  nCharsPreCodes = 4
  for wagon in list(wagonCounter.keys()):
    
    if maxLinksDict != {}:
        maxLinksList = maxLinksDict[wagon]
    else:
        maxLinksList = []
        for i in wagonCounter:
            maxLinksList.append(0)

    # Remove x-over index 
    #wagonTemp = wagon[0:2] + wagon[3:]
    #wagonTemp = wagon[0:nCharsPreCodes-1] + wagon[nCharsPreCodes:]
    # Remove last 2 link indices
    wagonTemp = wagon[:-2]

    EW = wagonTemp[1]

    bow = 3 if wagonTemp[0] else 1
    #print(y0,row,col,ySpaces)
    x = x0 + colSpacing * col
    y = y0 + rowSpacing * row #+ ySpaces * ySpaceExtra
    #print('x',x,'y',y)
    #centers = [(x,y,wagonTemp[2],0,'False' if len(wagonTemp) > 3 else ('True' if wagonTemp[1] else 'False'))]
    centers = [(x,y,wagonTemp[4],0,'True' if wagonTemp[2] == 0 else 'False', maxLinksList[0])]
    # print(centers)
    #hexdraw(x,y,wagonTemp[2],0,1,'False' if len(wagonTemp) > 3 else ('True' if wagonTemp[1] else 'False'))
    angle = 0
    orient = 0
    if len(wagonTemp) > nCharsPreCodes + 2:
      codeGroups = [wagonTemp[i*nCharsPerGroup:(i+1)*nCharsPerGroup] for i in range((len(wagonTemp)+nCharsPreCodes-1)//(nCharsPerGroup))][1:] # Precodes are already taken care of above
      for i, codeGroup in enumerate(codeGroups):

        #drawEngine = 'True' if i == (len(codeGroups) - 1) and wagonTemp[1] else 'False'
        drawEngine = 'True' if wagonTemp[2] == (i + 1) else 'False' 
  
        #angle = (int(codeGroup[0]) - orient) % 6
        angle = (orient + int(codeGroup[2])) % 6
        #orient = (int(codeGroup[1]) - orient) % 6
        orient = (orient + int(codeGroup[3])) % 6
        x += 2 * d * math.cos(angle * math.pi / 3)
        y -= 2 * d * math.sin(angle * math.pi / 3)
  
        #if any(i in codeGroup[2] for i in ['a','b','g']):
        #  orient = (orient + int(codeGroup[0])) % 6
  
        orientAdj = 0
        if False and any(i in codeGroup[4] for i in ['a','b','d','g']):
          #orient = (orient + 4) % 6
          orientAdj = 4
          if codeGroup[4] == 'd':
            #orient = (orient + 1) % 6
            orientAdj += 1
        centers.append((x,y,codeGroup[4],(orient + orientAdj) % 6,drawEngine,maxLinksList[i + 1]))
  
    xMin = np.min([i[0] for i in centers])
    yMax = np.max([i[1] for i in centers])
    yMin = np.min([i[1] for i in centers])
    yRange = yMax - yMin
    ySpaces += math.floor(yRange / (1.5 * r)) # rowSpacing)
    if math.floor(yRange / (1.5 * r)) > 0: row += 2
    #ySpaces += ySpacesNew
    #print('ySpaces',ySpaces)
    #if centers[0][1] == yMax:
    centers = [(i[0] + centers[0][0] - xMin,i[1] + ySpaces * ySpaceExtra,i[2],i[3],i[4],i[5]) for i in centers]
    #print(centers)
    #print('-------------------------')
    #centers = [(i[0] + centers[0][0] - xMin,i[1] + ySpaces*ySpaceExtra,i[2],i[3],i[4]) for i in centers]
    # print(centers)
    for center in centers:
      hexdraw(bow,center[0],center[1],center[2],center[3],1,center[4],center[5],EW)
    
    centers.sort(key=lambda centers: centers[1],reverse=True)
 
    draw.text((50 + colSpacing * col,centers[0][1] + 10),str(wagonCounter.get(wagon)),font=font,fill='black')
    draw.text((50 + colSpacing * col,centers[0][1] + 40),''.join(str(i) for i in wagon),font=font,fill='black')
  
    row += 1
    if centers[0][1] > 0.8 * (ymax - y0):
      row = 0
      col += 1
      ySpaces = 0
  
  im2.save('output/wagonSummaries/WagonSummary_{}.jpg'.format(str(geomVersion)), quality=95)
