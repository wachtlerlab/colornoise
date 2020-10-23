# !/usr/bin/env python3.7
# -*- coding: utf-8 -*-
""" 
Created on 28.09.20

@author yannan
"""
import numpy as np
from exploredata import ExploreData
from psychopy import data
import matplotlib.pyplot as plt
import pylab
from FitCumNormal import FitCumNormal


def fitnoise(pool):
    allIntensities = 10 - pool['allIntensities']
    allResponses = pool['allResponses']  # reverse the response
    ntrial = pool['ntrial']

    # curve fitting and plotting for each condition
    res = {}
    # print('label: ' + 'centre, ' + 'std, ' + 'ssq')
    fig, axes = plt.subplots(1, len(pool['allIntensities']), figsize=(8, 6))
    fig.suptitle(str(ntrial) + 'trials')
    for idx, label in enumerate(allResponses.index):
        res[label] = {}
        res[label]['intensities'] = allIntensities[label]
        res[label]['responses'] = allResponses[label]

        # plt.scatter(res[label]['intensities'], res[label]['responses'])

        res[label]['combinedInten'], res[label]['combinedResp'], res[label]['combinedN'] = \
            data.functionFromStaircase(res[label]['intensities'],
                                       res[label]['responses'],
                                       bins=5)  # bin data and fit to PF


        # plt.scatter(res[label]['combinedInten'], res[label]['combinedResp'])



        res[label]['sems'] = [1.0 / (n / sum(res[label]['combinedN']))
                              for n in res[label]['combinedN']]  # sems is defined as 1/weight in Psychopy

        guess = [3, 0.5]
        # if label == 'hue_1p' or label == 'hue_2p':
        #     print('detected')
        #     guess = [8, 0.5]
        res[label]['fit'] = FitCumNormal(res[label]['combinedInten'],
                                         res[label]['combinedResp'],
                                         sems=res[label]['sems'], guess=None,
                                         expectedMin=0.5, lapse=0.01)  # customized cumulative Gaussian

        # print(label + ':' + str(res[label]['fit'].params) + ', ' + str(
        #     res[label]['fit'].ssq))  # a list with [centre, sd] for the Gaussian distribution forming the cumulative

        res[label]['thresh'] = res[label]['fit'].inverse(0.76)  # threshold

        this_res = res[label]

        # print(label + ':' + str(this_res['fit'].params) + ', ' + str(
        #         this_res['fit'].ssq))  # a list with [centre, sd] for the Gaussian distribution forming the cumulative

        if len(pool['allIntensities']) > 1:
            ax = axes.flatten()[idx]
        else:
            ax = axes

        fontsize = 8
        for inten, resp, se in zip(this_res['combinedInten'], this_res['combinedResp'],
                                       this_res['sems']):  # plot combined data points
            ax.plot(inten, resp, '.', alpha=0.5, markersize=300 / se)

        smoothResp = pylab.arange(0.01, 0.99, .02)
        smoothInt = this_res['fit'].inverse(smoothResp)
            # smoothInt = pylab.arange(0, 6.0, 0.05)
            # smoothResp = this_res['fit'].eval(smoothInt)

        ax.plot(smoothInt, smoothResp, '-')  # plot fitted curve
        ax.plot([this_res['thresh'], this_res['thresh']], [0, 0.75], '--', color='grey')
        ax.plot([0, this_res['thresh']], [0.75, 0.75], '--', color='grey')

        ssq = np.round(this_res['fit'].ssq, decimals=3)  # sum-squared error
        thre_std = np.round(np.sqrt(np.diagonal(this_res['fit'].covar))[0], decimals=3)
        ax.text(3.5, 0.55, 'ssq = ' + str(ssq), fontsize=fontsize)
        ax.text(3.5, 0.53, 'thre_error = ' + str(thre_std), fontsize=fontsize)
        ax.set_title(label + ' ' + 'threshold = %0.3f' % this_res['thresh'], fontsize=fontsize)
        ax.set_ylim([0.5, 1])
            # ax.set_xlim([0, 6])
        ax.tick_params(axis='both', which='major', labelsize=fontsize - 2)
        ax.set_xlabel('level of coherence (10 - std)')
        ax.set_ylabel('correctness')

        print(this_res['fit'].params[0], ' +/- ' , thre_std)

    plt.show()


# Example
# dfs, pool = ExploreData('ysu', sel_par=['config/cn1x5_HH_nl_c.yaml'], xrl_path='data/ysu/noise_test/ysu.xrl').sumxrl()
# fitnoise(pool)

