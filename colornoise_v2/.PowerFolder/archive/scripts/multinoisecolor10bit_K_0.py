#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python version 3.7.6

"""
This module contains functions for running color-noise experiments (in 10-bit color depth).

Run experiment by running in Python3.7:
    run_exp(subject, par_file_path[optional], cfg_file_path[optional], res_dir[optional], priors_file_path[optional])
Or in bash:
    python3.7 multinoisecolor10bit.py [subject] [optional par_file] [optional cfg_file] [optional results_dir] [optional priors_file]

Running experiments requires config files in config folder:
    config/experiment_config.yaml   - experiment config file
    config/parameter.yaml           - parameters of stimuli
It writes log files in data folder:
    data/subject/*.yaml             - single session log file
    data/subject/*.xrl              - single subject log file
It saves results in data folder:
    data/subject/*.xlsx             - results of each complete session; no results will be saved if userbreak occurs

@author: yannansu
"""

import numpy as np
import time
from psychopy import visual, data, core, event, monitors, misc
import os
from colorpalette_plus import ColorPicker
import config_tools
import sys
import xlsxwriter
import csv
from bisect import bisect_left
import argparse


class Exp:
    """
    Class for performing the experiment.
    """

    def __init__(self, subject, par_file, cfg_file, res_dir, priors_file_path):
        self.subject = subject
        self.idx = time.strftime("%Y%m%dT%H%M", time.localtime())  # add the current date
        if not res_dir:
            res_dir = 'data/'
        self.res_dir = res_dir
        self.priors_file_path = priors_file_path
        self.cfg_file = cfg_file
        self.cfg = config_tools.read_yml(cfg_file)
        self.par_file = par_file

        self.param = config_tools.read_yml(par_file)

        self.patch_nmb = self.cfg['patch_nmb']
        self.trial_nmb = self.cfg['trial_nmb']
        self.trial_dur = self.cfg['trial_dur']
        self.depthBits = self.cfg['depthBits']
        self.hue_list = self.cfg['hue_list']

        self.ColorPicker = ColorPicker(c=self.param['c'],
                                       sscale=self.param['sscale'],
                                       unit='deg',
                                       depthBits=self.depthBits,
                                       subject=self.subject)
        self.ColorSpace = self.ColorPicker.colorSpace
        self.Csml = self.ColorPicker.Csml
        self.Crgb = self.ColorPicker.Crgb
        self.mon = monitors.Monitor(name=self.cfg['monitor']['name'],
                                    width=self.cfg['monitor']['width'],
                                    distance=self.cfg['monitor']['distance'])
        self.mon.setSizePix((self.cfg['monitor']['size']))
        self.win = visual.Window(monitor=self.mon,
                                 unit='deg',
                                 colorSpace=self.ColorSpace,
                                 color=self.Crgb,
                                 allowGUI=True,
                                 fullscr=True,
                                 bpc=(self.depthBits, self.depthBits, self.depthBits), depthBits=self.depthBits)

    """stimulus features"""

    def patch_ref(self, theta):  # reference patches
        ref = visual.Circle(win=self.win,
                            units='deg',
                            radius=self.cfg['ref_size'],
                            fillColorSpace=self.ColorSpace,
                            lineColorSpace=self.ColorSpace)
        ref.fillColor = self.ColorPicker.newcolor(theta, self.param['dlum'])[1]
        ref.lineColor = ref.fillColor
        return ref

    def patch_stim(self):  # standard and test stimuli
        patch = visual.ElementArrayStim(win=self.win,
                                        units='deg',
                                        nElements=self.patch_nmb,
                                        elementMask='circle',
                                        elementTex=None,
                                        sizes=self.cfg['patch_size'],
                                        colorSpace=self.ColorSpace)
        return patch

    def patch_pos(self, xlim, ylim):  # position of standard and test stimuli
        n = int(np.sqrt(self.patch_nmb))
        pos = [(x, y)
               for x in np.linspace(xlim[0], xlim[1], n)
               for y in np.linspace(ylim[0], ylim[1], n)]
        return pos

    """color noise & noise conditions"""

    def rand_color(self, theta, sigma, npatch):  # generate color noise
        noise = np.random.normal(theta, sigma, npatch)
        color = [ColorPicker.newcolor(theta, self.param['dlum']) for n in noise]
        sml, rgb = zip(*color)
        return sml, rgb

    def choose_con(self, standard, test):  # choose noise condition
        sColor = None
        tColor = None
        if self.param['noise_condition'] == 'L-L':  # low - low noise
            sColor = self.ColorPicker.newcolor(standard, self.param['dlum'])[1]
            tColor = self.ColorPicker.newcolor(test, self.param['dlum'])[1]

        elif self.param['noise_condition'] == 'L-H':  # low - high noise: only test stimulus has high noise
            sColor = self.ColorPicker.newcolor(standard, self.param['dlum'])[1]

            tColor = self.rand_color(test, self.param['sigma'], self.patch_nmb)[1]

        elif self.param['noise_condition'] == 'H-H':  # high - high noise
            sColor = self.rand_color(standard, self.param['sigma'], self.patch_nmb)[1]
            tColor = self.rand_color(test, self.param['sigma'], self.patch_nmb)[1]

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

    def run_trial(self, rot, cond, count):
        # for negative start values in staircases, because *.par files only give abs values
        if cond['label'].endswith('m'):
            rot = -rot

        # set two reference
        left = cond['leftRef']
        right = cond['rightRef']

        leftRef = self.patch_ref(left)
        leftRef.pos = self.cfg['leftRef.pos']
        rightRef = self.patch_ref(right)
        rightRef.pos = self.cfg['rightRef.pos']

        # set colors of two stimuli
        standard = cond['standard']  # standard should be fixed
        test = standard + rot

        sPatch = self.patch_stim()
        tPatch = self.patch_stim()
        sPatch.colors, tPatch.colors = self.choose_con(standard, test)

        # randomly assign patch positions: upper (+) or lower (-)
        patchpos = [self.cfg['standard.ylim'], self.cfg['test.ylim']]
        rndpos = patchpos.copy()
        np.random.shuffle(rndpos)

        sPatch.xys = self.patch_pos(self.cfg['standard.xlim'], rndpos[0])
        tPatch.xys = self.patch_pos(self.cfg['test.xlim'], rndpos[1])

        # fixation cross
        fix = visual.TextStim(self.win, text="+", units='deg', pos=[0, 0], height=0.4, color='black',
                              colorSpace=self.ColorSpace)
        # number of trial
        num = visual.TextStim(self.win, text="trial " + str(count), units='deg', pos=[12, -10], height=0.4,
                              color='black', colorSpace=self.ColorSpace)

        trial_time_start = time.time()
        # first present references for 0.5 sec
        fix.draw()
        num.draw()
        leftRef.draw()
        rightRef.draw()
        self.win.flip()
        core.wait(0.5)

        # then present the standard and the test stimuli as well for 1 sec
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
                    # xrl.add_break(breakinfo)
                    config_tools.write_xrl(self.subject, break_info='userbreak')
                    core.quit()

        trial_time = time.time() - trial_time_start

        return judge, thiskey, trial_time

    def run_session(self):

        path = os.path.join(self.res_dir, self.subject)
        if not os.path.exists(path):
            os.makedirs(path)

        # welcome
        msg = visual.TextStim(self.win, 'Welcome!' + '\n' + ' Press any key to start this session :)', color='black',
                              units='deg',
                              pos=(0, 0), height=0.8)
        msg.draw()
        self.win.mouseVisible = False
        self.win.flip()
        event.waitKeys()

        # read staircase parameters
        conditions = [dict({'stimulus': key}, **value) for key, value in self.param.items() if
                      key.startswith('stimulus')]

        if conditions[0]['stairType'] == 'simple':
            stairs = data.MultiStairHandler(stairType='simple', conditions=conditions, nTrials=self.trial_nmb,
                                            method='sequential')
        elif conditions[0]['stairType'] == 'quest':
            stairs = []
            for cond in conditions:
                if self.priors_file_path:
                    prior_file = self.priors_file_path + cond['label'] + '.psydat'
                    print(prior_file)
                    prior_handler = misc.fromFile(prior_file)
                else:
                    prior_handler = None
                cur_handler = data.QuestHandler(cond['startVal'], cond['startValSd'], pThreshold=cond['pThreshold'],
                                                nTrials=self.trial_nmb, minVal=cond['min_val'], maxVal=cond['max_val'],
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

        # write configuration files
        xpp = config_tools.WriteXpp(self.subject, self.idx)
        xpp_file = xpp.head(self.cfg_file, self.par_file)
        config_tools.write_xrl(self.subject, cfg_file=self.cfg_file, par_file=self.par_file, xpp_file=xpp_file)

        xlsname = path + '/' + self.idx + self.param['noise_condition'] + '.xlsx'

        """ running staircase """

        if isinstance(stairs, data.MultiStairHandler):
            # start running the staircase using the MultiStairHandler for the up-down method
            count = 0

            for rot, cond in stairs:
                count += 1
                judge, thiskey, trial_time = self.run_trial(rot, cond, count)

                # check whether the theta is valid - if not, the rotation given by staircase should be corrected by
                # realizable values
                valid_theta = np.round(np.load(self.hue_list), decimals=1)

                disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                stair_test = cond['standard'] + stairs._nextIntensity * (-1) ** (
                    cond['label'].endswith('m'))  # theta for staircase
                if stair_test < 0:
                    stair_test += 360
                disp_test = self.take_closest(valid_theta, stair_test)
                disp_intensity = abs(disp_test - disp_standard)
                if disp_intensity > 300:
                    disp_intensity = 360 - (disp_test + disp_standard)
                stairs.addResponse(judge, disp_intensity)

                xpp.task(count, cond, rot, float(disp_intensity), judge, trial_time)

                event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

            config_tools.write_xrl(self.subject, xls_file=xlsname)
            stairs.saveAsExcel(xlsname)  # save results
            psydat_file_path = os.path.join(path, "psydat", self.idx + self.param['condition'] + '.psydat')  # save the handler into a psydat-file
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
                    judge, thiskey, trial_time = self.run_trial(rot, cond, count)

                    if len(judge_all) <= handler_idx:
                        judge_all.append([])
                    judge_all[handler_idx].append(judge)
                    # cur_handler.addResponse(judge)  # to the next trial

                    valid_theta = np.round(np.load(self.hue_list), decimals=1)
                    disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                    stair_test = cond['standard'] + cur_handler._nextIntensity * (-1) ** (
                        cond['label'].endswith('m'))  # theta for staircase
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
                            [cur_handler.estimateLambda()[0],  # location
                             cur_handler.estimateLambda768()[1],  # slope
                             cur_handler.estimateThreshold(0.75)])
                    elif isinstance(cur_handler, data.QuestHandler):
                        estimates[cur_handler.extraInfo['label']].append(
                            [cur_handler.mean(),
                             cur_handler.mode(),
                             cur_handler.quantile(0.5)])

                    xpp.task(count, cond, rot, disp_intensity, judge, trial_time)
                    event.waitKeys(keyList=[thiskey])  # press the response key again to start the next trial

            config_tools.write_xrl(self.subject, xls_file=xlsname)

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
                file_name = os.path.join(path,
                                         self.idx + self.param['noise_condition'] + cur_handler.extraInfo['label'])
                misc.toFile(file_name + '.psydat', cur_handler)
                if isinstance(cur_handler, data.PsiHandler):
                    cur_handler.savePosterior(file_name + '.npy')


