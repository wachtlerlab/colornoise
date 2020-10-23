# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
""" 
Created on 25.09.20

@author yannan
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
            res_dir = 'data/' + subject + '/noise_test'
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
    def patch_ref(self, theta, pos):  # reference patches
        ref = visual.Circle(win=self.win,
                            units='deg',
                            pos=pos,
                            radius=self.cfg['ref_size'],
                            fillColorSpace=self.ColorSpace,
                            lineColorSpace=self.ColorSpace)
        ref.fillColor = self.ColorPicker.newcolor(theta=theta)[1]
        ref.lineColor = ref.fillColor
        return ref

    def patch_stim(self, xlim, ylim):  # standard and test stimuli
        n = int(np.sqrt(self.patch_nmb))
        pos = [[x, y]
               for x in np.linspace(xlim[0], xlim[1], n)
               for y in np.linspace(ylim[0], ylim[1], n)]
        patch = visual.ElementArrayStim(win=self.win,
                                        units='deg',
                                        fieldSize=self.cfg['field_size'],
                                        xys=pos,
                                        nElements=self.patch_nmb,
                                        elementMask='circle',
                                        elementTex=None,
                                        sizes=self.cfg['patch_size'],
                                        colorSpace=self.ColorSpace)
        return patch


    """color noise & noise conditions"""

    def rand_color(self, theta, std, npatch):  # generate color noise
        noise = np.random.normal(theta, std, npatch)
        color = [self.ColorPicker.newcolor(theta=n) for n in noise]
        sml, rgb = zip(*color)
        return sml, rgb

    def choose_con(self, standard, test, std):  # choose noise condition
        sColor = None
        tColor = None
        if self.param['noise_condition'] == 'L-L':  # low - low noise
            sColor = self.ColorPicker.newcolor(theta=standard)[1]
            tColor = self.ColorPicker.newcolor(theta=test)[1]

        elif self.param['noise_condition'] == 'L-H':  # low - high noise: only test stimulus has high noise
            sColor = self.ColorPicker.newcolor(theta=standard)[1]
            tColor = self.rand_color(test, std, self.patch_nmb)[1]

        elif self.param['noise_condition'] == 'H-H':  # high - high noise
            sColor = self.rand_color(standard, std, self.patch_nmb)[1]
            tColor = self.rand_color(test, std, self.patch_nmb)[1]

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
    def run_trial(self, std, cond, count):

        ref = self.patch_ref(theta=cond['ref'],
                             pos=self.cfg['ref.pos'])

        # randomly assign patch positions: upper (+) or lower (-)
        patchpos = [self.cfg['standard.ylim'],
                    self.cfg['test.ylim']]
        rndpos = patchpos.copy()
        np.random.shuffle(rndpos)

        sPatch = self.patch_stim(self.cfg['standard.xlim'], rndpos[0])
        tPatch = self.patch_stim(self.cfg['test.xlim'], rndpos[1])

        # set colors of two stimuli
        standard = cond['standard']  # standard should be fixed
        test = cond['test']
        sPatch.colors, tPatch.colors = self.choose_con(standard, test, std)

        # fixation cross
        fix = visual.TextStim(self.win, text="+", units='deg', pos=[0, 0], height=0.5, color='black',
                              colorSpace=self.ColorSpace)
        # number of trial
        num = visual.TextStim(self.win, text="trial " + str(count), units='deg', pos=[12, -10], height=0.4,
                              color='black', colorSpace=self.ColorSpace)

        trial_time_start = time.time()

        fix.draw()
        num.draw()
        ref.draw()
        sPatch.draw()
        tPatch.draw()
        self.win.flip()
        core.wait(self.trial_dur)

        judge = None
        react_time_stop = -1
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

        # If response is given during the mask
        if judge is None:
            kb = keyboard.Keyboard()
            get_keys = kb.getKeys(['up', 'down', 'escape'])  # if response during the checkerboard
            if ('up' in get_keys and rndpos[1][0] > 0) or ('down' in get_keys and rndpos[1][0] < 0):
                judge = 1  # correct
                react_time_stop = time.time()
            elif ('up' in get_keys and rndpos[1][0] < 0) or ('down' in get_keys and rndpos[1][0] > 0):
                judge = 0  # incorrect
                react_time_stop = time.time()
            if 'escape' in get_keys:
                config_tools.write_xrl(self.subject, break_info='userbreak')
                core.quit()

        # Refresh and wait for response (if no response was given in the pause mode or during mask)
        self.win.flip()
        fix.draw()
        self.win.flip()

        if judge is None:  # if response after the checkerboard
            for wait_keys in event.waitKeys():
                if (wait_keys == 'up' and rndpos[1][0] > 0) or (
                        wait_keys == 'down' and rndpos[1][0] < 0):
                    judge = 1  # correct
                    react_time_stop = time.time()
                elif (wait_keys == 'up' and rndpos[1][0] < 0) or (
                        wait_keys == 'down' and rndpos[1][0] > 0):
                    judge = 0  # incorrect
                    react_time_stop = time.time()
                elif wait_keys == 'escape':
                    config_tools.write_xrl(self.subject, break_info='userbreak')
                    core.quit()

        react_time = react_time_stop - react_time_start

        return judge, react_time, trial_time_start

    def run_session(self):

        path = self.res_dir
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
        xpp = config_tools.WriteXpp(self.subject, self.idx, dir_path=self.res_dir)
        xpp_file = xpp.head(self.cfg_file, self.par_file)
        config_tools.write_xrl(self.subject, cfg_file=self.cfg_file, par_file=self.par_file, xpp_file=xpp_file, dir_path=self.res_dir)

        xlsname = path + '/' + self.idx + self.param['noise_condition'] + '.xlsx'

        """ running staircase """

        if isinstance(stairs, data.MultiStairHandler):
            # start running the staircase using the MultiStairHandler for the up-down method
            count = 0

            for rev_std, cond in stairs:
                count += 1
                # direction = (-1) ** (cond['label'].endswith('m'))  # direction as -1 if for minus stim
                # rot = rot * direction  # rotation for this trial
                std = 10 - rev_std
                judge, react_time, trial_time_start = self.run_trial(std, cond, count)

                # check whether the theta is valid - if not, the rotation given by staircase should be corrected by
                # realizable values
                # valid_theta = np.round(np.load(self.hue_list), decimals=1)

                # disp_standard = self.take_closest(valid_theta, cond['standard'])  # theta actually displayed
                # stair_test = cond['standard'] + stairs._nextIntensity * direction
                # if stair_test < 0:
                #     stair_test += 360
                # disp_test = self.take_closest(valid_theta, stair_test)
                # disp_intensity = disp_test - disp_standard
                # if disp_intensity > 300:
                #     disp_intensity = (disp_test + disp_standard) - 360
                stairs.addResponse(judge, rev_std)

                xpp.task(count, cond, cond['test'], std, judge, react_time, trial_time_start)

                if 'escape' in event.waitKeys():
                    config_tools.write_xrl(self.subject, break_info='userbreak')
                    core.quit()

            config_tools.write_xrl(self.subject, xls_file=xlsname)
            stairs.saveAsExcel(xlsname)  # save results
            misc.toFile(os.path.join(psydat_path, self.idx + self.param['noise_condition'] + '.psydat'), stairs)

        elif isinstance(stairs, list):
            # start running the staircase using custom interleaving stairs for the quest and psi methods
            count = 0
            std_all = []
            # std_all_disp = []
            judge_all = []
            estimates = {s.extraInfo['label']: [] for s in stairs}

            for trial_n in range(self.trial_nmb):
                for handler_idx, cur_handler in enumerate(stairs):
                    count += 1

                    rev_std = cur_handler._nextIntensity
                    std = 10 - rev_std
                    cond = cur_handler.extraInfo
                    judge, react_time, trial_time_start = self.run_trial(std, cond, count)
                    xpp.task(count, cond, cond['test'], std, judge, react_time, trial_time_start)

                    if len(std_all) <= handler_idx:
                        std_all.append([])
                    std_all[handler_idx].append(std)

                    if len(judge_all) <= handler_idx:
                        judge_all.append([])
                    judge_all[handler_idx].append(judge)
                    cur_handler.addResponse(judge,
                                            rev_std)  # only positive number is accepted by addResponse

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

                    if 'escape' in event.waitKeys():
                        config_tools.write_xrl(self.subject, break_info='userbreak', dir_path=self.res_dir)
                        core.quit()

            config_tools.write_xrl(self.subject, xls_file=xlsname, dir_path=self.res_dir)

            # save results in xls-file
            workbook = xlsxwriter.Workbook(xlsname)
            for handler_idx, cur_handler in enumerate(stairs):
                worksheet = workbook.add_worksheet(cur_handler.extraInfo['label'])
                worksheet.write('A1', 'Reversal Intensities')
                worksheet.write('B1', 'Reversal Indices')
                worksheet.write('C1', 'All Intensities')
                worksheet.write('D1', 'All Responses')
                for i in range(len(std_all[handler_idx])):
                    worksheet.write('C' + str(i + 2), std_all[handler_idx][i])
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

# run_exp(subject='pseudo', par_file_path=['config/cn1x1_HH_nl_ysu.yaml'], cfg_file_path='config/expconfig.yaml')

""" run experiment in bash """
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
