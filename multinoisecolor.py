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
from psychopy import visual, data, core, event, monitors, misc
import os
import rgb2sml_copy
import colorpalette
import genconfig
import sys
import xlsxwriter
import csv
import math
from bisect import bisect_left

"""monitor settings"""
mon = monitors.Monitor(name='Dell Inc. 23"', width=38, distance=57)
mon.setSizePix((1920, 1080))
mon.save()  # if the monitor info is not saved

"""calibration files, transformation, and gray background"""

calib = rgb2sml_copy.calibration(rgb2sml_copy.openfile())  # Load the parameters of the calibration file
# Creates an object transf that has as methods all the needed transformations
transf = rgb2sml_copy.transformation(calib.A0(), calib.AMatrix(), calib.Gamma())
Csml = transf.center()
Crgb = transf.sml2rgb(Csml)


class Exp:
    """
    Class for performing the experiment.
    """

    def __init__(self, subject, par_file, res_dir, priors_file_path):
        self.subject = subject
        self.idx = time.strftime("%Y%m%dT%H%M", time.localtime())  # add the current date
        self.par_file = par_file
        self.param = genconfig.ParReader(par_file).read_param()
        if not res_dir:
            res_dir = 'data/'
        self.res_dir = res_dir
        self.priors_file_path = priors_file_path
        self.trial_nmb = 20
        self.patch_nmb = 16
        self.trial_dur = 1.5
        self.mon = mon
        self.win = visual.Window([800, 800], monitor=self.mon, unit='deg', colorSpace='rgb255',
                                 color=Crgb, allowGUI=True, fullscr=True)

    """stimulus features"""

    def patch_ref(self, theta):  # reference patches
        ref = visual.Circle(win=self.win, units='deg', radius=0.8, fillColorSpace='rgb255', lineColorSpace='rgb255')
        ref.fillColor = \
            colorpalette.newcolor(theta, self.param['c'], self.param['sscale'], self.param['dlum'], 'degree',
                                  self.subject)[1]
        ref.lineColor = ref.fillColor
        return ref

    def patch_stim(self, patchsize=0.75):  # standard and test stimuli
        patch = visual.ElementArrayStim(win=self.win, units='deg', nElements=self.patch_nmb, elementMask='circle',
                                        elementTex=None, sizes=patchsize, colorSpace='rgb255')
        return patch

    def patch_pos(self, xlim, ylim):  # position of standard and test stimuli
        n = int(np.sqrt(self.patch_nmb))
        pos = [(x, y)
               for x in np.linspace(xlim[0], xlim[1], n)
               for y in np.linspace(ylim[0], ylim[1], n)]
        return pos

    """color noise & noise conditions"""

    def rand_color(self, theta, sigma, npatch, unit, subject):  # generate color noise
        noise = np.random.normal(theta, sigma, npatch)
        color = [colorpalette.newcolor(n, self.param['c'], self.param['sscale'], self.param['dlum'], unit, subject) for
                 n in noise]
        sml, rgb = zip(*color)
        return sml, rgb

    def choose_con(self, standard, test):  # choose noise condition
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
            tColor = self.rand_color(test, self.param['sigma'], self.patch_nmb, unit='degree', subject=self.subject)[1]

        elif self.param['condition'] == 'H-H':  # high - high noise
            sColor = self.rand_color(standard, self.param['sigma'], self.patch_nmb, unit='degree', subject=self.subject)[1]
            tColor = self.rand_color(test, self.param['sigma'], self.patch_nmb, unit='degree', subject=self.subject)[1]

        else:
            print("No noise condition corresponds to the input!")

        return sColor, tColor

    """tool fucntion"""

    def take_closest(self, arr, val):
        """
        Assumes arr is sorted. Returns closest value to val (could be itself).
        If two numbers are equally close, return the smallest number.
        """
        pos = bisect_left(arr, val)
        if pos == 0:
            return arr[0]
        if pos == len(arr):
            return arr[-1]
        before = arr[pos - 1]
        after = arr[pos]
        if after - val < val - before:
            return after
        else:
            return before

    """main experiment"""

    def run_session(self):
        
        path = os.path.join(self.res_dir, self.subject)
        if not os.path.exists(path):
            os.makedirs(path)

        # welcome
        msg = visual.TextStim(self.win, 'Welcome! Press any key to start this session :)', color='black', units='deg',
                              pos=(7, 0), height=0.8)
        msg.draw()
        # self.win.mouseVisible = False
        self.win.flip()
        event.waitKeys()

        # read staircase parameters
        conditions = genconfig.ParReader(self.par_file).read_stair()
        # conditions = data.importConditions('MultiStairConditions.xlsx')  # directly read from *.xlsx files

        if conditions[0]['stairType'] == 'simple':
            stairs = data.MultiStairHandler(stairType='simple', conditions=conditions, nTrials=self.trial_nmb,
                                            method='sequential')
        elif conditions[0]['stairType'] == 'quest':
            # stairs = data.MultiStairHandler(stairType='quest', conditions=conditions, nTrials=self.trial_nmb,
            #                                 method='sequential')
            stairs = []
            for cond in conditions:
                if self.priors_file_path:
                    prior_file = self.priors_file_path + cond['label'] + '.psydat'
                    print(prior_file)
                    prior_handler = misc.fromFile(prior_file)
                else:
                    prior_handler = None
                cur_handler = data.QuestHandler(cond['startVal'], cond['startValSd'], pThreshold=cond['pThreshold'],
                                                nTrials=self.trial_nmb, minVal=cond['minVal'], maxVal=cond['maxVal'],
                                                staircase=prior_handler, extraInfo=cond)
                stairs.append(cur_handler)
        elif conditions[0]['stairType'] == 'psi':
            stairs = []
            for cond in conditions:
                if self.priors_file_path:
                    prior_file = self.priors_file_path + cond['label'] + '.npy'
                else:
                    prior_file = None
                print(prior_file)
                cur_handler = data.PsiHandler(nTrials=self.trial_nmb, intensRange=[1, 10], alphaRange=[1, 10],
                                              betaRange=[0.01, 10], intensPrecision=0.1, alphaPrecision=0.1,
                                              betaPrecision=0.01, delta=0.01, extraInfo=cond,
                                              prior=prior_file, fromFile=(prior_file is not None))
                stairs.append(cur_handler)
        elif conditions[0]['stairType'] == 'grid':
            stimuli = []
            for cond in conditions:
                for diff in np.arange(cond['minVal'], cond['maxVal'], cond['stepSize']):
                    stimuli.append({'cond': cond, 'diff': diff})
            repeats_nmb = math.ceil(self.trial_nmb / len(stimuli))
            stairs = data.TrialHandler(stimuli, repeats_nmb, method='random')

        # write configuration files
        xpp = genconfig.XppWriter(self.subject, self.idx, self.param['condition'])
        xpp.head(self.par_file, self.trial_dur)

        xrl = genconfig.XrlWriter(self.subject, self.par_file, xpp.f.name)
        xrl.mk_xrl()
        xlsname = path + '/' + self.idx + self.param['condition'] + '.xlsx'

        # runing staircase
        if isinstance(stairs, data.MultiStairHandler):
            # start running the staircase using the MultiStairHandler for the up-down method
            count = 0

            for rot, cond in stairs:
                count += 1
                judge, thiskey, trial_time = self.run_trial(rot, cond, count, xrl)

                # check whether the theta is valid - if not, the rotation given by staircase should be corrected by achievable values
                valid_theta = np.round(np.load('all-displayed-hue-more.npy'), decimals=1)
                disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                stair_test = cond['standard'] + stairs._nextIntensity * (-1) ** (cond['label'].endswith('m'))  # theta for staircase
                if stair_test < 0:
                    stair_test += 360
                disp_test = self.take_closest(valid_theta, stair_test)
                disp_intensity = abs(disp_test - disp_standard)
                if disp_intensity > 300:
                   disp_intensity = 360 - (disp_test + disp_standard)
                stairs.addResponse(judge, disp_intensity)

                print('to xpp:', count, rot, disp_intensity, cond, judge, trial_time)
                xpp.task(count, rot, disp_intensity, cond, judge, trial_time)  # write in *.xpp file

                print('stair test: ' + str(stair_test) + ', ' + 'disp_test:' + str(disp_test))

                event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

            xrl.add_data(xlsname)  # write in *.xlsx file - TO DO: fill in the All Intensities with real displayed values
            stairs.saveAsExcel(xlsname)  # save results
            psydat_file_path = os.path.join(path, self.idx + self.param['condition'] + '.psydat') # save the handler into a psydat-file
            misc.toFile(psydat_file_path, stairs)

        elif isinstance(stairs, list):
            # start running the staircase using custom interleaving stairs for the quest and psi methods
            count = 0
            rot_all = []
            rot_all_disp = []
            judge_all = []
            estimates = {s.extraInfo['label']: [] for s in stairs}

            for trial_n in range(self.trial_nmb):
                for handler_idx, cur_handler in enumerate(stairs):
                    count += 1
                    rot = next(cur_handler)

                    if len(rot_all) <= handler_idx:
                        rot_all.append([])
                    rot_all[handler_idx].append(rot)
                    cond = cur_handler.extraInfo
                    judge, thiskey, trial_time = self.run_trial(rot, cond, count, xrl)

                    if len(judge_all) <= handler_idx:
                        judge_all.append([])
                    judge_all[handler_idx].append(judge)
                    # cur_handler.addResponse(judge)  # to the next trial

                    valid_theta = np.round(np.load('all-displayed-hue-more.npy'), decimals=1)
                    disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                    stair_test = cond['standard'] + cur_handler._nextIntensity * (-1) ** (cond['label'].endswith('m'))  # theta for staircase
                    if stair_test < 0:
                        stair_test += 360
                    disp_test = self.take_closest(valid_theta, stair_test)
                    disp_intensity = abs(disp_test - disp_standard)
                    if disp_intensity > 300:
                       disp_intensity = 360 - (disp_test + disp_standard)
                    cur_handler.addResponse(judge, disp_intensity)

                    if len(rot_all_disp) <= handler_idx:  # add displayed intensities
                        rot_all_disp.append([])
                    rot_all_disp[handler_idx].append(disp_intensity)
                                                                                                                                               
                    print('stair test: ' + str(stair_test) + ', ' + 'disp_test:' + str(disp_test))

                    if isinstance(cur_handler, data.PsiHandler):
                        estimates[cur_handler.extraInfo['label']].append(
                            [cur_handler.estimateLambda()[0],           # location
                             cur_handler.estimateLambda768()[1],           # slope
                             cur_handler.estimateThreshold(0.75)])
                    elif isinstance(cur_handler, data.QuestHandler):
                        estimates[cur_handler.extraInfo['label']].append(
                            [cur_handler.mean(),
                             cur_handler.mode(),
                             cur_handler.quantile(0.5)])
                    xpp.task(count, rot, disp_intensity, cond, judge, trial_time)
                    event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

            xrl.add_data(xlsname)  # write in *.xlsx file

            # save results in xls-file
            workbook = xlsxwriter.Workbook(xlsname)
            for handler_idx, cur_handler in enumerate(stairs):
                worksheet = workbook.add_worksheet(cur_handler.extraInfo['label'])
                worksheet.write('A1', 'Reversal Intensities')
                worksheet.write('B1', 'Reversal Indices')
                worksheet.write('C1', 'All Intensities')
                worksheet.write('D1', 'All Responses')
                for i in range(len(rot_all[handler_idx])):
                    # worksheet.write('C' + str(i + 2), rot_all[handler_idx][i])
                    worksheet.write('C' + str(i + 2), rot_all_disp[handler_idx][i])
                    worksheet.write('D' + str(i + 2), judge_all[handler_idx][i])
            workbook.close()

            # print resulting parameters and estimates for each step
            res_file_path = os.path.join(path, self.idx + '_estimates.csv')
            res_writer = csv.writer(open(res_file_path, 'w'))
            for res_stim, res_vals in estimates.items():
                for res_val_id, res_val in enumerate(res_vals):
                    res_writer.writerow([res_stim, res_val_id, res_val[0], res_val[1], res_val[2]])

            # save each handler into a psydat-file and save posterior into a numpy-file
            for cur_handler in stairs:
                file_name = os.path.join(path, self.idx + self.param['condition'] + cur_handler.extraInfo['label'])
                misc.toFile(file_name + '.psydat', cur_handler)
                if isinstance(cur_handler, data.PsiHandler):
                    cur_handler.savePosterior(file_name + '.npy')

        """
        REMOVE this part: constant stimui
        ============================
        elif isinstance(stairs, data.TrialHandler):
            # start running the staircase using TrialHandler for the grid method
            count = 0
            results = {cond['label']: [] for cond in conditions}
            for trial in stairs:
                trial_cond = trial['cond']
                trial_diff = trial['diff']
                count += 1
                judge, thiskey = self.run_trial(trial_diff, trial_cond, count, xpp, xrl)
                results[trial_cond['label']].append((trial_diff, judge))
                event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

            xrl.add_data(xlsname)  # write in *.xlsx file

            # save results in xls-file
            workbook = xlsxwriter.Workbook(xlsname)
            for res_label, res_data in results.items():
                worksheet = workbook.add_worksheet(res_label)
                worksheet.write('A1', 'Reversal Intensities')
                worksheet.write('B1', 'Reversal Indices')
                worksheet.write('C1', 'All Intensities')
                worksheet.write('D1', 'All Responses')
                for i, (res_diff, res_resp) in enumerate(res_data):
                    worksheet.write('C' + str(i + 2), res_diff)
                    worksheet.write('D' + str(i + 2), res_resp)
            workbook.close()

            # save the handler into a psydat-file
            psydat_file_path = os.path.join(path, self.idx + self.param['condition'] + '.psydat')
            misc.toFile(psydat_file_path, stairs)

    """

    def run_trial(self, rot, cond, count, xrl):
        # for negative start values in staircases, because *.par files only give abs values
        if cond['label'].endswith('m'):
            rot = -rot

        # set two reference
        left = cond['leftRef']
        right = cond['rightRef']

        leftRef = self.patch_ref(left)
        leftRef.pos = [-5, 2.5]
        rightRef = self.patch_ref(right)
        rightRef.pos = [5, 2.5]

        # set colors of two stimuli
        standard = cond['standard']  # standard should be fixed
        test = standard + rot

        sPatch = self.patch_stim()
        tPatch = self.patch_stim()
        sPatch.colors, tPatch.colors = self.choose_con(standard, test)

        # randomly assign patch positions: upper (+) or lower (-)
        patchpos = [[1, 4], [-4, -1]]
        rndpos = patchpos.copy()
        np.random.shuffle(rndpos)

        sPatch.xys = self.patch_pos([-1.5, 1.5], rndpos[0])
        tPatch.xys = self.patch_pos([-1.5, 1.5], rndpos[1])

        # fixation cross
        fix = visual.TextStim(self.win, text="+", units='deg', pos=[14.75, 0], height=0.4, color='black',
                              colorSpace="rgb255")

        # a text showing the number of trial
        num = visual.TextStim(self.win, text="trial " + str(count), units='deg', pos=[28, -13], height=0.4,
                              color='black',
                              colorSpace="rgb255")

        trial_time_start = time.time()
        # first present references for 0.5 sec
        fix.draw()
        num.draw()
        leftRef.draw()
        rightRef.draw()
        self.win.flip()
        core.wait(0.5)

        # then present the standard and test stimuli
        fix.draw()
        num.draw()
        leftRef.draw()
        rightRef.draw()
        sPatch.draw()
        tPatch.draw()
        self.win.flip()

        if self.trial_dur:
            # show stimuli for some time
            core.wait(self.trial_dur)

            # refresh the window, clear references and stimuli
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
                    xrl.add_break(breakinfo)
                    core.quit()

        trial_time = time.time() - trial_time_start

        # xpp.task(count, rot, cond, judge, trial_time)  # write in *.xpp file

        return judge, thiskey, trial_time


