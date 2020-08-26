#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

# python version 3.7.6
""" 
Created on 13.07.20

This module contains all writing and reading functions for configuration files for the color-noise experiment.

Functions for writing:
    function write_cfg:     write experiment config file *.yaml
    function write_par:     write parameter file *.yaml
    class WriteXpp:         write session log file *.yaml
    function write_xrl:     write subject log file *.xrl

Functions for reading:
    function read_yml:      read all types of *.yaml
    function read_xrl:      read subject log file *.xrl

@author: yannansu
"""
import os
import numpy as np
import yaml


def read_yml(file_path):
    """
    Load and read a YAML file.

    :param file_path:   YAML file path
    :return:            a dictionary converted from YAML
    """
    with open(file_path) as file:
        par_dict = yaml.load(file, Loader=yaml.FullLoader)
    return par_dict


def write_cfg(file_path):
    """
    Write a configuration YAML file for experiment settings (monitor information, stimulus size and position, etc.).
    Usually it is not necessary to modify this file.
    
    :param file_path:
    """
    cfg_dict = {'monitor': {}}
    cfg_dict['monitor']['name'] = 'VIEWPixx_2000A'
    cfg_dict['monitor']['size'] = [1920, 1200]
    cfg_dict['monitor']['width'] = 48.4
    cfg_dict['monitor']['distance'] = 57
    cfg_dict['depthBits'] = 10

    cfg_dict['patch_nmb'] = 16
    cfg_dict['patch_size'] = 0.75
    cfg_dict['ref_size'] = 0.8
    cfg_dict['field_size'] = [4.0, 4.0]
    cfg_dict['leftRef.pos'] = [-5, 2.5]
    cfg_dict['rightRef.pos'] = [5, 2.5]
    cfg_dict['standard.xlim'] = [-1.5, 1.5]
    cfg_dict['standard.ylim'] = [1, 4]
    cfg_dict['test.xlim'] = [-1.5, 1.5]
    cfg_dict['test.ylim'] = [-4, -1]

    cfg_dict['trial_nmb'] = 20
    cfg_dict['trial_dur'] = 1.5

    with open(file_path, 'w') as file:
        yaml.dump(cfg_dict, file, default_flow_style=False, sort_keys=False)


def write_par(file_path, noise, method, seed=42, hue_num=8, min_max=None, start_val=3.0, step_type=None,
              up_down=None, p_threshold=0.63):
    """
    Write parameters to a YAML file.

    :param file_path:   par-file path
    :param noise:       'L-L', 'L-H', 'H-H'
    :param method:      'simple', 'quest', 'psi'
    :param seed:        seed for random permutation of the stimuli
    :param hue_num:     hue numbers
    :param min_max:     [min value, max value] for simple and quest methods
    :param start_val:   start value for simple and quest methods
    :param step_type:   'db', 'lin', 'log' (None if method is not 'simple')
    :param up_down:     tuple with the up-down rule settings (up, down)
    :param p_threshold: targeting probability threshold for the quest method
    """

    if min_max is None:
        min_max = [0.2, 10.0]
    if up_down is None:
        up_down = [None, None]
    """generate stimuli"""
    theta = np.linspace(0, 360, hue_num, endpoint=False)
    stimulus = [dict() for x in range(len(theta) * 2)]
    for idx, x in enumerate(np.repeat(theta, 2)):
        idx += 1
        stimulus[idx-1]['theta'] = x
        if idx % 2:
            stimulus[idx - 1]['label'] = 'hue_' + str(int((idx + 1) / 2)) + 'p'
        else:
            stimulus[idx - 1]['label'] = 'hue_' + str(int(idx / 2)) + 'm'

    """basic config"""
    par_dict = {'c': 0.12,
                'sscale': 2.6,
                'dlum': 0,
                'noise_condition': noise,
                'sigma': 2}

    """stimulus permutation"""
    np.random.permutation(seed)
    stim = np.random.permutation(stimulus)

    for idx, x in enumerate(stim):
        stim_num = 'stimulus_' + str(idx)
        par_dict[stim_num] = {}
        par_dict[stim_num]['label'] = x['label']
        par_dict[stim_num]['standard'] = float(x['theta'])
        par_dict[stim_num]['leftRef'] = float(x['theta'] + 10)
        par_dict[stim_num]['rightRef'] = float(x['theta'] - 10)
        par_dict[stim_num]['stairType'] = method
        # if x['label'] in ['hue_3m', 'hue_3p', 'hue_4m', 'hue_7p', 'hue_8m']:
        #     par_dict[stim_num]['startVal'] = 1.0
        # else:
        #     par_dict[stim_num]['startVal'] = start_val
        par_dict[stim_num]['startVal'] = start_val
        par_dict[stim_num]['min_val'] = min_max[0]
        par_dict[stim_num]['max_val'] = min_max[1]

        """specify for simple method"""
        par_dict[stim_num]['stepType'] = step_type
        par_dict[stim_num]['nReversals'] = 2
        par_dict[stim_num]['stepSizes'] = [2, 1]
        par_dict[stim_num]['nUp'] = up_down[0]
        par_dict[stim_num]['nDown'] = up_down[1]

        """specify for quest method"""
        par_dict[stim_num]['startValSd'] = 12
        par_dict[stim_num]['pThreshold'] = p_threshold  # typical value is 0.63, which is equivalent to a 1 up 1 down standard staircase

    with open(file_path, 'w') as file:
        yaml.dump(par_dict, file, default_flow_style=False, sort_keys=False)