def run_exp(subject, par_file_path=None, cfg_file_path=None, res_dir=None, priors_file_path=None):
    if par_file_path:
        par_files = par_file_path
    else:
        par_files = ['config/parameter_example.yaml']  # change the file list as you wish

    if cfg_file_path is None:
        cfg_file_path = ['config/expconfig.yaml']

    for count, pf in enumerate(par_files):
        Exp(subject, pf, cfg_file_path, res_dir, priors_file_path).run_session()  # run one session

        waitwin = Exp(subject, pf, cfg_file_path, res_dir, priors_file_path).win

        #  rest between sessions
        if count + 1 == len(par_files):
            msg = visual.TextStim(waitwin, 'Well done!' + '\n' +
                                  'You have finished all sessions :)',
                                  color='black', units='deg', pos=(0, 0), height=0.8)
        else:
            msg = visual.TextStim(waitwin, 'Take a break!' + '\n' +
                                  'Then press any key to start the next session :)',
                                  color='black', units='deg', pos=(0, 0), height=0.8)

        msg.draw()
        waitwin.flip()
        event.waitKeys()
        # if [k == 'escape' for k in continuekey]:
        #     core.quit()


# run_exp(subject='pilot', par_file_path=['config/cn4_quest_LL_a.yaml'], cfg_file_path='config/expconfig_8bit.yaml')

""" 
run experiment in bash by calling
"python multinoisecolor10bit.py [subject] [optional par_file] [optional cfg_file] [optional results_dir] [optional priors_file]"
"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject')
    parser.add_argument('--par_file', nargs='*')
    parser.add_argument('--cfg_file')
    parser.add_argument('--results_dir')
    parser.add_argument('--priors_file')

    args = parser.parse_args()
    subject = args.subject
    par_file = args.par_file
    cfg_file = args.cfg_file
    results_dir = args.results_dir
    priors_file = args.priors_file
    run_exp(subject, par_file, cfg_file, results_dir, priors_file)

