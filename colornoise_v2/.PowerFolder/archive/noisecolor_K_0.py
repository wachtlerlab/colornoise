#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

import numpy as np
import random
import copy
from psychopy import visual, data, core, event, monitors
import os
import rgb2sml_copy
import colorpalette

"""monitor settings"""
#  should be more color settings after calibration?
mon = monitors.Monitor(name='testMonitor', width=32.7, distance=57)
mon.setSizePix((1024, 768))

# mon.save()  # if the monitor info is not saved

"""files and data"""
def userinfo(path=''):
    from psychopy import gui
    import time

    dlg = gui.Dlg()
    dlg.addField("Subject ID:")
    dlg.show()

    user = dlg.data[0]
    id = time.strftime("%Y%m%dT%H%M", time.localtime())  # add the current date
    os.makedirs(path + user)  # create a new folder named by user name
    return user, id

user, id = userinfo(path='data/')
path = 'data/' + user


def savedata(noise_condition, track):
    with open(path + '/' + id + '.data', 'w+') as f:
        f.write('user: ' + user + '\n' + 'id: ' + id + '\n')
        f.write('condition: ' + noise_condition + '\n')
        f.write('sigma: ' + str(sigma) + '\n')
        f.write('left, right, standard, test, rotation, judge' + '\n')
        np.savetxt(f, track, delimiter=',', fmt='%1.1f %1.1f %1.1f %1.1f %1.1f %i')

"""calibration files, transformation, and gray background"""
calib = rgb2sml_copy.calibration(rgb2sml_copy.openfile())  # Load the parameters of the calibration file
transf = rgb2sml_copy.transformation(calib.A0(), calib.AMatrix(),
                                     calib.Gamma())  # Creates an object transf that has as methods all the needed transformations
Csml = transf.center()
Crgb = transf.sml2rgb(Csml)

win = visual.Window(monitor='testMonitor', fullscr=True, unit='deg', colorSpace='rgb255', color=Crgb, allowGUI=True)

c = 0.12
sscale = 2.6
dlum = 0

"""fill stimuli color for different noise conditions"""

ntrial = 10
dist = 2
sigma = 2  # not sure about this value yet; probably depend on subjects
npatch = 16


def patchstim(patchsize=0.5):  
    patch = visual.ElementArrayStim(win=win, units='deg', nElements=npatch, elementMask='circle',
                                    elementTex=None, sizes=patchsize, colorSpace='rgb255')
    return patch


def patchpos(xlim, ylim, n=4):
    pos = [(x, y)
           for x in np.linspace(xlim[0], xlim[1], n)
           for y in np.linspace(ylim[0], ylim[1], n)]
    return pos


def randcolor(theta, sigma, npatch, c=0.12, sscale=2.6, dlum=0, unit='degree', subject='None'):
    noise = np.random.normal(theta, sigma, npatch)
    color = [colorpalette.newcolor(n, c, sscale, dlum, unit, subject=subject) for n in noise]
    sml, rgb = zip(*color)
    return sml, rgb


def expcolornoise(noise_condition, theta, subject='None', c=0.12, sscale=2.6, dlum=0):
    
    # set two reference 
    left = theta + 20
    right = theta - 20

    leftRef = visual.Circle(win=win, units='deg', fillColorSpace='rgb255', lineColorSpace='rgb255', pos=[-8, 2])
    leftRef.fillColor = colorpalette.newcolor(left, c, sscale, dlum, unit='degree', subject=subject)[1]
    leftRef.lineColor = leftRef.fillColor

    rightRef = visual.Circle(win=win, units='deg', fillColorSpace='rgb255', lineColorSpace='rgb255', pos=[8, 2])
    rightRef.fillColor = colorpalette.newcolor(right, c, sscale, dlum, unit='degree', subject=subject)[1]
    rightRef.lineColor = rightRef.fillColor

    # set position and color of stimuli
    sPatch = patchstim()
    tPatch = patchstim()

    sPatch.xys = patchpos([-1, 1], [1, 3])
    tPatch.xys = patchpos([-1, 1], [-3, -1])

    # create staircases
    info = {'startVal': [-3], 'steps': [[2, 1], [1, 2]]}  # set two stairs here, with different startpoints;
    # later maybe make it as diffferent size?
    stairs = []
    for startVal in info['startVal']:
        thisInfo = copy.copy(info)
        thisInfo['startVal'] = startVal
        for steps in info['steps']:
            thisInfo['steps'] = steps
            thisStair = data.StairHandler(startVal=startVal,
                                          extraInfo=thisInfo,
                                          nTrials=ntrial, stepSizes=0.5,
                                          nUp=steps[0], nDown=steps[1],
                                          minVal=-5, maxVal=5)

            stairs.append(thisStair)

    track = np.empty((0, 6))

    for trialN in range(ntrial):
        random.shuffle(stairs)  # this shuffles 'in place' (ie stairs itself is changed, nothing returned)

        for thisStair in stairs:

            standard = theta  # standard should be fixed
            # rotation = next(thisStair)  # what is rotation = 0? skip this trial?
            rotation = thisStair
            test = standard + rotation

            #  choose noise condition
            if noise_condition == 'L-L':  # low - low noise
                sPatch.colors = colorpalette.newcolor(standard, c, sscale, dlum, unit='degree', subject=subject)[1]
                tPatch.colors = colorpalette.newcolor(test, c, sscale, dlum, unit='degree', subject=subject)[1]

            elif noise_condition == 'L-H':  # low - high noise: only compare stimulus has high noise
                sPatch.colors = colorpalette.newcolor(standard, c, sscale, dlum, unit='degree', subject=subject)[1]
                tPatch.colors = randcolor(test, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]

            elif noise_condition == 'H-H':  # high - high noise
                sPatch.colors = randcolor(standard, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]
                tPatch.colors = randcolor(test, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]

            else:
                print("No noise condition corresponds to the input!")
                core.quit()

            # draw all stimuli
            leftRef.draw()
            rightRef.draw()
            sPatch.draw()
            tPatch.draw()
            win.flip()
            core.wait(1)  # foe how long the stimuli will show
            win.flip()

            # get response
            judge = None

            while judge is None:
                allkeys = event.waitKeys()
                for key in allkeys:  # press left -> adjust comparision stim counter-clockwise to standard stim; press right -> clockwisely
                    if (key == 'left' and rotation > 0) or (key == 'right' and rotation < 0):
                        judge = 1  # correct
                    elif (key == 'left' and rotation < 0) or (key == 'right' and rotation > 0):
                        judge = 0  # incorrect
                    elif key == 'escape':
                        core.quit()

            thisStair.addResponse(judge)
            thisStair.saveAsExcel(path+ '/stair'+ str(trialN))

        track = np.append(track, [[left, right, standard, test, rotation, judge]], axis=0)

    win.close()
    core.quit()

    savedata(noise_condition, track)

    return track





# """run example"""
expcolornoise(noise_condition="L-L", theta=90)
# # expcolornoise(noise_condition="L-H", theta=300, subject="test")
# # expcolornoise(noise_condition="H-H", theta=300, subject="test")



# def randcolornoise(noise_condition="L-L", subject="test"):
#     # theta = np.repeat(np.linspace(0, 360, 16, endpoint=False), repeat)
#     theta = np.linspace(0, 360, 16, endpoint=False)
#     colors = [colorpalette.newcolor(x, c, sscale, dlum, unit='degree', subject=None)[1] for x in theta]
#
#     repeat = 10
#     for
#     random.shuffle(colors)