class WriteXpp:
    def __init__(self, subject, idx, dir_path='data'):
        """
        Create a log YAML file for one session.

        :param subject:     subject name [string]
        :param idx:         date and time [string]
        :param dir_path:    the directory for storing. default: data/subject
        """
        if not os.path.exists('data/' + subject):
            os.makedirs('data/' + subject)

        self.idx = idx
        self.file_path = os.path.join(dir_path, subject, subject + idx + '.yaml')
        self.f = open(self.file_path, 'w+')

    def head(self, cfg_file, par_file):
        """
        Copy the metadata from experiment config and parameter file into the head part of this log file.

        :param cfg_file:    experiment config file path
        :param par_file:    parameter file path
        :return:            the log file path
        """
        info = {'time': self.idx,
                'cfg_file': cfg_file,
                'par_file': par_file}
        # yaml.safe_dump(info, self.f, default_flow_style=False, sort_keys=False)

        cfg_dict = read_yml(cfg_file)
        par_dict = read_yml(par_file)
        yaml.safe_dump({**info, **cfg_dict, **par_dict}, self.f, default_flow_style=False, sort_keys=False)
        return self.file_path

    def task(self, count, cond, rot, disp_intensity, judge, react_time, trial_stamp):
        """
        Append log of every single trials in iterations to this log file.

        :param count:           count of this trial
        :param stim:            stimulus of this trial
        :param cond:            condition of this trial
        :param rot:             the calculated rotation of hue angle
        :param disp_intensity:  the actual and realizable rotation of hue angle
        :param judge:           correctness, 0 or 1
        :param t:               reaction time
        """
        trial_dict = {}
        this_trial = 'trial_' + str(count)
        trial_dict[this_trial] = {}
        trial_dict[this_trial]['count'] = count
        trial_dict[this_trial]['stimulus'] = cond['stimulus']
        trial_dict[this_trial]['standard_stim'] = float(cond['standard'])
        trial_dict[this_trial]['test_stim'] = float(cond['standard'] + rot)
        trial_dict[this_trial]['calculated_intensity'] = float(rot)
        trial_dict[this_trial]['actual_intensity'] = float(round(disp_intensity, 1))
        trial_dict[this_trial]['judge'] = judge
        trial_dict[this_trial]['react_time'] = react_time
        trial_dict[this_trial]['trial_time_stamp'] = trial_stamp
        yaml.safe_dump(trial_dict, self.f, default_flow_style=False, sort_keys=False)
        self.f.flush()


def write_xrl(subject, cfg_file=None, par_file=None, xpp_file=None, break_info=None, xls_file=None, dir_path='data'):
    """
    Write a subject log file *.xrl that pairs parameter files with corresponding session log files, in plain text style.
    If the session is completed, the data file path will be appended,
    otherwise 'userbreak' will be documented,

    :param subject:     subject name[string] for creating subject.xrl
    :param cfg_file:    experiment config YAML path
    :param par_file:    parameter YAML path
    :param xpp_file:    xpp YAML path
    :param break_info:  break information, e.g. "userbreak"
    :param xls_file:    data xlsx file path
    :param dir_path:    the directory for storing. default: data/subject
    """
    xrl_file = open(os.path.join(dir_path, subject, subject + '.xrl'), 'a')  # append instead of rewriting
    if cfg_file is not None and par_file is not None and xpp_file is not None:
        xrl_file.write(cfg_file + ", " + par_file + ", " + xpp_file + ", ")
    if break_info:
        xrl_file.write(break_info + '\n')
    if xls_file:
        xrl_file.write(xls_file + '\n')


def read_xrl(xrl_file):
    """
    Read subject log file *.xrl.

    :param xrl_file:    xrl file path
    :return:            a dictionary consisting of completed sessions: sessions[xpp_filename] = (par_filename, data_filename)
    """
    sessions = {}
    with open(xrl_file) as xrl_file:
        for line in xrl_file:
            parts = line.rstrip('\n').split(', ')
            sessions[parts[2]] = (parts[1], parts[3])
    return sessions


