#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python version 3.5.2

"""
This module contains all writing and reading functions for config files in /config folder.

Functions for writing:
    writepar: *.par - parameters of stimuli
    class writexpp: *.xpp - records of each single session
    class writexrl: *.xrl - records of all pairs of parameters and sessions belong to one subject

Functions for reading:
    readpar: *.par - parameters of stimuli
    readstairs: *.par - parameters of stimuli; especially staircases

@author: yannansu
"""

import os as os
import numpy as np

if not os.path.exists('config'):
    os.makedirs('config')

huenum = 8

theta = np.linspace(0, 360, huenum, endpoint=False)

stimulus = [dict() for x in range(len(theta) * 2)]

for idx, x in enumerate(np.repeat(theta, 2)):
    idx += 1
    stimulus[idx - 1]['theta'] = x
    if idx % 2:
        stimulus[idx - 1]['label'] = 'hue_' + str(int((idx + 1) / 2)) + 'p'
        stimulus[idx - 1]['startVal'] = 5  # adjust this value
        stimulus[idx - 1]['minVal'] = 1
    else:
        stimulus[idx - 1]['label'] = 'hue_' + str(int(idx / 2)) + 'm'
        stimulus[idx - 1]['startVal'] = - 5
        stimulus[idx - 1]['maxVal'] = -1

"""write params into *.par file; params as MultiStairConditions.xlsx"""


def writepar(stim, name, stepType, quest=None):
    # stepType:'db', 'lin', 'log'
    # if quest is True, a QUEST staircase method will be used.
    with open('config/cn' + str(huenum * 2) + name + '.par', 'w+') as f:

        # this part can and should be read
        f.write('noise_condition: L-L' + '\n')
        f.write('sigma: 2' + '\n' + '\n')

        # this part is currently not read for running experiments; at moment it is only for documentation
        # because usually you do not need to change the display
        f.write('leftRef.pos: [-5, 2.5]' + '\n' + 'rightRef.pos: [5, 2.5]' + '\n')
        f.write('standard.xlim: [-1.5, 1.5]' + '\n' + 'standard.ylim: [1, 4]' + '\n')
        f.write('test.xlim: [-1.5, 1.5]' + '\n' + 'test.ylim: [-4, -1]' + '\n')
        f.write('patchsize: 0.75' + '\n')
        f.write('npatch: 16' + '\n' + '\n')

        # this part can ans should be read
        f.write('c: 0.12' + '\n' + 'sscale: 2.6' + '\n' + 'dlum: 0' + '\n' + '\n')

        for idx, x in enumerate(stim):
            f.write('stimulus: ' + str(idx) + '\n')
            f.write('label: ' + x['label'] + '\n')
            f.write('standard: ' + str(x['theta']) + '\n')
            f.write('leftRef: ' + str(x['theta'] + 10) + '\n' + 'rightRef: ' + str(x['theta'] - 10) + '\n')
            f.write('startVal: ' + str(x['startVal']) + '\n')

            if 'minVal' in x:
                f.write('minVal: ' + str(x['minVal']) + '\n')
            if 'maxVal' in x:
                f.write('maxVal: ' + str(x['maxVal']) + '\n')

            if quest:
                f.write('stairType: quest' + '\n')
                f.write('startValSd: 0.2' + '\n')
                f.write('pThreshold: 0.82' + '\n')
                f.write('gamma: 0.5' + '\n')
                f.write('beta: 0.01' + '\n' + '\n')

            else:
                f.write('stairType: simple' + '\n')
                f.write('nReversals: 2' + '\n')
                if x['startVal'] > 0 or stepType !='lin':
                    f.write('stepSizes: 2, 1' + '\n')
                else:
                    f.write('stepSizes: -2, -1' + '\n')
                f.write('nUp: 2' + '\n' + 'nDown: 3' + '\n')
                f.write('stepType: ' + stepType + '\n' + '\n')

    f.close()


"""read parameters from *.par files"""
# every time add/delete lines in writepar(), remember to check this part, especially readstair()!!!

def str2float(s):
    try:
        float(s)
        return float(s)
    except ValueError:
        if s[0] == '[':
            s = s[1:-1]
        return [float(x) for x in s.split(', ')]


def findparam(lines, paramname):
    for line in lines:
        if line.startswith(paramname):
            x = line.split(': ')[-1].strip()
            try:
                float(x)
                return float(x)
            except ValueError:
                return x


def readpara(parafile):
    param = dict()

    with open(parafile) as pf:
        lines = pf.read().splitlines()
        param['condition'] = findparam(lines, 'noise_condition')
        param['sigma'] = findparam(lines, 'sigma')
        param['c'] = findparam(lines, 'c')
        param['sscale'] = findparam(lines, 'sscale')
        param['dlum'] = findparam(lines, 'dlum')

    return param


