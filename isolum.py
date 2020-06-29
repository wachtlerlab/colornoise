#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from psychopy import visual, core, event
import os
import rgb2sml_plus
import colorpalette
from genconfig import ParReader
import filetools

"""get user information"""

def userinfo(path='/'):
    from psychopy import gui
    import time

    dlg = gui.Dlg()
    dlg.addField("Subject ID:")
    dlg.show()

    user = dlg.data[0]
    id = time.strftime("%Y%m%dT%H%M", time.localtime())  # add the current date
    os.makedirs(path + user)  # create a new folder named by user name in current path
    return user, id


user, id = userinfo(path='isolum/')
path = 'isolum/' + user


"""load calibration file and make transformations"""

info = rgb2sml_plus.openfile().splitlines()

calibinfo = info[0:2] + info[7:17]

calib = rgb2sml_plus.calibration(rgb2sml_plus.openfile())  # Load the parameters of the calibration file

transf = rgb2sml_plus.transformation(calib.A0(),
                                     calib.AMatrix(),
                                     calib.Gamma())  # Creates an object transf that has as methods all the needed transformations

gray_level = 0.66  # this is determined from the calibration file (rgb2lms)

# get the gray color in the center of the color space
Csml = colorpalette.Csml
Crgb = colorpalette.Crgb

win = visual.Window(unit='pix', size=[1200, 1200], allowGUI=True, colorSpace="rgb255", color=Crgb, fullscr=True)



"""main function: isoslant"""

def isoslant(c, r):


    def isodata(theta, numStim, shownum, lim=0.02, refresh=60):
        # baseC: basic color angle (picked from the color circle)
        # lim: the limit of luminance contrast you can reach; for scaling the mouse movement; or understood as mouse gain  <------------- can be adjusted
        # refresh: refresh rate of the monitor

        keep = 2  # each stimulus lasts 4 frames; each frame last for 1/refresh second
        freq = refresh / keep

        rect = visual.Rect(win, pos=[0, 0], width=0.35, height=0.5, fillColorSpace="rgb255", lineColorSpace="rgb255")
        rect.fillColor = colorpalette.gensml(theta, c=c, sscale=2.6, gray=Csml, unit='rad')
        rect.lineColor = rect.fillColor

        text = visual.TextStim(win, text=str(shownum) + ' of ' + str(numStim) + ' stimuli at ' + str(freq) + 'Hz',
                               pos=[-0.7, 0.95], height=0.03)

        mouse = event.Mouse(win=win, newPos=[0, 0], visible=False)
        frameN = 0

        while True:
            if frameN % (2 * keep) < keep:

                mouse_X, _ = mouse.getPos()  # get the current position of mouse as ratio: 1 as right edge, -1 as left edge
                dlum = - mouse_X * lim  # the change of luminance: move left -> brighter, move right -> darker
                # rect.fillColor = transf.sml2rgb([baseC[0], (1 + dlum) * baseC[1], (1 + dlum) * baseC[2]])
                refgray = colorpalette.gengray(Csml, dlum)

                rect.fillColor = transf.sml2rgb(colorpalette.gensml(theta, c=c, sscale=2.6, gray=refgray, unit='rad'))
                rect.lineColor = rect.fillColor

                rect.draw()

                if event.getKeys('space'):
                    # dlum = gray_level * (1 + dlum)
                    win.close()
                    return dlum
                    break

            text.draw()
            win.flip()

            frameN += 1

    """fit to get parameters for forming an iso-luminance plane"""

    def fitiso(filename):
        from scipy import optimize

        stim, res = np.loadtxt(filename, skiprows=15, unpack=True)

        # def fitter(x, amp, phi, offset=0):
        #     return amp * np.sin(x + phi) + offset

        def fitter(x, amp, phi):
            return amp * np.sin(x + phi)

        params, _ = optimize.curve_fit(fitter, stim, res)
        return stim, res, params

    # Msml, Mrgb = colorpalette.circolors(c=c, sscale=2.6, numStim=8)

    """run the flicker for all colors"""
    response = []
    stimulus = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    randstim = np.random.permutation(np.repeat(stimulus, r))
    # doublestim = np.random.permutation(list(zip(np.repeat(stimulus, 2),
    #                                             np.repeat(Msml, 2, axis=0))))

    for idx, theta in enumerate(randstim):  # save the luminance change
        # response.append([pair[0],
        #                  isodata(pair[1], len(doublestim), id + 1)])
        response.append([theta,
                         isodata(theta, len(randstim), idx + 1)])

    """save and fit"""

    with open(path + '/' + id + '.isodata', 'w+') as data:
        data.write('user: ' + user + '\n' + 'id: ' + id + '\n')
        for line in calibinfo:
            data.write(line + '\n')
        data.write('stimulus ' + 'response' + '\n')
        np.savetxt(data, response, fmt='%f %f', delimiter=',')

    _, _, params = fitiso(data.name)

    with open(path + '/' + id + '.isoslant', 'w+') as slant:
        slant.write('user: ' + user + '\n' + 'id: ' + id + '\n' +
                    'amplitude = %f' % params[0] + '\n' +
                    'phase = %f' % params[1] + '\n')
        # + 'offset = %f' % params[2] + '\n')
        for line in calibinfo:
            slant.write(line + '\n')


"""test: run the file"""
# isoslant(c=0.12, r=1)


"""just test the fitting a bit, if necessary"""


def showfit(datafile, paramfile):  # arguments are file names as strings; the file name should include relative path

    stim, res = np.loadtxt(datafile, skiprows=15, unpack=True)

    with open(paramfile) as f:
        lines = f.read().splitlines()
        amplitude = ParReader(paramfile).find_param(lines, 'amplitude', '=')
        phase = ParReader(paramfile).find_param(lines, 'phase', '=')
        # offset = filetools.readparam(lines, 'offset')

    import matplotlib.pyplot as plt
    plt.figure(figsize=(6, 4))
    plt.scatter(stim, res, label='Data')
    xfit = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    # yfit = amplitude * np.sin(xfit + phase) + offset
    yfit = amplitude * np.sin(xfit + phase)
    plt.plot(xfit, yfit, label='Fitted function')
    plt.show()