"""example"""


# write_cfg('metadata_examples/expconfig_example.yaml')
# write_par('metadata_examples/parameter_example.yaml', 'L-L', 'quest')
# xpp = WriteXpp('subject_example', '20200000T0000')
# xpp.head('metadata_examples/expconfig_example.yaml', 'metadata_examples/parameter_example.yaml')
# pseudo_cond = {'stimulus':'stimulus_0', 'label': 'hue_5p', 'standard': 180.0, 'leftRef': 190.0, 'rightRef': 170.0,
# 'stairType': 'quest', 'startVal': 5.0, 'min_val': 1, 'max_val': 10, 'stepType': None, 'nReversals': 2, 'stepSizes':
# [2, 1], 'nUp': None, 'nDown': None, 'startValSd': 10, 'pThreshold': None}
# xpp.task(1, pseudo_cond, 5, 5.1, 0, 4.6)
# write_xrl('subject_example', cfg_file='metadata_examples/expconfig_example.yaml', par_file='metadata_examples/parameter_example.yaml',
#           xpp_file='subject_example20200000T0000.yaml', break_info='userbreak')


def read_value(text_file, keywords, sep=':'):
    """

    :param text_file:       the path of text file
    :param keywords:        the keywords you are looking for [list]
    :param sep:             the separator
    :return:                the values corresponding to the keywords
    """
    file = open(text_file, "r", encoding='utf-8')
    lines = file.read().splitlines()
    for word in keywords:
        for line in lines:
            if line.lstrip().startswith(word):
                x = line.split(sep)[-1].strip()
                try:
                    float(x)
                    return float(x)
                except ValueError:
                    return x

# def xpp2yaml(xpp_file, yaml_file):
#     """
#     Convert existed task sections in xpp files to yaml file.
#     :param xpp_file:       xpp file path
#     :param yaml_file:      YAML file path
#     :return:
#     """
#     from genconfig import XppReader
#     trials, _ = XppReader(xpp_file).read()
#     dict = {}
#     for trl in trials:
#         subdict = 'trial_'+str(trl[0])
#         dict[subdict] = {}
#         dict[subdict]['count'] = trl[0]
#         dict[subdict]['stimulus'] = trl[1]
#         dict[subdict]['standard_stim'] = trl[2]
#         dict[subdict]['test_stim'] = trl[3]
#         dict[subdict]['calculated_intensity'] = trl[4]
#         dict[subdict]['actual_intensity'] = None
#         dict[subdict]['judge'] = trl[8]
#         dict[subdict]['time'] = None
#
#     with open(yaml_file, 'w') as file:
#         yaml.safe_dump(dict, file, default_flow_style=False, sort_keys=False)

# def par2yaml(par_file, yaml_file):
#     from genconfig import ParReader
#     param = ParReader(par_file).read_param()
#     conditions = ParReader(par_file).read_stair()
#     """basic config"""
#     par_dict = {'c': param['c'],
#                 'sscale': param['sscale'],
#                 'dlum': param['dlum'],
#                 'noise_condition': param['condition'],
#                 'sigma': param['sigma']}
#     for idx, x in enumerate(conditions):
#         stim_num = 'stimulus_' + str(idx)
#         par_dict[stim_num] = {}
#         par_dict[stim_num]['label'] = x['label']
#         par_dict[stim_num]['standard'] = float(x['standard'])
#         par_dict[stim_num]['leftRef'] = float(x['leftRef'])
#         par_dict[stim_num]['rightRef'] = float(x['rightRef'])
#         par_dict[stim_num]['stairType'] = x['stairType']
#         par_dict[stim_num]['startVal'] = x['startVal']
#         par_dict[stim_num]['min_val'] = x['minVal']
#         par_dict[stim_num]['max_val'] = None
#
#         """specify for simple method"""
#         par_dict[stim_num]['stepType'] = x['stepType']
#         par_dict[stim_num]['nReversals'] = x['nReversals']
#         par_dict[stim_num]['stepSizes'] = x['stepSizes']
#         par_dict[stim_num]['nUp'] = x['nUp']
#         par_dict[stim_num]['nDown'] = x['nDown']
#
#         """specify for quest method"""
#         par_dict[stim_num]['startValSd'] = 10  # quest method
#         par_dict[stim_num]['pThreshold'] = None  # quest method
#
#     with open(yaml_file, 'w') as file:
#         yaml.dump(par_dict, file, default_flow_style=False, sort_keys=False)
