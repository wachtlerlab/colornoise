#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
THis module generates sml and RGB values with hue angles on an iso-luminance plane, and vice versa.
Main module: ColorPicker

@author: yannansu
"""
import os
import numpy as np
from psychopy import visual, misc, event
import rgb2sml_plus
import config_tools
import warnings


class ColorPicker:
    def __init__(self, gray_level=0.66, c=0.12, sscale=2.6, unit='rad', depthBits=8, subject=None):
        """
        Color Picker for generating sml and RGB values with hue angles on an iso-luminance plane, and vice versa.

        Advanced features:
            - switch color depths;
            - adjust the iso-luminance plane for single subjects;
            - generate display-realizable hue lists
            - display a color circle

        :param gray_level: default is 0.66
        :param c: contrast (i.e. chromaticity since we use iso-luminance); no larger than 0.155; default is 0.12
        :param sscale: just for better viewing, usually no need to change; default is 2.6
        :param unit: hue angle unit: radian[default] or degree
        :param depthBits: color depth: 8[default] or 10 
        :param subject: perform subjective adjustment if not None. Subject isolum files will be searched and used.
        """
        self.gray_level = gray_level  # this is determined from the calibration file (rgb2lms)
        self.c = c
        self.sscale = sscale  # 
        self.unit = unit
        self.depthBits = depthBits  # 8 or 10-bit
        self.subject = subject
        """load calibration file and make transformations"""
        self.calib = rgb2sml_plus.calibration(rgb2sml_plus.openfile())  # Load the parameters of the calibration file
        self.transf = rgb2sml_plus.transformation(self.calib.A0(),
                                                  self.calib.AMatrix(),
                                                  self.calib.Gamma(),
                                                  self.depthBits)  # Creates an object transf that has as methods all the needed transformations
        self.Csml = self.transf.center()
        self.Crgb = self.transf.sml2rgb(self.Csml)

        if self.depthBits == 8:
            self.colorSpace = "rgb255"
        elif self.depthBits == 10:
            self.colorSpace = "rgb"
        else:
            raise ValueError

    def gengray(self, gray_sml, dlum):
        """
        Change gray colors by changing luminance
        :param gray_sml:  gray color sml
        :param dlum:      change in luminance
        :return:          new gray color sml
        """
        gray = [gray_sml[0], gray_sml[1] * (1 + dlum), gray_sml[2] * (1 + dlum)]
        return gray

    def gensml(self, theta, gray=None):
        """
        Generate any color sml value given the angle - WITHOUT subjective adjustment.
        :param theta: hue angle
        :param gray: alternative gray sml values if not None
        :return: sml values
        """
        if self.unit != 'rad':
            theta = theta * 2 * np.pi / 360
        if gray is None:
            gray = self.Csml

        lmratio = 1 * gray[2] / gray[1]  # this ratio can be adjusted
        sml = [gray[0] * (1.0 + self.sscale * self.c * np.sin(theta)),
               gray[1] * (1.0 - self.c * np.cos(theta) * lmratio / (1.0 + lmratio)),
               gray[2] * (1.0 + self.c * np.cos(theta) / (1.0 + lmratio))]
        return sml

    def genrgb(self, theta, gray=None):
        """
        Generate any color RGB value given the angle - WITHOUT subjective adjustment.
        :param theta: hue angle
        :param gray: alternative gray sml values if not None
        :return: RGB values
        """
        if gray is None:
            gray = self.Csml
        rgb = self.transf.sml2rgb(self.gensml(theta, gray))
        return rgb

    def newcolor(self, theta, dlum=0):
        """
        Generate any new color sml and rgb values - can have subjective adjustment.
        :param theta: hue angle (radian[default] or degree)
        :param dlum: relative luminance change from the default gray color
        :return: sml and grb values
        """
        gray = self.gengray(self.Csml, dlum)

        if self.subject is not None:
            basepath = 'isolum/' + self.subject

            if os.path.isdir(basepath):
                for root, dirs, names in os.walk(basepath):  # show names also in subfolders
                    for name in names:
                        if name.endswith('.isoslant'):
                            filepath = basepath + '/' + name
                            # amplitude = config_tools.read_value(filepath, ['amplitude'], sep='=')
                            # phase = config_tools.read_value(filepath, ['phase'], sep='=')

                            amplitude = config_tools.read_value(filepath, ['dl'], sep=':')  # for iris-isoslant data
                            phase = config_tools.read_value(filepath, ['phi'], sep=':')

                            # offset = ParReader(name).find_param(lines, 'offset', '=')
                            # offset = filetools.findparam(lines, 'offset')

                            # sub_dlum = dlum + amplitude * np.sin(theta + phase) + offset
                            sub_dlum = dlum + amplitude * np.sin(theta + phase)
            else:
                sub_dlum = 0
                warnings.warn("No isoslant file is found for this subject! "
                              "Results without subjective adjustment will be given.")
        else:
            sub_dlum = 0
            warnings.warn("No subjective adjustment is requested. "
                          "Results without subjective adjustment will be given.")

        tempgray = self.gengray(gray, sub_dlum)  # first move along luminance axis to the temporal gray and then find the desired color
        
        sml = self.gensml(theta, gray=tempgray)
        rgb = self.genrgb(theta, gray=tempgray)
        return sml, rgb

    def gentheta(self, rgb, gray=None):  
        """
        Calculate hue angle given RGB values
        :param rgb: RGB values
        :param gray: alternative gray RGB values if not None
        :return: theta (in radian or degree, depending on the class init)
        """
        c = self.c
        sscale = self.c
        if gray is None:
            gray = self.Csml
        sml = self.transf.rgb2sml(rgb)
        lmratio = 1 * gray[2] / gray[1]  # this ratio can be adjusted

        y = (sml[0] / gray[0] - 1.0) / (sscale * c)  # sin value
        x = (sml[2] / gray[2] - 1.0) * (1.0 + lmratio) / c  # cos value
        x = (sml[1] / gray[1] - 1.0) * (1.0 + lmratio) / (- c * lmratio)
        theta = np.arctan2(y, x)

        if self.unit != 'rad':
            theta = 180 * theta / np.pi
            if theta < 0:
                theta = 360 + theta

        return theta
        # sml = [gray[0] * (1.0 + sscale * c * np.sin(theta)),
        #        gray[1] * (1.0 - c * np.cos(theta) * lmratio / (1.0 + lmratio)),
        #        gray[2] * (1.0 + c * np.cos(theta) / (1.0 + lmratio))]

    def gencolorlist(self, hue_res):
        """
        Generate colors that are realizable in a 10-bit display and save them in a color list
        :param hue_res: the resolution of hue angles, i.e. hue angle bins
        :return: all rgb, realizable rgb,
                 all theta, realizable theta
        """
        if self.depthBits != 10:
            raise ValueError("The current depthBits is NOT 10-bit!")
            exit(1)

        theta = np.linspace(0, 360 - hue_res, int(360 / hue_res))
        convt = [self.newcolor(theta=x) for x in theta]
        rgb = [x[1] for x in convt]
        rgb_res = 1 / 2 ** 10  # resolution of 10bit in [0, 1] scale
        selrgb = []
        seltheta = []
        it = iter(list(range(0, len(rgb) - 2)))

        for idx in it:
            selrgb.append(rgb[idx])
            seltheta.append(theta[idx])
            if sum(abs(rgb[idx] - rgb[idx + 1]) > rgb_res) == 0:  # skip the repeated RGB
                next(it)
            if sum(abs(rgb[idx] - rgb[idx + 2]) > rgb_res) == 0:
                next(it)
                next(it)

        subpath = 'config/colorlist/' + self.subject
        if not os.path.exists(subpath):
            os.makedirs(subpath)
        np.save(subpath + '/hue-list-10bit-res' + str(hue_res) + '-sub-' + str(self.subject), seltheta)
        np.save(subpath + '/rgb-list-10bit-res' + str(hue_res) + '-sub-' + str(self.subject), selrgb)

        return rgb, selrgb, theta, seltheta

    def displaycolor(self, rgb):
        """
        Simple fill a window will the color RGB you want to dislplay
        :param rgb: RGB values
        """
        win = visual.Window(size=[400, 400], allowGUI=True, bpc=(self.depthBits, self.depthBits, self.depthBits),
                            depthBits=self.depthBits, color=rgb, colorSpace=self.colorSpace)
        win.flip()
        print(win.color)
        event.waitKeys()
        win.close()

    def circolors(self, numStim):
        """
        Generate colors for a color circle
        :param numStim: the number of colors in the color circle
        :return: the sml and RGB of all colors in the color circle
        """
        theta = np.linspace(0, 2 * np.pi, numStim, endpoint=False)
        Msml = []
        for i_stim in range(numStim):
            Msml.append(self.gensml(theta[i_stim]))

        Mrgb = np.empty(np.shape(Msml))
        for id in range(len(Msml)):
            Mrgb[id] = self.transf.sml2rgb(Msml[id])

        return Msml, Mrgb

    def showcolorcircle(self, numStim=8):  # show the color circle
        """
        Draw and paint a color circle
        :param numStim: the number of colors in the color circle
        """
        _, Mrgb = self.circolors(numStim)

        winM = visual.Window(size=[800, 800], allowGUI=True, bpc=(self.depthBits, self.depthBits, self.depthBits),
                             depthBits=self.depthBits, colorSpace=self.colorSpace, color=self.Crgb)

        rectsize = 0.5 * winM.size[0] * 2 / numStim
        radius = 0.3 * winM.size[0]
        alphas = np.linspace(0, 360, numStim, endpoint=False)

        rect = visual.Rect(win=winM,
                           units="pix",
                           width=int(rectsize), height=int(rectsize))
        for i_rect in range(numStim):
            rect.fillColorSpace=self.colorSpace
            rect.lineColorSpace=self.colorSpace
            rect.fillColor = Mrgb[i_rect]
            rect.lineColor = Mrgb[i_rect]
            rect.pos = misc.pol2cart(alphas[i_rect], radius)
            rect.draw()

        winM.flip()

        event.waitKeys()
        winM.close()


"example: to show color circle"
# ColorPicker(depthBits=8).showcolorcircle(numStim=8)+

"example: to generate hue-list and rgb-list"
# ColorPicker(depthBits=10).gencolorlist(0.2)
# ColorPicker(depthBits=10).gencolorlist(0.5)
# ColorPicker(depthBits=10).gencolorlist(1.0)
