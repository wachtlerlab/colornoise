#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
This module contains functions generating colors with sml or rgb values;
The color generation can have subjective adjustments, only if a isoslant file exists.

With the last part of functions, you can also display a pretty color circle.

@author: yannansu
"""
import os
import numpy as np
from psychopy import visual, misc, event

import rgb2sml_copy
import filetools

"""load calibration file and make transformations"""

gray_level = 0.66  # this is determined from the calibration file (rgb2lms)

calib = rgb2sml_copy.calibration(rgb2sml_copy.openfile())  # Load the parameters of the calibration file

transf = rgb2sml_copy.transformation(calib.A0(),
                                     calib.AMatrix(),
                                     calib.Gamma())  # Creates an object transf that has as methods all the needed transformations

# get the gray color in the center of the color space
Csml = transf.center()
Crgb = transf.sml2rgb(Csml)

"""single colors"""


def gengray(Csml, dlum):  # generate gray colors by changing luminance
    gray = [Csml[0], Csml[1] * (1 + dlum), Csml[2] * (1 + dlum)]
    return gray


def gensml(theta, c=0.12, sscale=2.6, gray=Csml,
           unit='rad'):  # generate any color sml value given the angle - without subjectctive adjustment
    #  arguments:
    #  c as contrast (because it is isoluminant, so it equals to chromaticity now); current no larger than 0.155
    #  sscale just for better viewing -- usually no need to change
    #  gray can be changed by altering luminance; default gray Csml is from calibration file

    if unit != 'rad':
        theta = theta * 2 * np.pi / 360

    lmratio = 1 * gray[2] / gray[1]  # this ratio can be adjusted

    sml = [gray[0] * (1.0 + sscale * c * np.sin(theta)),
           gray[1] * (1.0 - (c / (1.0 + 1. / lmratio)) * np.cos(theta)),
           gray[2] * (1.0 + (c / (1.0 + lmratio)) * np.cos(theta))]

    return sml


def genrgb(theta, c=0.12, sscale=2.6, gray=Csml,
           unit='rad'):  # generate any color rgb value given the angle - without subjectctive adjustment

    rgb = transf.sml2rgb(gensml(theta, c, sscale, gray, unit))

    return rgb


def newcolor(theta, c=0.12, sscale=2.6, dlum=0, unit='rad',
             subject=None):  # generate any new color sml and rgb values - can have subjective adjustment; useful for generating colors on experiments
    # arguments:
    # dlum: relative change from the default gray color
    # subject: user name as string

    gray = gengray(Csml, dlum)

    if subject is not None:
        basepath = 'isolum/' + subject

        if os.path.isdir(basepath):
            for root, dirs, names in os.walk(basepath):  # show names also in subfolders
                for name in names:
                    if name.endswith('.isoslant'):
                        file = open(root + '/' + name, "r", encoding='utf-8')
                        lines = file.read().splitlines()

                        amplitude = filetools.readparam(lines, 'amplitude')
                        phase = filetools.readparam(lines, 'phase')
                        # offset = filetools.findparam(lines, 'offset')

                        # dlum = dlum + amplitude * np.sin(theta + phase) + offset
                        dlum = dlum + amplitude * np.sin(theta + phase)

                        # print("Error: No isoslant file is found! Results without subjective adjustment will be given!")
        else:
            print(
                "No subject is given/The given subject does not exist! Results without subjective adjustment will be given!")
    else:
        print("No subject... Results without subjective adjustment will be given!")

    tempgray = gengray(gray,
                       dlum)  # old-fashioned way: first move along luminance axis to the temporal gray and then find the desired color

    sml = gensml(theta, c, sscale, gray=tempgray, unit=unit)
    rgb = genrgb(theta, c, sscale, gray=tempgray, unit=unit)
    return sml, rgb


def displaycolor(rgb):
    win = visual.Window(size=[400, 400], allowGUI=True, color=rgb, colorSpace="rgb255")
    win.flip()
    print(win.color)
    event.waitKeys()
    win.close()


def gentheta(rgb, c=0.12, sscale=2.6, gray=Csml, unit='rad'):  # derive hue angle from rgb values
    sml = transf.rgb2sml(rgb)
    lmratio = 1 * gray[2] / gray[1]  # this ratio can be adjusted

    y = (sml[0] / gray[0] - 1.0) / (sscale * c)  # sin value
    x = (sml[2] / gray[2] - 1.0) * (1.0 + lmratio) / c  # cos value
    # x = (sml[1] / gray[1] - 1.0) * (1.0 + lmratio) / (- c * lmratio)
    theta = np.arctan2(y, x)

    if unit != 'rad':
        theta = 180 * theta / np.pi
        if theta < 0:
            theta = 360 + theta

    return theta

    # sml = [gray[0] * (1.0 + sscale * c * np.sin(theta)),
    #        gray[1] * (1.0 - c * np.cos(theta) * lmratio / (1.0 + lmratio)),
    #        gray[2] * (1.0 + c * np.cos(theta) / (1.0 + lmratio))]


"""color circle"""


def circolors(c=0.12, sscale=2.6, numStim=8):  # generate colors for color circle display

    theta = np.linspace(0, 2 * np.pi, numStim, endpoint=False)
    Msml = []
    for i_stim in range(numStim):
        Msml.append(gensml(theta[i_stim], c, sscale))

    Mrgb = np.empty(np.shape(Msml))
    for id in range(len(Msml)):
        Mrgb[id] = transf.sml2rgb(Msml[id])

    return Msml, Mrgb


def showcolorcircle(c=0.12, sscale=2.6, numStim=8):  # show the color circle

    _, Mrgb = circolors(c, sscale, numStim)

    winM = visual.Window(size=[800, 800], allowGUI=True, colorSpace="rgb255", color=Crgb)

    rectsize = 0.5 * winM.size[0] * 2 / numStim
    radius = 0.3 * winM.size[0]
    alphas = np.linspace(0, 360, numStim, endpoint=False)

    rect = visual.Rect(win=winM,
                       units="pix",
                       fillColorSpace="rgb255", lineColorSpace="rgb255",
                       width=int(rectsize), height=int(rectsize))

    for i_rect in range(numStim):
        rect.fillColor = Mrgb[i_rect]
        rect.lineColor = Mrgb[i_rect]
        rect.pos = misc.pol2cart(alphas[i_rect], radius)
        rect.draw()

    winM.flip()

    event.waitKeys()
    winM.close()


def alldisphue():
    """
    check what hue angle can be displayed in a 8-bit display and save the values in a *.npy file
    :return: all presented hue angles
    """
    import matplotlib.pyplot as plt

    theta = np.linspace(0, 360 - 1, 360)
    convt = [newcolor(x, unit='degree') for x in theta]
    rgb = [np.round(x[1]) for x in convt]
    diff = np.empty(len(rgb) - 1)

    for idx, val in enumerate(rgb):
        if idx == len(rgb) - 1:
            break
        diff[idx] = sum(abs(rgb[idx + 1] - val)) != 0

    fullrgb = np.empty((1000, 3), float)
    count = 0
    for idx, val in enumerate(rgb):
        if idx == len(rgb) - 1:
            break
        step = rgb[idx + 1] - val
        if sum(abs(step)) != 0:
            if sum(abs(step)) == 1:
                fullrgb[count] = val
                count += 1
            else:
                fullrgb[count] = val + [step[0], 0, 0]
                fullrgb[count + 1] = val + [0, step[1], 0]
                fullrgb[count + 2] = val + [0, 0, step[2]]
                count += 3

    seltheta = np.where(diff == 1)[0]

    # np.save('all-displayed-hue', seltheta)

    fig = plt.figure()
    plt.plot(diff)
    plt.title("if the hue can be presented on a 8-bit? ")
    plt.show()

    return rgb, fullrgb, diff, seltheta


"""example"""
# showcolorcircle(c=0.12, numStim=16)
# rgb,sml = newcolor(0, c=0.12, sscale=2.6, dlum=0, subject='test-abs')
# alldisphue()