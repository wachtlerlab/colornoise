#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

"""
This module generates sml and RGB values with hue angles on an iso-luminance plane, and vice versa.
Main module: ColorPicker

@author: yannansu
"""
import os
import numpy as np
from psychopy import visual, misc, event
import config_tools
import warnings
import sys


def read_calib():
    """
    Load and read calibration outputs from *.rgb2lms file.

    :return:
    """
    gray_level = 0
    A0 = []
    A = []
    v = []
    Gamma = []
    basepath = './config'
    file_num = 0
    for root, dirs, names in os.walk(basepath):  # show names also in subfolders
        for name in names:
            if name.endswith(".rgb2lms"):
                file_num += 1
                file = open(root + '/' + name, "r", encoding='utf-8')
                lines = file.read().splitlines()

    if file_num < 1:
        sys.exit('No calibration file is found.')
    if file_num > 1:
        sys.exit('Multiple calibration files are found. Please specify one!')
    else:
        for lidx, line in enumerate(lines):
            if line.lstrip().find('gray-level') != -1:
                gray_level = float(line.strip().split(": ")[1])
            if line.lstrip().find("[A₀S, A₀M, A₀L]") != -1:  # strip(None) removes whitespace of the string
                for b in lines[lidx + 1].strip().split(","):
                    A0.append(float(b))
            if line.lstrip().find("ArL, AgL, AbL") != -1:
                for k in range(1, 4):
                    for c in lines[lidx + k].strip().split(","):
                        v.append(float(c))
                    A.append(v)
                    v = []
            if line.lstrip().find("[rˠ, gˠ, bˠ]") != -1:
                for b in lines[lidx + 1].strip().split(","):
                    Gamma.append(float(b))

    return gray_level, np.array(A0), np.array(A), np.array(Gamma)


