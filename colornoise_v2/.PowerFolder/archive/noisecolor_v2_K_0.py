#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

from numpy import *
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

"""calibration files, transformation, and gray background"""
calib = rgb2sml_copy.calibration(rgb2sml_copy.openfile())  # Load the parameters of the calibration file
transf = rgb2sml_copy.transformation(calib.A0(), calib.AMatrix(),
                                     calib.Gamma())  # Creates an object transf that has as methods all the needed transformations
Csml = transf.center()
Crgb = transf.sml2rgb(Csml)

win = visual.Window(monitor='testMonitor', fullscr=True, unit='deg', colorSpace='rgb255', color=Crgb, allowGUI=True)

"""fill stimuli color for different noise conditions"""

ntrial = 10
dist = 2
sigma = 2  # not sure about this value yet; probably depend on subjects
npatch = 16


def patchstim(patchsize=0.5):  # patchsize=0.41
    patch = visual.ElementArrayStim(win=win, units='deg', nElements=npatch, elementMask='circle',
                                    elementTex=None, sizes=patchsize, colorSpace='rgb255')
    return patch


def patchpos(xlim, ylim, n=4):
    pos = [(x, y)
           for x in linspace(xlim[0], xlim[1], n)
           for y in linspace(ylim[0], ylim[1], n)]
    return pos


def randcolor(theta, sigma, npatch, c=0.12, sscale=2.6, dlum=0, unit='degree', subject='None'):
    noise = random.normal(theta, sigma, npatch)
    color = [colorpalette.newcolor(n, c, sscale, dlum, unit, subject=subject) for n in noise]
    sml, rgb = zip(*color)
    return sml, rgb


def expcolornoise(noise_condition, theta=200, subject='None', c=0.12, sscale=2.6, dlum=0):
    # change the theta for different trials

    left = theta + dist
    right = theta - dist

    # set position and color of stimuli
    leftpatch = patchstim()
    rightpatch = patchstim()
    cmppatch = patchstim()

    leftpatch.xys = patchpos([-3, -1], [-3, -1])
    rightpatch.xys = patchpos([1, 3], [-3, -1])
    cmppatch.xys = patchpos([-1, 1], [2 * sqrt(3) - 3, 2 * sqrt(3) - 1])

    # create staircases
    info = {'startPoints': [0.5, -0.5], 'nTrials': ntrial}  # set two stairs here, with different startpoints;
    # later maybe make it as different size?
    stairs = []
    for thisStart in info['startPoints']:
        thisInfo = copy.copy(info)
        thisInfo['thisStart'] = thisStart  # we might want to keep track of this
        thisStair = data.StairHandler(startVal=thisStart,
                                      extraInfo=thisInfo,
                                      nTrials=50, stepSizes=0.5,
                                      nUp=1, nDown=2,
                                      minVal=-5, maxVal=5)
        stairs.append(thisStair)

    track = empty((0, 4))

    for trialN in range(ntrial):
        random.shuffle(stairs)  # this shuffles 'in place' (ie stairs itself is changed, nothing returned)

        for thisStair in stairs:
            rotation = next(thisStair)
            ratio = random.uniform(0, 1, 1)

            cmp = int(ratio * dist + right)
            # side = int(random.choice([-1, 1], 1))
            # cmp = theta + side * (dist + 2 * sigma)
            # cmp = cmp + rotation  # if use staircase

            #  choose noise condition
            if noise_condition == 'L-L':  # low - low noise
                leftpatch.colors = colorpalette.newcolor(left, c, sscale, dlum, unit='degree', subject=subject)[1]
                rightpatch.colors = colorpalette.newcolor(right, c, sscale, dlum, unit='degree', subject=subject)[1]

                cmppatch.colors = colorpalette.newcolor(cmp, c, sscale, dlum, unit='degree', subject=subject)[1]

            elif noise_condition == 'L-H':  # low - high noise: only compare stimulus has high noise

                leftpatch.colors = colorpalette.newcolor(left, c, sscale, dlum, unit='degree', subject=subject)[1]
                rightpatch.colors = colorpalette.newcolor(right, c, sscale, dlum, unit='degree', subject=subject)[1]

                cmppatch.colors = randcolor(cmp, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]

            elif noise_condition == 'H-H':  # high - high noise
                leftpatch.colors = randcolor(left, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]
                rightpatch.colors = randcolor(right, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]
                cmppatch.colors = randcolor(cmp, sigma, npatch, c, sscale, dlum, unit='degree', subject=subject)[1]

            else:
                print("No noise condition corresponds to the input!")
                core.quit()

            # draw all stimuli

            leftpatch.draw()
            rightpatch.draw()
            cmppatch.draw()
            win.flip()
            core.wait(3)  # foe how long the stimuli will show
            win.flip()

            # get response
            judge = None

            while judge is None:
                allkeys = event.waitKeys()
                for key in allkeys:  # press left -> adjust comparision stim counter-clockwise to standard stim; press right -> clockwisely
                    # if (key == 'left' and side > 0) or (key == 'right' and side < 0):
                    #     judge = 1  # correct
                    # elif (key == 'left' and side < 0) or (key == 'right' and side > 0):
                    #     judge = 0  # incorrect
                    # elif key == 'escape':
                    #     core.quit()
                    if (key == 'left' and ratio > 0.5) or (key == 'right' and ratio < 0.5):
                        judge = 1  # correct
                    elif (key == 'left' and ratio < 0.5) or (key == 'right' and ratio > 0.5):
                        judge = 0  # incorrect
                    elif key == 'escape':
                        core.quit()

                    # # only fo pilot test: show feedback
                    # feedback = visual.TextStim(win,
                    #                            text='theta: ' + str(cmp) + ' side: ' + str(side) + ' judge: ' + str(
                    #                                judge),
                    #                            height=0.03, pos=(0, -0.7))
                    # feedback.draw()
                    # win.flip()
                    # core.wait(5.0)
                    # win.flip()

                event.clearEvents()

            thisStair.addResponse(judge)

        track = append(track, [[left, right, cmp, judge]], axis=0)

    with open(path + '/' + id + '.data', 'w+') as f:
        f.write('user: ' + user + '\n' + 'id: ' + id + '\n')
        f.write('condition: ' + noise_condition + '\n')
        f.write('sigma: ' + str(sigma) + '\n')
        f.write('left,  right,  cmp,  response' + '\n')
        savetxt(f, track, delimiter=',', fmt='%1.1f %1.1f %1.1f %i')

    win.close()
    core.quit()


"""run example"""
# expcolornoise(noise_condition="L-L", theta=300, subject="test")
# expcolornoise('L-H')
# expcolornoise('H-H')