def readstair(parafile):
    import re

    with open(parafile) as pf:
        condnum = int(''.join(re.findall(r'[1-9]', parafile)))  # join all single numerical chars
        lines = pf.read().splitlines()
        num = 0
        conditions = [None] * condnum

        conidx = np.where([l.startswith('stimulus') == 1 for l in lines])  # the starting index of each condition
        conidx = conidx[0] - 1  # get rid of stupid tuple and convert to python indexing
        conlen = conidx[1] - conidx[0] - 1  # the line length of each condition

        for lidx in conidx:
            condition = ('\n'.join(lines[lidx:lidx + conlen])).replace(':', '')  # join all lines of a single condition, rearrange them in single lines, and remove ":";
            condition = dict(re.findall(r'(\S+)\s+(.+)',
                                        condition))  # find all non-white space + chars + white space, put all info into a dictionary
            for key, val in condition.items():
                if key != 'label' and key != 'stepType' and key != 'stairType':  # be careful about labels containing non-numerical chars
                    val = str2float(val)
                condition[key] = val

            conditions[num] = condition
            num += 1

    if condnum != num:
        print('Error!!! The number of conditions is not correct in the parameter file!')

    return conditions


"""write output tracking file *.xpp for each session"""


class writexpp():
    def __init__(self, subject, idx, noise_condition):
        self.subject = subject
        self.idx = idx
        self.noisecon = noise_condition
        self.f = open('config/' + subject + idx + '.xpp', 'w+')

    def head(self, parafile):
        self.f.write(self.subject + '.xrl' + '\n')
        self.f.write(self.idx + '\n')

        self.f.write('stimparfl: ' + parafile + '\n')  # copy info from paramfiles
        with open(parafile, 'r') as pf:
            self.f.writelines(line for line in pf)

        self.f.write('\n' + 'task: ' + '\n')  # make a head of a table thing
        self.f.write('trl  stim  standard  test  diff  leftRef  rightRef  startVal  response' + '\n')

    def task(self, count, rot, cond, judge):  # keep records: one line one trial

        self.f.write(str(count) + '  '
                     + str(cond['stimulus']) + '  '
                     + str(cond['standard']) + '  '
                     + str(cond['standard'] + rot) + '  '
                     + str(rot) + '  '
                     + str(cond['leftRef']) + '  '
                     + str(cond['rightRef']) + '  '
                     + str(cond['startVal']) + '  '
                     + str(judge) + '\n')


"""write *.xrl files: put all pairs of paramfiles and xpp files together for single subjects"""


class writexrl():
    def __init__(self, subject, parafile, xppfile):
        self.subject = subject
        self.pf = parafile
        self.xpp = xppfile
        self.f = open('config/' + self.subject + '.xrl', 'a')  # append instead of rewriting

    def mkxrl(self):
        self.f.write(self.pf + ", " + self.xpp + ", ")

    def addbreak(self, breakinfo):
        self.f.write(breakinfo + '\n')

    def adddata(self, xlsxfile):
        self.f.write(xlsxfile + '\n')


"""run: generate configuration files; one time is enough"""
#
# # sequential
# writepar(stimulus, 'seq')
#
# # pseudo-random with specific seed
# np.random.seed(10)
# rnd_a = np.random.permutation(stimulus)
# writepar(rnd_a, 'rnd_a')
#
# np.random.seed(20)
# rnd_b = np.random.permutation(stimulus)
# writepar(rnd_b, 'rnd_b')
#
# # c and d use different start values and step sizes
# np.random.seed(30)
# rnd_c_new = np.random.permutation(stimulus)
# writepar(rnd_c_new, 'rnd_c_new')
#
# np.random.seed(40)
# rnd_d = np.random.permutation(stimulus)
# writepar(rnd_d, 'rnd_d')

## new steptype with 'lin'

# np.random.seed(10)
# rnd_a = np.random.permutation(stimulus)
# writepar(rnd_a, 'rnd_a')

# ## back to db steptypes
# np.random.seed(20)
# rnd_b = np.random.permutation(stimulus)
# writepar(rnd_b, 'rnd_b')
# #
# np.random.seed(30)
# rnd_c = np.random.permutation(stimulus)
# writepar(rnd_c, 'rnd_c')

# np.random.seed(30)
# rnd_f = np.random.permutation(stimulus)
# writepar(rnd_f, 'rnd_f')

# np.random.seed(30)
# rndq_a = np.random.permutation(stimulus)
# writepar(rndq_a, 'rndq_a', quest=True)

# np.random.seed(30)
# rnd_g = np.random.permutation(stimulus)
# writepar(rnd_g, 'rnd_g')

# np.random.seed(10)
# rnd_h = np.random.permutation(stimulus)
# writepar(rnd_h, 'rnd_h')

##################################################
## back to lin steps, also control max and min values

# np.random.seed(10)
# rnd_a_lin = np.random.permutation(stimulus)
# writepar(rnd_a_lin, 'rnd_a_lin', 'lin', quest=None)