def run_exp(subject, par_file_path=None, res_dir=None, priors_file_path=None):

    if par_file_path:
        par_files = [par_file_path]
    else:
        par_files = ['config/compare_updown_hue1.par']  # change the file list as you wish

    for count, pf in enumerate(par_files):
        Exp(subject, pf, res_dir, priors_file_path).run_session()  # run one session

        waitwin = Exp(subject, pf, res_dir, priors_file_path).win

        #  rest between sessions
        if count + 1 == len(par_files):
            msg = visual.TextStim(waitwin, 'Well done!' + '\n' + 'You have finished all sessions :)',
                                  color='black', units='deg', pos=(7, 0), height=0.8)
        else:
            msg = visual.TextStim(waitwin, 'Take a break!' + '\n' + 'Then press any key to start the next session :)',
                                  color='black', units='deg', pos=(7, 0), height=0.8)

        msg.draw()
        # waitwin.mouseVisible = False
        waitwin.flip()
        event.waitKeys()
        # if [k == 'escape' for k in continuekey]:
        #     core.quit()



# run_exp(subject='ysu_lab_updown', par_file_path='config/test_updown.par', res_dir='data')

#  # run experiment in bash by calling
# # # "python multinoisecolor.py [subject] [optional par_file] [optional results_dir] [optional priors_file]"
# if __name__ == '__main__':
#     # pass the first argument (subject) and optionally the second one (par-file) to the run_exp function
#     par_file = None
#     if len(sys.argv) > 2:
#         par_file = sys.argv[2]
#     results_dir = None
#     if len(sys.argv) > 3:
#         results_dir = sys.argv[3]
#     priors_file = None
#     if len(sys.argv) > 4:
#         priors_file = sys.argv[4]
#     run_exp(sys.argv[1], par_file, results_dir, priors_file)
