#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
This module contains functions for running color noise experiments.
The experiments can be loaded by running runexp(subject) in commands.

Running experiments requires config files in /config folder:
    *.par - parameters of stimuli
It writes config files in /config folder:
    *.xpp - records of each single session
    *.xrl - records of all pairs of parameters and sessions belong to one subject
It saves results in /data folder:
    *.xlsx - results of each complete session - no results will be saved if userbreak occurs

@author: yannansu
"""

import numpy as np
import time
from psychopy import visual, data, core, event, monitors
import os
import rgb2sml_copy
import colorpalette
import genconfig


"""monitor settings"""
mon = monitors.Monitor(name='testMonitor', width=38, distance=57)
mon.setSizePix((1024, 768))
mon.save()  # if the monitor info is not saved

"""calibration files, transformation, and gray background"""

calib = rgb2sml_copy.calibration(rgb2sml_copy.openfile())  # Load the parameters of the calibration file
transf = rgb2sml_copy.transformation(calib.A0(), calib.AMatrix(),
                                     calib.Gamma())  # Creates an object transf that has as methods all the needed transformations
Csml = transf.center()
Crgb = transf.sml2rgb(Csml)

"""experiments"""
class Exp():
    def __init__(self, subject, parafile):
        self.subject = subject
        self.idx = time.strftime("%Y%m%dT%H%M", time.localtime())  # add the current date
        self.parafile = parafile
        self.param = genconfig.readpara(parafile)
        self.ntrial = 15
        self.npatch = 16
        self.mon = mon
        self.win = visual.Window([1024, 768], monitor=self.mon, fullscr=True, unit='deg', colorSpace='rgb255',
                                 color=Crgb,
                                 allowGUI=True)

    """stimulus features"""

    def patchref(self, theta):  # reference patches
        ref = visual.Circle(win=self.win, units='deg', radius=0.8, fillColorSpace='rgb255', lineColorSpace='rgb255')
        ref.fillColor = \
            colorpalette.newcolor(theta, self.param['c'], self.param['sscale'], self.param['dlum'], 'degree',
                                  self.subject)[
                1]
        ref.lineColor = ref.fillColor
        return ref

    def patchstim(self, patchsize=0.75):  # standard and test stimuli
        patch = visual.ElementArrayStim(win=self.win, units='deg', nElements=self.npatch, elementMask='circle',
                                        elementTex=None, sizes=patchsize, colorSpace='rgb255')
        return patch

    def patchpos(self, xlim, ylim):  # position of standard and test stimuli
        n = int(np.sqrt(self.npatch))
        pos = [(x, y)
               for x in np.linspace(xlim[0], xlim[1], n)
               for y in np.linspace(ylim[0], ylim[1], n)]
        return pos

    """color noise & noise conditions"""

    def randcolor(self, theta, sigma, npatch, unit, subject):  # generate color noise
        noise = np.random.normal(theta, sigma, npatch)
        color = [colorpalette.newcolor(n, self.param['c'], self.param['sscale'], self.param['dlum'], unit, subject) for
                 n in noise]
        sml, rgb = zip(*color)
        return sml, rgb

    def choosecon(self, standard, test):  # choose noise condition
        sColor = None
        tColor = None
        if self.param['condition'] == 'L-L':  # low - low noise
            sColor = colorpalette.newcolor(standard, self.param['c'], self.param['sscale'], self.param['dlum'],
                                           unit='degree', subject=self.subject)[1]
            tColor = colorpalette.newcolor(test, self.param['c'], self.param['sscale'], self.param['dlum'],
                                           unit='degree', subject=self.subject)[1]

        elif self.param['condition'] == 'L-H':  # low - high noise: only test stimulus has high noise
            sColor = colorpalette.newcolor(standard, self.param['c'], self.param['sscale'], self.param['dlum'],
                                           unit='degree', subject=self.subject)[1]
            tColor = self.randcolor(test, self.param['sigma'], self.npatch, unit='degree', subject=self.subject)[1]

        elif self.param['condition'] == 'H-H':  # high - high noise
            sColor = self.randcolor(standard, self.param['sigma'], self.npatch, unit='degree', subject=self.subject)[1]
            tColor = self.randcolor(test, self.param['sigma'], self.npatch, unit='degree', subject=self.subject)[1]

        else:
            print("No noise condition corresponds to the input!")

        return sColor, tColor

    """main experiment"""

    def expcolornoise(self):

        # welcome
        msg = visual.TextStim(self.win, 'Welcome! Press any key to start this session :)', color='black', units='deg',
                              pos=(7, 0), height=0.8)
        msg.draw()
        self.win.mouseVisible = False
        self.win.flip()

        event.waitKeys()

        # startkey = event.waitKeys()
        # if [k == 'escape' for k in startkey]:
        #     core.quit()


        path = 'data/' + self.subject
        if not os.path.exists(path):
            os.makedirs(path)  # create a new folder named by user name

        # staircases
        conditions = genconfig.readstair(self.parafile)
        # conditions = data.importConditions('MultiStairConditions.xlsx')

        if conditions[0]['stairType'] == 'simple':
            stairs = data.MultiStairHandler(stairType='simple', conditions=conditions, nTrials=self.ntrial, method='sequential')
        elif conditions[0]['stairType'] == 'quest':
            stairs = data.MultiStairHandler(stairType='quest',conditions=conditions, nTrials=self.ntrial, method='sequential')

        # write configuration files
        xpp = genconfig.writexpp(self.subject, self.idx, self.param['condition'])
        xpp.head(self.parafile)

        xrl = genconfig.writexrl(self.subject, self.parafile, xpp.f.name)
        xrl.mkxrl()

        count = 0
        for rot, cond in stairs:
            count += 1

            if cond['label'].endswith('m'):  # for negative start values in staircases
                rot = -rot

            # set two reference
            left = cond['leftRef']
            right = cond['rightRef']

            leftRef = self.patchref(left)
            leftRef.pos = [-5, 2.5]
            rightRef = self.patchref(right)
            rightRef.pos = [5, 2.5]

            # set position and color of stimuli
            standard = cond['standard']  # standard should be fixed
            test = standard + rot

            sPatch = self.patchstim()
            tPatch = self.patchstim()
            sPatch.colors, tPatch.colors = self.choosecon(standard, test)

            # randomly assign patch positions: upper (+) or lower (-)
            patchpos = [[1, 4], [-4, -1]]
            rndpos = patchpos.copy()
            np.random.shuffle(rndpos)

            sPatch.xys = self.patchpos([-1.5, 1.5], rndpos[0])
            tPatch.xys = self.patchpos([-1.5, 1.5], rndpos[1])

            # fixation cross
            fix = visual.TextStim(self.win, text="+", units='deg', pos=[14.75, 0], height=0.4, color='black',
                                  colorSpace="rgb255")
            # number of trial
            num = visual.TextStim(self.win, text="trial " + str(count), units='deg', pos=[28, -13], height=0.4, color='black',
                                  colorSpace="rgb255")

            # first present references for 0.5 sec
            fix.draw()
            num.draw()
            leftRef.draw()
            rightRef.draw()
            self.win.flip()
            core.wait(0.5)

            # then present the standard and the test stimuli as well for 1.5 sec
            fix.draw()
            num.draw()
            leftRef.draw()
            rightRef.draw()
            sPatch.draw()
            tPatch.draw()
            self.win.flip()
            core.wait(1.5)  # for how many seconds the stimuli will show
            num.draw()
            self.win.flip()


            # get response
            judge = None

            while judge is None:
                allkeys = event.waitKeys()
                for key in allkeys:
                    if (key == 'left' and rot * rndpos[0][0] > 0) or (key == 'right' and rot * rndpos[0][0] < 0):
                        judge = 1  # correct
                        thiskey = key
                    elif (key == 'left' and rot * rndpos[0][0] < 0) or (key == 'right' and rot * rndpos[0][0] > 0):
                        judge = 0  # incorrect
                        thiskey = key
                    elif key == 'escape':
                        breakinfo = 'userbreak'
                        xrl.addbreak(breakinfo)
                        core.quit()

            xpp.task(count, rot, cond, judge)  # write to *.xpp files

            stairs.addResponse(judge)  # to the next trial
            event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

        xlsname = path + '/' + self.idx + self.param['condition'] + '.xlsx'
        xrl.adddata(xlsname)

        stairs.saveAsExcel(xlsname)  # save results

        # self.win.close()
        # core.quit()


"""run several sessions"""


def runexp(subject):  # for experiments, you should run this function in bash

    parfile = ['config/cn16rnd_lin_newtest.par']

    for count, pf in enumerate(parfile):
        Exp(subject, pf).expcolornoise()  # run one session

        waitwin = Exp(subject, pf).win

        #  rest between sessions
        if count == len(parfile):
            msg = visual.TextStim(waitwin, 'Well done!' + '\n' + 'You have finished all sessions :)',
                              color='black', units='deg', pos=(7, 0), height=0.8)
        else:            msg = visual.TextStim(waitwin, 'Take a break!' + '\n' + 'Then press any key to start the next session :)',
                              color='black', units='deg', pos=(7, 0), height=0.8)

        msg.draw()
        waitwin.mouseVisible = False
        waitwin.flip()
        event.waitKeys()
        # if [k == 'escape' for k in continuekey]:
        #     core.quit()

runexp('test')