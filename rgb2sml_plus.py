#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 14:59:35 2019

This module contains a set of functions designed to read the data from a calibration file named as "  .rgb2lms"
Then, use this information to convert rgb values to sml values ( yeah, in that order)

@author: nicovattuone

Adapted on Fri Jun 26 10:55:20 2020
This module is adapted for both 8-bit and 10-bit color depth environment (Python 3.5 & 3.7)
by yannansu
"""

import os
from sys import exit
import numpy as np


# This function looks in the directory basepath the file ending with rgb2lms,
# its output is a string with the data in the file
def openfile():
    basepath = './config'
    for root, dirs, names in os.walk(basepath):  # show names also in subfolders
        for name in names:
            # print(os.path.join(root, name))
            if name.endswith(".rgb2lms"):
                file = open(root + '/' + name, "r", encoding='utf-8')
            # else:
            #  print("No rgb2lms file is found!")
            #  exit(1)
    return file.read()


# the calibration class will contain the information of the matrix necesary to do the transformation which is of the form,
# data is the string that receives from the function openfile() and then turns them to numpy variables
# (s,m,l) = A . (rˠ, gˠ, bˠ) +  A₀
class calibration():
    def __init__(self, data):
        self.data = data

    def A0(self):
        A0 = []
        a = self.data.split("\n")
        for j in range(len(a)):
            if a[j].strip().find("[A₀S, A₀M, A₀L]") != -1:  # strip(None) removes whitespace of the string
                for b in a[j + 1].strip().split(","):
                    A0.append(float(b))
        return np.array(A0)

    def AMatrix(self):
        A = []
        v = []
        a = self.data.split("\n")
        for j in range(len(a)):
            if a[j].strip().find("ArL, AgL, AbL") != -1:
                for k in range(1, 4):
                    for c in a[j + k].strip().split(","):
                        v.append(float(c))
                    A.append(v)
                    v = []
        return np.matrix(A)

    def Gamma(self):
        gamma = []
        a = self.data.split("\n")
        for j in range(len(a)):
            if a[j].strip().find("[rˠ, gˠ, bˠ]") != -1:
                for b in a[j + 1].strip().split(","):
                    gamma.append(float(b))
        return np.array(gamma)


# Transformation class will receive  the value of A₀, A and ˠ

class transformation():
    def __init__(self, A0, A, Gamma, depthBits=8):
        self.A = np.around(A, decimals=10)
        self.A0 = np.around(A0, decimals=10)
        self.Gamma = np.around(Gamma, decimals=10)
        self.InvA = np.linalg.pinv(np.around(A, decimals=10))  # compute the inverse A
        self.depthBits = depthBits  # 8 or 10 bit color depth; default is 8

    #  Converts  (r,g,b) to (s,m,l)
    def rgb2sml(self, rgb):  # value in each gun should be from [-1, 1]
        if self.depthBits == 8:
            rgb = (rgb[0] % 256, rgb[1] % 256, rgb[2] % 256)
            c = np.array(rgb)
        elif self.depthBits == 10:
            c = (np.array(
                rgb) + 1) / 2 * 1023  # The 10-bit modification is the rescaling into [-1,1] as Psychopy requires in colorSpace 'rgb'
        else:
            raise ValueError
        if len(c) > 3:
            c = np.resize(c, 3)
        return np.squeeze(np.asarray(np.dot(self.A, np.power(c, self.Gamma)))) + self.A0

    #  Converts  (s,m,l) to (r,g,b)    
    def sml2rgb(self, sml):
        c = np.array(sml)
        rgb = np.power(np.abs(np.squeeze(np.asarray(np.dot(self.InvA, (c - self.A0))))), 1 / (self.Gamma))
        if self.depthBits == 8:
            if rgb.any() > 255:
                print("transformed values are larger than 255!")
                exit(1)
            np_rgb = np.array(rgb)
        elif self.depthBits == 10:
            np_rgb = np.array(rgb) % 1024 / 1023 * 2 - 1  # scale to [-1, 1] used in Psychopy 'rgb' color space
        else:
            raise ValueError
        return np_rgb

    # def truncsml(self, sml):
    #     return self.rgb2sml(self.sml2rgb(sml))

    def center(self):
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
        c = (vertex8 + vertex1) * 0.6 # / 2
        return np.array(c)

    def isindomain(self, sml):  # it checks if the transformation can work
        sml = np.array(sml)
        s1 = np.sum(np.less(np.squeeze(np.asarray(np.dot(self.InvA, (sml - self.A0)))),
                            0))  # it checks if the transformation is invertible
        if self.depthBits == 8:
            s2 = np.sum(np.greater(np.rint(self.sml2rgb(sml)), 255))  # it checks if the rgb are larger than 255
        elif self.depthBits == 10:
            s2 = np.sum(np.greater(np.rint(self.sml2rgb(sml)), 1))  # it checks if the rgb are larger than 1
        else:
            raise ValueError
        return (s1 + s2 == 0)  # returning True means it can work well

    def deltasml(self, sml):
        return (self.Gamma * np.squeeze(
            np.asarray(np.dot(self.A, np.power(np.abs(np.array(self.sml2rgb(sml))), self.Gamma - 1)))))

    def listS(self):
        c = np.array(self.center())
        listS = []
        while (self.isindomain(c - 0.2 * np.array((self.deltasml(c)[0], 0, 0)))):
            c = c - 0.2 * np.array((self.deltasml(c)[0], 0, 0))

        while (self.isindomain(c + 0.2 * np.array((self.deltasml(c)[0], 0, 0)))):
            caux = c
            c = c + 0.2 * np.array((self.deltasml(c)[0], 0, 0))
            if np.sum(np.abs(self.sml2rgb(c) - self.sml2rgb(caux))) > 5:
                return listS
                break
            elif (np.sum(self.sml2rgb(c) != self.sml2rgb(caux)) > 0 and self.truncsml(c)[0] - self.truncsml(caux)[
                0] > 0.001):
                listS.append(self.sml2rgb(c))

        return listS

    def listM(self):
        c = np.array(self.center())
        listM = []
        while (self.isindomain(c + 0.1 * np.array((0, self.deltasml(c)[1], 0)))):
            c = c + 0.1 * np.array((0, self.deltasml(c)[1], 0))
        c = c - 0.1 * np.array((0, self.deltasml(c)[1], 0))

        while (self.isindomain(c - 0.1 * np.array((0, self.deltasml(c)[1], 0)))):
            caux = c
            c = c - 0.1 * np.array((0, self.deltasml(c)[1], 0))
            if np.sum(np.abs(self.sml2rgb(c) - self.sml2rgb(caux))) > 5:
                listM.sort(key=lambda x: self.rgb2sml(x)[1])
                return listM
                break
            elif (np.sum(self.sml2rgb(c) != self.sml2rgb(caux)) > 0):
                listM.append(np.trunc(self.sml2rgb(c)))
        listM.sort(key=lambda x: self.rgb2sml(x)[1])

        return listM

    def listL(self):
        c = np.array(self.center())
        listL = []
        while (self.isindomain(c + 0.1 * np.array((0, 0, self.deltasml(c)[2])))):
            c = c + 0.1 * np.array((0, 0, self.deltasml(c)[2]))
        c = c - 0.1 * np.array((0, 0, self.deltasml(c)[2]))

        while (self.isindomain(c - 0.1 * np.array((0, 0, self.deltasml(c)[2])))):
            caux = c
            c = c - 0.1 * np.array((0, 0, self.deltasml(c)[2]))
            if np.sum(np.abs(self.sml2rgb(c) - self.sml2rgb(caux))) > 5:
                listL.sort(key=lambda x: self.rgb2sml(x)[2])
                return listL
                break
            elif (np.sum(np.trunc(self.sml2rgb(c)) != np.trunc(self.sml2rgb(caux))) > 0):
                listL.append(np.trunc(self.sml2rgb(c)))
        listL.sort(key=lambda x: self.rgb2sml(x)[2])

        return listL

    def disp(self):  # I create this...
        gray = np.array(self.center())
        lum = gray[1] + gray[2]
        cm = gray[1] / lum
        cl = gray[2] / lum
        disp = np.linalg.norm(self.deltasml(gray)) * np.array((0, -cm, cl))
        return disp

    def listLmM(self):  # list all l-m values
        gray = np.array(self.center())
        lum = gray[1] + gray[2]
        cm = gray[1] / lum
        cl = gray[2] / lum
        c = np.array(self.center())
        listLmM = []
        disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, -cm, cl))
        while (self.isindomain(c + disp)):
            c = c + disp
            disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, -cm, cl))
        c = c - disp

        while (self.isindomain(c - disp)):
            caux = c
            c = c - disp
            disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, -cm, cl))
            if np.sum(np.abs(self.sml2rgb(c) - self.sml2rgb(caux))) > 5:
                listLmM.sort(key=lambda x: (self.rgb2sml(x)[2]))
                return listLmM
                break
            elif (np.sum(np.trunc(self.sml2rgb(c)) != np.trunc(self.sml2rgb(caux))) > 0):
                listLmM.append(np.trunc(self.sml2rgb(c)))
        listLmM.sort(key=lambda x: (self.rgb2sml(x)[2]))
        return listLmM

    def listLpM(self):  # list all l+m values
        gray = np.array(self.center())
        lum = gray[1] + gray[2]
        cm = gray[1] / lum
        cl = gray[2] / lum
        c = np.array(self.center())
        listLpM = []
        disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, cm, cl))
        while (self.isindomain(c + disp)):
            c = c + disp
            disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, cm, cl))
        c = c - disp

        while (self.isindomain(c - disp)):
            caux = c
            c = c - disp
            disp = 0.1 * np.linalg.norm(self.deltasml(c)) * np.array((0, cm, cl))
            if np.sum(np.abs(self.sml2rgb(c) - self.sml2rgb(caux))) > 5:
                listLpM.sort(key=lambda x: (self.rgb2sml(x)[2] * cl + self.rgb2sml(x)[1] * cm))
                return listLpM
                break
            elif (np.sum(np.trunc(self.sml2rgb(c)) != np.trunc(self.sml2rgb(caux))) > 0):
                listLpM.append(np.trunc(self.sml2rgb(c)))
        listLpM.sort(key=lambda x: (self.rgb2sml(x)[2] * cl + self.rgb2sml(x)[1] * cm))

        return listLpM

    def changeM(self, rgb, deltaM):
        aux = self.rgb2sml(rgb) + np.array([0, deltaM, 0])
        return (self.sml2rgb(aux))

    def changeL(self, rgb, deltaL):
        aux = self.rgb2sml(rgb) + np.array([0, 0, deltaL])
        return (self.sml2rgb(aux))

    def changeLmM(self, rgb, deltaLmM):
        gray = np.array(self.center())
        aux = self.rgb2sml(rgb) + np.array([0, -gray[1], gray[2]]) * deltaLmM
        return (self.sml2rgb(aux))

    def sml2LmM(self, sml):
        gray = np.array(self.center())
        lum = gray[1] + gray[2]
        return ((sml[2] - gray[2]) / gray[2])

    def topS(self):
        c = np.array(self.center())
        i = 0
        while (self.isindomain(c + np.array((self.deltasml(c)[0], 0, 0)))):
            c = c + np.array((self.deltasml(c)[0], 0, 0))
            print(c)
            print(self.sml2rgb(c))

        print(i)
        return (c[0])

    def botS(self):
        c = np.array(self.center())
        while (self.isindomain(c - np.array((self.deltasml(c)[0], 0, 0)))):
            c = c - np.array((self.deltasml(c)[0], 0, 0))

        return (c[0])

    def changeS(self, rgb, deltaS):
        aux = self.rgb2sml(rgb) + [deltaS, 0, 0]
        return (self.sml2rgb(aux))
