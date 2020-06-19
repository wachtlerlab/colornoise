#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
This module contains all writing and reading functions for config files in /config folder.

Functions for writing:
    class ParWriter: *.par - parameters of stimuli
    class writexpp: *.xpp - records of each single session
    class writexrl: *.xrl - records of all pairs of parameters and sessions belong to one subject

Functions for reading:
    class readpar(): *.par - parameters of stimuli
                    it includes readparam() and readstairs()

@author: yannansu
"""

import os as os
import numpy as np

if not os.path.exists('config'):
    os.makedirs('config')


class ParWriter:
    """
    Parameters writer for the par-files
    """

    def __init__(self, hue_num=8, min_val=1, max_val=10):
        self.hue_num = hue_num
        self.theta = np.linspace(0, 360, self.hue_num, endpoint=False)
        self.stimulus = [dict() for x in range(len(self.theta) * 2)]
        for idx, x in enumerate(np.repeat(self.theta, 2)):
            idx += 1
            self.stimulus[idx - 1]['theta'] = x
            self.stimulus[idx - 1]['minVal'] = min_val
            self.stimulus[idx - 1]['maxVal'] = max_val
            if idx % 2:
                self.stimulus[idx - 1]['label'] = 'hue_' + str(int((idx + 1) / 2)) + 'p'
            else:
                self.stimulus[idx - 1]['label'] = 'hue_' + str(int(idx / 2)) + 'm'

    def write(self, file_path, method, start_val=5.0, step_type=None, up_down=None, p_threshold=None, step_size=None,
              seed=42):
        """
        Write parameters to a par-file.

        :param file_path:   par-file path
        :param method:      'simple', 'quest', 'psi', 'grid'
        :param start_val:   start value for updown and quest methods
        :param step_type:   'db', 'lin', 'log' (None if method is not 'simple')
        :param up_down:     tuple with the up-down rule settings (up, down)
        :param seed:        seed for random permutation of the stimuli
        :param p_threshold: targeting probability threshold for the quest method
        :param step_size:   step size for the grid method
        """
        with open(file_path, 'w+') as f:

            # this part can and should be read
            f.write('noise_condition: L-H\n')
            f.write('sigma: 2\n\n')   # watch out the value!

            # this part is currently not read for running experiments; at moment it is only for documentation
            # because usually you do not need to change the display
            f.write('leftRef.pos: [-5, 2.5]\nrightRef.pos: [5, 2.5]\n')
            f.write('standard.xlim: [-1.5, 1.5]\nstandard.ylim: [1, 4]\n')
            f.write('test.xlim: [-1.5, 1.5]\ntest.ylim: [-4, -1]\n')
            f.write('patchsize: 0.75\n')
            f.write('npatch: 16\n\n')

            # this part can and should be read
            f.write('c: 0.12\nsscale: 2.6\ndlum: 0\n\n')

            np.random.permutation(seed)
            stim = np.random.permutation(self.stimulus)

            for idx, x in enumerate(stim):
                f.write('stimulus: {}\n'.format(idx))
                f.write('label: {}\n'.format(x['label']))
                f.write('standard: {}\n'.format(x['theta']))
                f.write('leftRef: {}\nrightRef: {}\n'.format(x['theta'] + 10, x['theta'] - 10))

                if 'minVal' in x:
                    f.write('minVal: {}\n'.format(x['minVal']))
                if 'maxVal' in x:
                    f.write('maxVal: {}\n'.format(x['maxVal']))

                if method == 'simple':
                    f.write('startVal: {}\n'.format(start_val))
                    f.write('stairType: simple\n')
                    f.write('nReversals: 2\n')
                    f.write('stepSizes: 2, 1\n')
                    f.write('nUp: {}\nnDown: {}\n'.format(up_down[0], up_down[1]))
                    f.write('stepType: {}\n\n'.format(step_type))

                elif method == 'quest':
                    f.write('startVal: {}\n'.format(start_val))
                    f.write('stairType: quest\n')
                    f.write('startValSd: 10.0\n')
                    f.write('pThreshold: {}\n\n'.format(p_threshold))

                elif method == 'psi':
                    f.write('stairType: psi\n\n')

                elif method == 'grid':
                    f.write('stepSize: {}\n'.format(step_size))
                    f.write('stairType: grid\n\n')

        f.close()


# ParWriter(hue_num=4).write('config/methods/ll_4x2st_50tr_updown.par', 'simple', step_type='lin', up_down=(1, 3))
# ParWriter(hue_num=4).write('config/methods/ll_4x2st_50tr_quest.par', 'quest', p_threshold=0.75)
# ParWriter(hue_num=4).write('config/methods/ll_4x2st_50tr_psi.par', 'psi')
# ParWriter(hue_num=4, min_val=0.1, max_val=5).write('config/methods/ll_4x2st_50tr_grid.par', 'grid', step_size=0.1)

# ParWriter(hue_num=8, min_val=0.1, max_val=5).write('config/simulation/ll_8x2st_grid.par', 'grid', step_size=0.1)
# ParWriter(hue_num=8, min_val=1, max_val=5).write('config/simulation/ll_8x2st_updown.par', 'simple', start_val=3,
#                                                  step_type='lin', up_down=(1, 3))
# ParWriter(hue_num=8, min_val=0.1, max_val=5).write('config/simulation/ll_8x2st_quest.par', 'quest', start_val=3,
#                                                    p_threshold=0.75)
# ParWriter(hue_num=8, min_val=0.1, max_val=5).write('config/simulation/ll_8x2st_psi.par', 'psi')


# ====== tests =====
# ParWriter(hue_num=8, min_val=1, max_val=10).write('config/test_updown.par', 'simple', start_val=5, step_type='lin', up_down=(1, 3), seed=42)
# ParWriter(hue_num=8, min_val=1, max_val=10).write('config/test_quest_LH.par', 'quest', start_val=3, p_threshold=.75, seed=42)
# ParWriter(hue_num=8, min_val=1, max_val=10).write('config/test_psi.par', 'psi', seed=42)


class XppWriter:
    """
    Writer for output tracking files *.xpp for each session
    """

    def __init__(self, subject, idx, noise_condition, dir_path='config'):
        self.subject = subject
        self.idx = idx
        self.noise_con = noise_condition
        self.f = open(os.path.join(dir_path, subject + idx + '.xpp'), 'w+')

    def head(self, par_file, trial_duration):
        self.f.write('{}.xrl\n'.format(self.subject))
        self.f.write('{}\n'.format(self.idx))

        self.f.write('stimparfl: {}\n'.format(par_file))  # copy info from paramfiles
        with open(par_file, 'r') as pf:
            self.f.writelines(line for line in pf)

        self.f.write('\ntrial duration: {}\n'.format(trial_duration))

        self.f.write('\ntask: \n')  # make a head of a table thing
        self.f.write('trl  stim  standard  test  diff  disp_intensity leftRef  rightRef  startVal  response  time\n')

    def task(self, count, rot, disp_intensity, cond, judge, time):  # keep records: one line one trial
        start_val = cond['startVal'] if 'startVal' in cond else None

        self.f.write(str(count) + '  '
                     + str(cond['stimulus']) + '  '
                     + str(cond['standard']) + '  '
                     + str(cond['standard'] + rot) + '  '
                     + str(rot) + '  '
                     + "{:.1f}".format(disp_intensity) + '  '
                     + str(cond['leftRef']) + '  '
                     + str(cond['rightRef']) + '  '
                     + str(start_val) + '  '
                     + str(judge) + '  '
                     + str(time) + '\n')
        self.f.flush()


class XppReader:
    """
    Reader for xpp files describing single session
    """

    def __init__(self, xpp_file_path):
        self.xpp_file_path = xpp_file_path

    def read(self):
        trial_duration = None
        trials = []
        with open(self.xpp_file_path) as xpp_file:
            steps_started = False
            for line in xpp_file:
                if line.startswith('trial duration'):
                    trial_duration = line.rstrip('\n').split()[-1]
                    trial_duration = str2float(trial_duration)
                elif line.startswith('task'):
                    steps_started = True
                    next(xpp_file)
                elif steps_started:
                    parts = line.rstrip('\n').split()
                    trials.append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]),
                                   float(parts[5]), float(parts[6]), str2float(parts[7]), int(parts[8]),
                                   float(parts[9])))
        return trials, trial_duration

    def read_customized(self, term):

        nth = None
        N = None
        xpp_file = open(self.xpp_file_path, 'r+')
        lines = xpp_file.readlines()  #
        for idx, line in enumerate(lines):
            if line.startswith('task'):
                nextline = lines[idx+1].split()
                nth = [i for i, word in enumerate(nextline) if word == term][0]
                N = idx + 2
                break

        if nth is None or N is None:
            print("The given term is not found!")
            data = None

        data = [str2float(l.split()[nth]) for l in lines[N:-1]]

        return data


def str2float(float_str):
    try:
        return float(float_str)
    except ValueError:
        return None


class XrlWriter:
    """
    Writer for *.xrl files: put all pairs of paramfiles and xpp files together for single subjects
    """

    def __init__(self, subject, parafile, xppfile, dir_path='config'):
        self.subject = subject
        self.pf = parafile
        self.xpp = xppfile
        self.f = open(os.path.join(dir_path, self.subject + '.xrl'), 'a')  # append instead of rewriting

    def mk_xrl(self):
        self.f.write(self.pf + ", " + self.xpp + ", ")

    def add_break(self, break_info):
        self.f.write(break_info + '\n')

    def add_data(self, xls_file):
        self.f.write(xls_file + '\n')


class XrlReader:
    """
    Reader for xrl-files describing multiple sessions
    """

    def __init__(self, xrl_file_path):
        self.xrl_file_path = xrl_file_path

    def read(self):
        sessions = {}
        with open(self.xrl_file_path) as xrl_file:
            for line in xrl_file:
                parts = line.rstrip('\n').split(', ')
                sessions[parts[1]] = (parts[0], parts[2])
        return sessions


# every time add/delete lines in writepar(), remember to check this part, especially readstair()!!!
class ParReader:
    """
    Parameters reader for *.par files
    """

    def __init__(self, par_file):
        self.par_file = par_file

    def str2float(self, s):
        try:
            float(s)
            return float(s)
        except ValueError:
            if s[0] == '[':
                s = s[1:-1]
            return [float(x) for x in s.split(', ')]

    def find_param(self, lines, paramname):
        for line in lines:
            if line.startswith(paramname):
                x = line.split(': ')[-1].strip()
                try:
                    float(x)
                    return float(x)
                except ValueError:
                    return x

    def read_param(self):
        param = dict()

        with open(self.par_file) as pf:
            lines = pf.read().splitlines()
            param['condition'] = self.find_param(lines, 'noise_condition')
            param['sigma'] = self.find_param(lines, 'sigma')
            param['c'] = self.find_param(lines, 'c')
            param['sscale'] = self.find_param(lines, 'sscale')
            param['dlum'] = self.find_param(lines, 'dlum')

        return param

    def read_stair(self):
        import re

        with open(self.par_file) as pf:
            # condnum = int(''.join(re.findall(r'[1-9]', self.par_file)))  # join all single numerical chars
            lines = pf.read().splitlines()
            num = 0
            conditions = []

            conidx = np.where([l.startswith('stimulus') == 1 for l in lines])  # the starting index of each condition
            conidx = conidx[0] - 1  # get rid of stupid tuple and convert to python indexing
            conlen = conidx[1] - conidx[0]  # the line length of each condition

            for lidx in conidx:
                # join all lines of a single condition, rearrange them in single lines, and remove ":";
                condition = ('\n'.join(lines[lidx:lidx + conlen])).replace(':', '')
                # find all non-white space + chars + white space, put all info into a dictionary
                condition = dict(re.findall(r'(\S+)\s+(.+)', condition))
                for key, val in condition.items():
                    # be careful about labels containing non-numerical chars
                    if key != 'label' and key != 'stepType' and key != 'stairType':
                        val = self.str2float(val)
                    condition[key] = val

                conditions.append(condition)
                num += 1

        # if condnum != num:
        #     print('Error!!! The number of conditions is not correct in the parameter file!')

        return conditions