class ColorPicker:
    def __init__(self, c=0.15, sscale=2.6, unit='rad', depthBits=8, subject=None):
        """
        Color Picker for generating sml and RGB values with hue angles on an iso-luminance plane.

        Advanced features:
            - switch color depths
            - adjust the iso-luminance plane for single subjects
            - generate display-realizable hue lists
            - display a color circle

        :param c:          contrast (i.e. chromaticity since we use iso-luminance), less than 0.16 (tested on VPixx); default is 0.15
        :param sscale:     chromatic scaling along S-axis relative to L-M axis to make all stimuli look more salient; default is 2.6
        :param unit:       hue angle unit: radian[default] or degree
        :param depthBits:  color depth: 8[default] or 10
        :param subject:    perform subjective adjustment if not None. Subject isolum files will be searched and used.
        """
        self.gray_level, A0, A, Gamma = read_calib()
        self.A0 = np.around(A0, decimals=10)
        self.A = np.around(A, decimals=10)
        self.Gamma = np.around(Gamma, decimals=10)
        self.c = c
        self.sscale = sscale
        self.unit = unit
        self.depthBits = depthBits  # 8 or 10-bit
        if self.depthBits == 8:
            self.colorSpace = "rgb255"
        elif self.depthBits == 10:
            self.colorSpace = "rgb"
        else:
            raise ValueError
        self.subject = subject

    def rgb2sml(self, rgb):
        """
        Transfrom from rgb to sml.

        """
        if self.depthBits == 8:
            rgb = (rgb[0] % 256, rgb[1] % 256, rgb[2] % 256)
            c = np.array(rgb)
        elif self.depthBits == 10:
            c = (np.array(rgb) + 1) / 2 * 1023  # rescaling [0, 1] into [-1,1] as Psychopy requires in colorSpace 'rgb'
        else:
            raise ValueError
        if len(c) > 3:
            c = np.resize(c, 3)
        return np.squeeze(np.asarray(np.dot(self.A, np.power(c, self.Gamma)))) + self.A0

    def sml2rgb(self, sml):
        """
        Transfrom from sml to rgb.
        """
        InvA = np.linalg.pinv(np.around(self.A, decimals=10))  # compute the inverse A

        c = np.array(sml)
        rgb = np.power(np.abs(np.squeeze(np.asarray(np.dot(InvA, (c - self.A0))))), 1 / self.Gamma)
        if self.depthBits == 8:
            if rgb.any() > 255:
                sys.exit("transformed values are out of range!")
            np_rgb = np.array(rgb)
        elif self.depthBits == 10:
            np_rgb = np.array(rgb) % 1024 / 1023 * 2 - 1  # scale to [-1, 1] used in Psychopy 'rgb' color space
            if abs(np_rgb.any()) > 1:
                sys.exit("transformed values are out of range!")
        else:
            raise ValueError
        return np_rgb

    def center(self, gray_level=None):
        """
        Calculate sml value of the central gray color based on the gray level (from 0 to 1.0).
        """
        if gray_level is None:
            gray_level = self.gray_level
        vertex1 = self.A0
        if self.depthBits == 8:
            vertex2 = self.rgb2sml((255, 0, 0))  # red
            vertex3 = self.rgb2sml((0, 255, 0))  # green
            vertex4 = self.rgb2sml((0, 0, 255))  # blue
        elif self.depthBits == 10:
            vertex2 = self.rgb2sml((1, -1, -1))  # red
            vertex3 = self.rgb2sml((-1, 1, -1))  # green
            vertex4 = self.rgb2sml((-1, -1, 1))  # blue
        else:
            raise ValueError
        vertex8 = vertex2 + vertex3 + vertex4
        c = (vertex8 + vertex1) * gray_level
        return np.array(c)

    def newcolor(self, theta, iris=True):
        """
        Generate any new color sml and rgb values based on a hue angle - can have subjective adjustment.
        """

        sub_dlum = 0
        isoslant_file = 0

        if self.subject is not None:
            basepath = 'isolum/' + self.subject

            if os.path.isdir(basepath):
                for root, dirs, names in os.walk(basepath):
                    for name in names:
                        if name.endswith('.isoslant'):
                            isoslant_file += 1
                            filepath = basepath + '/' + name
                            iso_dl = config_tools.read_value(filepath, ['dl'], sep=':')
                            iso_phi = config_tools.read_value(filepath, ['phi'], sep=':')

                            # sub_dlum += iso_dl * np.sin(theta + iso_phi)  # this is incorrect!

                            # correct the calculation as it in iris-tool:
                            sub_dlum += iso_dl * (np.cos(theta) * np.cos(iso_phi) +
                                                  np.sin(theta) * np.sin(iso_phi))
                            # print(str(theta) + ': ' + str(sub_dlum))
            if isoslant_file < 1:
                warnings.warn("No isoslant file is found for this subject.")
            if isoslant_file > 1:
                sys.exit('Multiple isoslant files are found. Please specify one!')
        else:
            warnings.warn("No subjective adjustment is requested.")

        sub_gray = self.center(gray_level=self.gray_level + sub_dlum)

        if self.unit != 'rad':
            theta = theta * 2 * np.pi / 360

        lmratio = 1 * sub_gray[2] / sub_gray[1]  # this ratio can be adjusted

        if iris is True:
            # TODO: discuss and understand the transformation used in iris-tool dkl::iso_lum
            sml = [sub_gray[0] * (1.0 + self.sscale * self.c * np.sin(theta)),
                   sub_gray[1] * (1.0 - self.c / (1.0 + 1 / lmratio) * np.cos(theta)),
                   sub_gray[2] * (1.0 + self.c / (1.0 + lmratio) * np.cos(theta))]
        else:
            sml = [sub_gray[0] * (1.0 + self.sscale * self.c * np.sin(theta)),
                   sub_gray[1] * (1.0 + self.c * np.cos(theta) * (1.0 - lmratio)),
                   sub_gray[2] * (1.0 + self.c * np.cos(theta) * (1.0 - 1 / lmratio))]

        rgb = self.sml2rgb(sml)

        return sml, rgb

    def gencolorlist(self, hue_res):
        """
        Generate colors that are realizable in a 10-bit display and save them in a color list.

        :param hue_res: the resolution of hue angles, i.e. hue angle bins
        :return: all rgb, realizable rgb,
                 all theta, realizable theta
        """
        if self.depthBits != 10:
            sys.exit("The current depthBits is NOT 10-bit!")

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
        Simply fill a window with the color RGB you want to dislplay.

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
        Generate colors for a color circle.

        """
        theta = np.linspace(0, 2 * np.pi, numStim, endpoint=False)

        Msml = []
        Mrgb = []
        for t in theta:
            sml, rgb = self.newcolor(theta=t)
            Msml.append(sml)
            Mrgb.append(rgb)

        return Msml, Mrgb

    def showcolorcircle(self, numStim=16):  # show the color circle
        """
        Draw and paint a color circle.

        """
        _, Mrgb = self.circolors(numStim)

        winM = visual.Window(size=[1400, 1400], allowGUI=True, bpc=(self.depthBits, self.depthBits, self.depthBits),
                             depthBits=self.depthBits, colorSpace=self.colorSpace, color=self.sml2rgb(self.center()))

        rectsize = 0.2 * winM.size[0] * 2 / numStim
        radius = 0.1 * winM.size[0]
        alphas = np.linspace(0, 360, numStim, endpoint=False)

        rect = visual.Rect(win=winM,
                           units="pix",
                           width=int(rectsize), height=int(rectsize))
        for i_rect in range(numStim):
            rect.fillColorSpace = self.colorSpace
            rect.lineColorSpace = self.colorSpace
            rect.fillColor = Mrgb[i_rect]
            rect.lineColor = Mrgb[i_rect]
            rect.pos = misc.pol2cart(alphas[i_rect], radius)
            rect.draw()

        winM.flip()

        event.waitKeys()
        winM.close()


"example: to show color circle"
# ColorPicker(depthBits=8, subject=None).showcolorcircle(numStim=16)

"example: to generate hue-list and rgb-list"
# ColorPicker(depthBits=10).gencolorlist(0.2)
# ColorPicker(depthBits=10).gencolorlist(0.5)
# ColorPicker(depthBits=10).gencolorlist(1.0)

