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
import rgb2sml_plus
import filetools


class Generator:  # TODO: check the parameters
    def __int__(self, gray_level=0.66, c=0.12, sscale=2.6, unit='rad', depthBits=8, subject=None):
        self.gray_level = gray_level  # this is determined from the calibration file (rgb2lms)
        self.c = c
        self.sscale = sscale
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

    def gensml(self, theta,
               gray=None):  # generate any color sml value given the angle - without subjectctive adjustment
        #  arguments:
        #  c as contrast (because it is isoluminant, so it equals to chromaticity now); current no larger than 0.155
        #  sscale just for better viewing -- usually no need to change
        #  gray can be changed by altering luminance; default gray Csml is from calibration file
        c = self.c
        sscale = self.sscale
        unit = self.unit
        if unit != 'rad':
            theta = theta * 2 * np.pi / 360
        if gray is None:
            gray = self.Csml

        lmratio = 1 * gray[2] / gray[1]  # this ratio can be adjusted
        sml = [gray[0] * (1.0 + sscale * c * np.sin(theta)),
               gray[1] * (1.0 - c * np.cos(theta) * lmratio / (1.0 + lmratio)),
               gray[2] * (1.0 + c * np.cos(theta) / (1.0 + lmratio))]

        return sml

    def genrgb(self, theta,
               gray=None):  # generate any color rgb value given the angle - without subjectctive adjustment
        if gray is None:
            gray = self.Csml
        rgb = self.transf.sml2rgb(self.gensml(theta, gray))
        return rgb

    def newcolor(self, theta,
                 dlum=0):  # generate any new color sml and rgb values - can have subjective adjustment; useful for generating colors on experiments
        # arguments:
        # dlum: relative change from the default gray color
        # subject: user name as string
        # gray = [self.Csml[0], self.Csml[1] * (1 + dlum), self.Csml[2] * (1 + dlum)  # TODO: check whether it is needed 

        if self.subject is not None:
            basepath = 'isolum/' + self.subject

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
        # TODO: check whether it is needed or the newer version is better
        # tempgray = gengray(gray, dlum)  # old-fashioned way: first move along luminance axis to the temporal gray and then find the desired color

        tempgray = [self.Csml[0], self.Csml[1] * (1 + dlum), self.Csml[2] * (1 + dlum)]

        sml = self.gensml(theta, gray=tempgray)
        rgb = self.genrgb(theta, gray=tempgray)
        return sml, rgb

    def gentheta(self, rgb, gray=None):  # derive hur angle from rgb values
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

    def allvisiblehue(self, hue_res):
        """
        check what hue angle is visible in a 10-bit display
        :return: all visible hue angles
        """
        import matplotlib.pyplot as plt
        if self.depthBits != 10:
            raise ValueError("10-bit environment is not found!")
            exit(1)
        theta = np.linspace(0, 360 - 1, int(360 / hue_res))  # theta bin is 0.2 degree
        convt = [self.newcolor(x, self.subject) for x in theta]  # subject can be adjusted
        # rgb = [np.round(x[1]) for x in convt]
        rgb = [x[1] for x in convt]
        rgb_res = 1 / 2 ** 10  # resolution of 10bit in [0, 1] scale
        selrgb = []
        seltheta = []
        it = iter(list(range(0, len(rgb) - 2)))

        for idx in it:
            selrgb.append(rgb[idx])
            seltheta.append(rgb[idx])
            if sum(abs(rgb[idx] - rgb[idx + 1]) > rgb_res) == 0:  # skip the repeated RGB
                next(it)
            if sum(abs(rgb[idx] - rgb[idx + 2]) > rgb_res) == 0:
                next(it)
                next(it)

        np.save('config/config_10bit/colorlist/hue-list-10bit-res' + str(hue_res) + '-sub-' + self.subject, seltheta)
        np.save('config/config_10bit/colorlist/rgb-list-10bit-res' + str(hue_res) + '-sub-' + self.subject, selrgb)

        return rgb, selrgb, theta, seltheta


class Painter:
    def __int__(self, gray_level=0.66, c=0.12, sscale=2.6, unit='rad', depthBits=8):
        self.gray_level = gray_level  # this is determined from the calibration file (rgb2lms)
        self.c = c
        self.sscale = sscale
        self.unit = unit
        self.depthBits = depthBits  # 8 or 10-bit
        self.gen = Generator(gray_level=self.gray_level, c=self.c, sscale=self.sscale, unit=self.unit,
                             depthBits=self.depthBits)

        if self.depthBits == 8:
            self.colorSpace = "rgb255"
        elif self.depthBits == 10:
            self.colorSpace = "rgb"
        else:
            raise ValueError

    def displaycolor(self, rgb):
        win = visual.Window(size=[400, 400], allowGUI=True, bpc=(self.depthBits, self.depthBits, self.depthBits),
                            depthBits=self.depthBits, color=rgb, colorSpace=self.colorSpace)
        win.flip()
        print(win.color)
        event.waitKeys()
        win.close()

    """color circle"""

    def circolors(self, numStim=8):  # generate colors for color circle display
        theta = np.linspace(0, 2 * np.pi, numStim, endpoint=False)
        Msml = []
        for i_stim in range(numStim):
            Msml.append(self.gen.gensml(theta[i_stim]))

        Mrgb = np.empty(np.shape(Msml))
        for id in range(len(Msml)):
            Mrgb[id] = self.gen.transf.sml2rgb(Msml[id])

        return Msml, Mrgb

    def showcolorcircle(self, numStim=8):  # show the color circle

        _, Mrgb = self.circolors(numStim)

        winM = visual.Window(size=[800, 800], allowGUI=True, bpc=(self.depthBits, self.depthBits, self.depthBits),
                             depthBits=self.depthBits, colorSpace=self.colorSpace, color=self.gen.Crgb)

        rectsize = 0.5 * winM.size[0] * 2 / numStim
        radius = 0.3 * winM.size[0]
        alphas = np.linspace(0, 360, numStim, endpoint=False)

        rect = visual.Rect(win=winM,
                           units="pix",
                           fillColorSpace=self.colorSpace, lineColorSpace=self.colorSpace,
                           width=int(rectsize), height=int(rectsize))

        for i_rect in range(numStim):
            rect.fillColor = Mrgb[i_rect]
            rect.lineColor = Mrgb[i_rect]
            rect.pos = misc.pol2cart(alphas[i_rect], radius)
            rect.draw()

        winM.flip()

        event.waitKeys()
        winM.close()


"""example"""
# showcolorcircle(c=0.12, numStim=16)
# rgb,sml = newcolor(0, c=0.12, sscale=2.6, dlum=0, subject='test-abs')

# # generate hue-list and rgb-list
# rgb, selrgb, theta, seltheta = allvisiblehue(0.2)
# rgb, selrgb, theta, seltheta = allvisiblehue(0.5)
# rgb, selrgb, theta, seltheta = allvisiblehue(1.0)
