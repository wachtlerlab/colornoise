#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python version 3.7.6

"""
This module contains functions for running color-noise experiments (in 10-bit color depth).

Run experiment by running in Python3.7:
    run_exp(subject, par_file_path, cfg_file_path[optional], res_dir[optional], priors_file_path[optional])
Or in bash:
    python3.7 multinoisecolor10bit.py [subject] [par_file] [optional cfg_file] [optional results_dir] [optional priors_file]

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
from psychopy.hardware import keyboard
import os
from colorpalette import ColorPicker
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

        self.ColorPicker = ColorPicker(c=self.param['c'],
                                       sscale=self.param['sscale'],
                                       unit='deg',
                                       depthBits=self.depthBits,
                                       subject=self.subject)
        self.ColorSpace = self.ColorPicker.colorSpace

        hue_list_path = 'config/colorlist/' + self.subject
        if not os.path.exists(hue_list_path):
            self.ColorPicker.gencolorlist(0.2)
        self.hue_list = hue_list_path + '/hue-list-10bit-res0.2-sub-' + self.subject + '.npy'

        self.Csml = self.ColorPicker.center()
        self.Crgb = self.ColorPicker.sml2rgb(self.ColorPicker.center())
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
        ref.fillColor = self.ColorPicker.newcolor(theta=theta)[1]
        ref.lineColor = ref.fillColor
        return ref

    def patch_stim(self):  # standard and test stimuli
        patch = visual.ElementArrayStim(win=self.win,
                                        units='deg',
                                        fieldSize=self.cfg['field_size'],
                                        nElements=self.patch_nmb,
                                        elementMask='circle',
                                        elementTex=None,
                                        sizes=self.cfg['patch_size'],
                                        colorSpace=self.ColorSpace)
        return patch

    def patch_pos(self, xlim, ylim):  # position of standard and test stimuli
        n = int(np.sqrt(self.patch_nmb))
        pos = [[x, y]
               for x in np.linspace(xlim[0], xlim[1], n)
               for y in np.linspace(ylim[0], ylim[1], n)]
        return pos

    """color noise & noise conditions"""

    def rand_color(self, theta, sigma, npatch):  # generate color noise
        noise = np.random.normal(theta, sigma, npatch)
        color = [ColorPicker.newcolor(theta=n) for n in noise]
        sml, rgb = zip(*color)
        return sml, rgb

    def choose_con(self, standard, test):  # choose noise condition
        sColor = None
        tColor = None
        if self.param['noise_condition'] == 'L-L':  # low - low noise
            sColor = self.ColorPicker.newcolor(theta=standard)[1]
            tColor = self.ColorPicker.newcolor(theta=test)[1]

        elif self.param['noise_condition'] == 'L-H':  # low - high noise: only test stimulus has high noise
            sColor = self.ColorPicker.newcolor(theta=standard)[1]

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
        fix = visual.TextStim(self.win, text="+", units='deg', pos=[0, 0], height=0.5, color='black',
                              colorSpace=self.ColorSpace)
        # number of trial
        num = visual.TextStim(self.win, text="trial " + str(count), units='deg', pos=[12, -10], height=0.4,
                              color='black', colorSpace=self.ColorSpace)

        trial_time_start = time.time()
        # first present references
        fix.draw()
        num.draw()
        leftRef.draw()
        rightRef.draw()
        self.win.flip()
        core.wait(1.0)

        # then present the standard and the test stimuli as well
        fix.draw()
        num.draw()
        leftRef.draw()
        rightRef.draw()
        sPatch.draw()
        tPatch.draw()
        self.win.flip()
        core.wait(self.trial_dur)

        fix.draw()
        self.win.flip()
        core.wait(0.2)  # 0.2 sec gray background
        react_time_start = time.time()

        # refresh the window and show a colored checkerboard
        horiz_n = 30
        vertic_n = 20
        rect = visual.ElementArrayStim(self.win, units='norm', nElements=horiz_n * vertic_n, elementMask=None,
                                       elementTex=None,
                                       sizes=(2 / horiz_n, 2 / vertic_n), colorSpace=self.ColorSpace)
        rect.xys = [(x, y) for x in np.linspace(-1, 1, horiz_n, endpoint=False) + 1 / horiz_n
                    for y in np.linspace(-1, 1, vertic_n, endpoint=False) + 1 / vertic_n]

        rect.colors = [self.ColorPicker.newcolor(theta=x)[1] for x in
                       np.random.randint(0, high=360, size=horiz_n * vertic_n)]
        rect.draw()
        self.win.flip()
        core.wait(0.5)  # 0.5 sec checkerboard

        judge = None
        react_time_stop = -1
        kb = keyboard.Keyboard()
        get_keys = kb.getKeys(['right', 'left', 'escape'])  # if response during the checkerboard
        if ('left' in get_keys and rot * rndpos[0][0] > 0) or ('right' in get_keys and rot * rndpos[0][0] < 0):
            judge = 1  # correct
            react_time_stop = time.time()
        elif ('left' in get_keys and rot * rndpos[0][0] < 0) or ('right' in get_keys and rot * rndpos[0][0] > 0):
            judge = 0  # incorrect
            react_time_stop = time.time()
        if 'escape' in get_keys:
            config_tools.write_xrl(self.subject, break_info='userbreak')
            core.quit()

        self.win.flip()
        fix.draw()
        self.win.flip()

        if judge is None:  # if response after the checkerboard
            for wait_keys in event.waitKeys():
                if (wait_keys == 'left' and rot * rndpos[0][0] > 0) or (
                        wait_keys == 'right' and rot * rndpos[0][0] < 0):
                    judge = 1  # correct
                    react_time_stop = time.time()
                elif (wait_keys == 'left' and rot * rndpos[0][0] < 0) or (
                        wait_keys == 'right' and rot * rndpos[0][0] > 0):
                    judge = 0  # incorrect
                    react_time_stop = time.time()
                elif wait_keys == 'left' == 'escape':
                    config_tools.write_xrl(self.subject, break_info='userbreak')
                    core.quit()

        react_time = react_time_stop - react_time_start

        return judge, react_time, trial_time_start

    def run_session(self):

        path = os.path.join(self.res_dir, self.subject)
        if not os.path.exists(path):
            os.makedirs(path)
        psydat_path = os.path.join(path, 'psydat')
        if not os.path.exists(psydat_path):
            os.makedirs(psydat_path)

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
                                                staircase=prior_handler, extraInfo=cond, grain=0.02)
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
                direction = (-1) ** (cond['label'].endswith('m'))  # direction as -1 if for minus stim
                rot = rot * direction  # rotation for this trial
                judge, react_time, trial_time_start = self.run_trial(rot, cond, count)

                # check whether the theta is valid - if not, the rotation given by staircase should be corrected by
                # realizable values
                valid_theta = np.round(np.load(self.hue_list), decimals=1)

                disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                stair_test = cond['standard'] + stairs._nextIntensity * direction
                if stair_test < 0:
                    stair_test += 360
                disp_test = self.take_closest(valid_theta, stair_test)
                disp_intensity = disp_test - disp_standard
                if disp_intensity > 300:
                    disp_intensity = (disp_test + disp_standard) - 360
                stairs.addResponse(judge, abs(disp_intensity))

                xpp.task(count, cond, rot, float(disp_intensity), judge, react_time, trial_time_start)

                if 'escape' in event.waitKeys():
                    config_tools.write_xrl(self.subject, break_info='userbreak')
                    core.quit()

            config_tools.write_xrl(self.subject, xls_file=xlsname)
            stairs.saveAsExcel(xlsname)  # save results
            misc.toFile(os.path.join(psydat_path, self.idx + self.param['noise_condition'] + '.psydat'), stairs)

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
                    direction = (-1) ** (
                        cur_handler.extraInfo['label'].endswith('m'))  # direction as -1 if for minus stim

                    if cur_handler._nextIntensity <= 0.2 or cur_handler._nextIntensity >= 10.0:
                        sys.exit("Hue difference is out of range! Please enlarge the testing range or take more training!")

                    rot = cur_handler._nextIntensity * direction  # rotation for this trial
                    if trial_n >= 5:  # avoid repeating an intensity more than 3 times
                        last_rots = [np.round(r, decimals=1) for r in
                                     [rot_all_disp[handler_idx][trial_n-1],
                                      rot_all_disp[handler_idx][trial_n-2],
                                      rot_all_disp[handler_idx][trial_n-3]]]
                        last_resp = [judge_all[handler_idx][trial_n-1],
                                     judge_all[handler_idx][trial_n-2],
                                     judge_all[handler_idx][trial_n-3]]
                        if last_rots[0] == last_rots[1] == last_rots[2] \
                                and last_resp[0] == last_resp[1] == last_resp[2]:
                            if cur_handler._nextIntensity > 0.5:
                                rot = (cur_handler._nextIntensity - 0.5) * direction
                                print('Intensity decreases by 0.5!')
                            if cur_handler._nextIntensity <= 0.5:
                                rot = (cur_handler._nextIntensity + 0.5) * direction
                                print('Intensity increases by 0.5!')
                    cond = cur_handler.extraInfo
                    judge, react_time, trial_time_start = self.run_trial(rot, cond, count)

                    if len(rot_all) <= handler_idx:
                        rot_all.append([])
                    rot_all[handler_idx].append(rot)

                    if len(judge_all) <= handler_idx:
                        judge_all.append([])
                    judge_all[handler_idx].append(judge)

                    valid_theta = np.round(np.load(self.hue_list), decimals=1)
                    disp_standard = self.take_closest(valid_theta, cond['standard'])
                    stair_test = cond['standard'] + rot  # calculated test hue for this trial
                    if stair_test < 0:
                        stair_test += 360
                    disp_test = self.take_closest(valid_theta, stair_test)  # actual displayed test hue for this trial

                    disp_intensity = disp_test - disp_standard  # actual displayed hue difference
                    if disp_intensity > 300:
                        disp_intensity = (disp_test + disp_standard) - 360

                    cur_handler.addResponse(judge,
                                            abs(disp_intensity))  # only positive number is accepted by addResponse

                    if len(rot_all_disp) <= handler_idx:  # add displayed intensities
                        rot_all_disp.append([])
                    rot_all_disp[handler_idx].append(disp_intensity)

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

                    xpp.task(count, cond, rot, disp_intensity, judge, react_time, trial_time_start)

                    if 'escape' in event.waitKeys():
                        config_tools.write_xrl(self.subject, break_info='userbreak')
                        core.quit()

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
                file_name = os.path.join(psydat_path,
                                         self.idx + self.param['noise_condition'] + cur_handler.extraInfo['label'])
                misc.toFile(file_name + '.psydat', cur_handler)
                if isinstance(cur_handler, data.PsiHandler):
                    cur_handler.savePosterior(file_name + '.npy')


def run_exp(subject, par_file_path=None, cfg_file_path=None, res_dir=None, priors_file_path=None):
    if par_file_path:
        par_files = par_file_path
    else:
        sys.exit("Please set experiment parameters!")

    if cfg_file_path is None:
        cfg_file_path = 'config/expconfig.yaml'

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


# run_exp(subject='psuedo', par_file_path=['config/cn2_LL_correct.yaml'], cfg_file_path='config/expconfig_8bit.yaml')

# """ run experiment in bash """
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--subject')
#     parser.add_argument('--par_file', nargs='*')
#     parser.add_argument('--cfg_file')
#     parser.add_argument('--results_dir')
#     parser.add_argument('--priors_file')
#
#     args = parser.parse_args()
#     subject = args.subject
#     par_file = args.par_file
#     cfg_file = args.cfg_file
#     results_dir = args.results_dir
#     priors_file = args.priors_file
#     run_exp(subject, par_file, cfg_file, results_dir, priors_file)
