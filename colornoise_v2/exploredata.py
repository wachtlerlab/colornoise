import pandas as pd
import numpy as np
import pylab
import matplotlib.pyplot as plt
from natsort import index_natsorted, order_by_index
import colorpalette
import glob
import genconfig
import config_tools
import xlsxwriter
from psychopy import data
from FitCumNormal import FitCumNormal

"""gnerate colors for plotting"""


def color4plot(num):
    _, colorcodes = colorpalette.ColorPicker().circolors(numStim=num)
    return [x / 255 for x in colorcodes]


def session_profile(xls_file, title, res_file=False, show_fig=True, max_trials=None):
    """
    :param xls_file: data from a single session
    :param title: figure title
    :param res_file: path for saving figure
    :param max_trials: max trials for plotting
    :return:
    """
    res_df = pd.read_excel(pd.ExcelFile(xls_file), sheet_name=None)
    stimuli = list(res_df.keys())
    stimuli.sort()
    color_codes = color4plot(len(stimuli) // 2)
    fig, axs = plt.subplots(len(stimuli) // 2, 2, sharey=True, figsize=(10, len(stimuli) * 3 // 2))
    fig.suptitle(title, fontsize=20)
    for ax_x in range(2):
        for ax_y in range(len(stimuli) // 2):
            cur_stimulus = stimuli[ax_y * 2 + ax_x]
            sheet_df = res_df[cur_stimulus]
            hue_vals = abs(sheet_df['All Intensities'])
            responses = sheet_df['All Responses'].to_numpy()
            correctness = sum(responses) / len(responses) * 100
            resp_wrong_idx = list(np.where(responses == 0)[0])
            resp_correct_idx = list(np.where(responses == 1)[0])
            axs[ax_y, ax_x].plot(hue_vals, linestyle=':', color=color_codes[ax_y])
            axs[ax_y, ax_x].plot(hue_vals, linestyle='None', color=color_codes[ax_y], marker='o', fillstyle='none',
                                 markersize=5, markevery=resp_wrong_idx)
            axs[ax_y, ax_x].plot(hue_vals, linestyle='None', color=color_codes[ax_y], marker='o', fillstyle='full',
                                 markersize=5, markevery=resp_correct_idx)
            axs[ax_y, ax_x].set(xlabel='trials', ylabel='hue angle')
            axs[ax_y, ax_x].set_title(cur_stimulus + ', correctness= ' + str(correctness) + '%')
            axs[ax_y, ax_x].label_outer()
            if max_trials:
                axs[ax_y, ax_x].set_xlim([0, max_trials])
    if res_file:
        pylab.savefig(res_file)
    if show_fig:
        pylab.show()


# session_profile('data/ysu/20200831T1537L-L.xlsx', '20200831T1537L-L')

""""the main module for exploring data"""


class ExploreData():
    def __init__(self, sub, sel_par=None, sel_ses=None, rm_ses=None, xrl_path=None, sel_ses_idx=None):
        """
        :param sub: the subject
        :param sel_par: parameter keywords, e.g. ['cn16_quest_LL_a', 'cn16_quest_LL_b']
        :param sel_ses: session keywords, e.g. ['20200730T1039L-L', '202007301122L-L']
        """
        self.sub = sub
        self.sel_par = sel_par
        self.sel_ses = sel_ses
        self.rm_ses = rm_ses
        self.xrl_path = xrl_path
        self.sel_ses_idx = sel_ses_idx

    def readxrl(self):
        """
        :param xrl: a *.xrl file
        :return: par: a dataframe merging params for all selected sessions
        :return: xls: a dataframe merging results for all selected sessions
        """
        xrl = self.xrl_path
        if xrl is None:
            xrl = 'data/' + self.sub + '/' + self.sub + '.xrl'

        with open(xrl) as f:
            lines = f.read().splitlines()
            finished = [line for line in lines if line.endswith('.xlsx')]

            if self.sel_par is not None:
                finished = [line for line in finished
                            if any(p in line for p in self.sel_par)]
            if self.sel_ses is not None:
                finished = [line for line in finished
                            if any(s in line for s in self.sel_ses)]
            if self.rm_ses is not None:
                finished = [line for line in finished
                            if all(s not in line for s in self.rm_ses)]

            if self.sel_ses_idx is not None:
                finished = [line for idx, line in enumerate(finished)
                            if (idx in self.sel_ses_idx)]

            par = [None] * len(finished)
            xls = [None] * len(finished)
            count = 0
            for line in finished:
                stim_list = [v for k, v in config_tools.read_yml(line.split(', ')[1]).items() if
                             k.startswith('stimulus')]
                for idx, s in enumerate(stim_list):
                    s['stimulus'] = idx
                par[count] = pd.DataFrame(stim_list)
                xls[count] = pd.read_excel(pd.ExcelFile(line.split(', ')[3]), sheet_name=None)
                count += 1
        return par, xls, count

    """combine single *.par and *.xlsx"""

    def checkdf(self, p, x):
        """
        :return: merged dataframes
        """
        labels = x.keys()
        colnames = ['standard_hue', 'ntrial', 'all_intensities', 'all_responses', 'reversal value']
        df = pd.DataFrame(columns=colnames, index=labels)

        for label in labels:
            sheet = x[label]
            df.loc[label, colnames[0]] = float(p[p['label'] == label]['standard'])
            df.loc[label, colnames[1]] = len(sheet)
            df.loc[label, colnames[2]] = np.array((sheet['All Intensities']))
            df.loc[label, colnames[3]] = np.array((sheet['All Responses']))
            df.loc[label, colnames[4]] = np.array((sheet['Reversal Intensities']))
            df = df.reindex(index=order_by_index(df.index, index_natsorted(df.index, reverse=False)))
        return df

    """statistics for all dataframes for a single subject"""

    def meanvalue(self, x):
        return np.nanmean((np.concatenate(x.values[-3:])))  # the last 3 reversals

    def stdvalue(self, x):
        return np.nanstd((np.concatenate(x.values[-3:])))

    def sumxrl(self):

        par, xls, count = self.readxrl()

        dfs = pd.concat([self.checkdf(p, x) for p, x in zip(par, xls)], axis=0)

        pool = {}
        pool['allIntensities'] = dfs.groupby(level=0)['all_intensities'].apply(np.hstack)
        pool['allResponses'] = dfs.groupby(level=0)['all_responses'].apply(np.hstack)
        pool['ntrial'] = dfs.groupby(level=0)['ntrial'].sum().unique()

        return dfs, pool

    """psychometric curve"""

    def fitpf(self):
        dfs, pool = self.sumxrl()
        allIntensities = pool['allIntensities']
        allResponses = pool['allResponses']
        ntrial = pool['ntrial']

        # curve fitting and plotting for each condition
        res = {}
        # print('label: ' + 'centre, ' + 'std, ' + 'ssq')
        for idx, label in enumerate(allResponses.index):
            res[label] = {}
            res[label]['intensities'] = abs(allIntensities[label])
            res[label]['responses'] = allResponses[label]

            res[label]['combinedInten'], res[label]['combinedResp'], res[label]['combinedN'] = \
                data.functionFromStaircase(res[label]['intensities'],
                                           res[label]['responses'],
                                           bins='unique')  # bin data and fit to PF

            res[label]['sems'] = [1.0 / (n / sum(res[label]['combinedN']))
                                  for n in res[label]['combinedN']]  # sems is defined as 1/weight in Psychopy

            # res[label]['fit'] = data.FitCumNormal(res[label]['combinedInten'],
            #                                       res[label]['combinedResp'],
            #                                       sems=res[label]['sems'], guess=None,
            #                                       expectedMin=0.5)  # cumulative Gaussian
            guess = [5, 0]

            res[label]['fit'] = FitCumNormal(res[label]['combinedInten'],
                                                  res[label]['combinedResp'],
                                                  sems=res[label]['sems'], guess=None,
                                                  expectedMin=0.5, lapse=0.01)  # customized cumulative Gaussian

            # print(label + ':' + str(res[label]['fit'].params) + ', ' + str(
            #     res[label]['fit'].ssq))  # a list with [centre, sd] for the Gaussian distribution forming the cumulative

            res[label]['thresh'] = res[label]['fit'].inverse(0.75)  # threshold

        return ntrial, res

    def pfplot(self, savefig=False):
        ntrial, res = self.fitpf()
        num = int(len(res) / 2)
        colorcodes = np.repeat(color4plot(num), 2, axis=0)
        fig, axes = plt.subplots(4, 4, figsize=(16, 10))
        fig.suptitle(self.sub + '_' + str(ntrial) + 'trials')
        print('label: ' + 'centre, ' + 'std, ' + 'ssq')
        for idx, label in enumerate(res.keys()):
            this_res = res[label]

            print(label + ':' + str(this_res['fit'].params) + ', ' + str(
                this_res['fit'].ssq))  # a list with [centre, sd] for the Gaussian distribution forming the cumulative

            ax = axes.flatten()[idx]
            fontsize = 8
            for inten, resp, se in zip(this_res['combinedInten'], this_res['combinedResp'],
                                       this_res['sems']):  # plot combined data points
                ax.plot(inten, resp, '.', color=colorcodes[idx], alpha=0.5, markersize=100 / se)

            # smoothResp = pylab.arange(0.49, 0.96, .02)
            # smoothInt = this_res['fit'].inverse(smoothResp)
            smoothInt = pylab.arange(0, 6.0, 0.05)
            smoothResp = this_res['fit'].eval(smoothInt)

            ax.plot(smoothInt, smoothResp, '-', color=colorcodes[idx])  # plot fitted curve
            ax.plot([this_res['thresh'], this_res['thresh']], [0, 0.75], '--', color='grey')
            ax.plot([0, this_res['thresh']], [0.75, 0.75], '--', color='grey')

            ssq = np.round(this_res['fit'].ssq, decimals=3)  # sum-squared error
            ax.text(3.5, 0.55, 'ssq = ' + str(ssq), fontsize=fontsize)
            ax.set_title(label + ' ' + 'threshold = %0.3f' % this_res['thresh'], fontsize=fontsize)
            ax.set_ylim([0.5, 1])
            ax.set_xlim([0, 6])
            ax.tick_params(axis='both', which='major', labelsize=fontsize - 2)

        plt.setp(axes[-1, :], xlabel='hue angle')
        plt.setp(axes[:, 0], ylabel='correctness')

        if savefig is True:
            plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_'
                        + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + str(ntrial) + 'trl' + '.png')

        plt.show()

    def threshplot(self, polar=False, savefig=False):
        ntrial, res = self.fitpf()
        labels = res.keys()
        N = int(len(labels) / 2)
        color_codes = color4plot(N)
        thresh = [res[k]['thresh'] for k in res.keys()]
        thre_err = [np.sqrt(np.diagonal(res[k]['fit'].covar))[0] for k in res.keys()]

        if polar is False:
            angles = np.repeat([(n / float(N) * 360 + 22.5) for n in range(N)], 2, axis=0)
            plt.figure(figsize=(16, 10))
            ax = plt.subplot(111)
            ax.set_title('hue discrimination threshold')
            ax.scatter(range(2 * N), thresh, color=np.repeat(color_codes, repeats=2, axis=0), s=45)
            ax.errorbar(range(2 * N), thresh, yerr=thre_err, color='grey', ls='--')
            xlabels = [f"{l}\n{a}" for l, a in zip(labels, angles)]
            ax.set_xticks(range(2 * N))
            ax.set_xticklabels(xlabels)
            ax.set_xlabel('hue')
            ax.set_ylabel('threshold')
            if savefig:
                plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_' + 'threshplot_radar_' + str(ntrial) + '_trials' + '.pdf')
            plt.show()
        else:
            angles = [(n / float(N) * 2 + 22.5 / 180) * np.pi for n in range(N)]
            angles += angles[:1]
            ax = plt.subplot(111, polar=True)
            ax.set_theta_offset(0)
            ax.set_theta_direction(1)
            plt.xticks(angles[:-1], [round(a / np.pi * 180, 1) for a in angles])
            ax.set_rlabel_position(0)
            plt.yticks([0, 2, 4], ["0", "2", "4"], color="grey", size=7)
            plt.ylim(-0.5, 6)

            thresh_m = thresh[::2]
            thresh_m += thresh_m[:1]
            thresh_p = thresh[1::2]
            thresh_p += thresh_p[:1]
            # ax.plot([a - 2 * np.pi/180 for a in angles], thresh_m, linestyle='--', linewidth=1, label='m')
            # ax.plot([a + 2 * np.pi/180 for a in angles], thresh_p, linestyle='--', linewidth=1, label='p')
            shift_angles = []
            for idx, c in enumerate(color_codes):
                shift_angles.append(angles[idx] - 2 * np.pi / 180)
                shift_angles.append(angles[idx] + 2 * np.pi / 180)
                ax.plot(angles[idx] - 2 * np.pi / 180, thresh_m[idx], marker='o', fillstyle='full', markersize=8,
                        color=c)
                ax.plot(angles[idx] + 2 * np.pi / 180, thresh_p[idx], marker='<', markersize=8, color=c)
            shift_angles += shift_angles[:1]
            thresh += thresh[:1]
            thre_err += thre_err[:1]
            ax.errorbar(shift_angles, thresh, yerr=thre_err, color='grey', ls='--', capsize=2)
            plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            if savefig:
                plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_' + 'threshplot_radar_' + str(ntrial) + '_trials' + '.pdf')
            plt.show()

    def paramplot(self, savefig=False):
        ntrial, res = self.fitpf()
        labels = res.keys()
        N = int(len(labels) / 2)
        color_codes = color4plot(N)
        angles = np.repeat([(n / float(N) * 360 + 22.5) for n in range(N)], 2, axis=0)
        centre = [res[k]['fit'].params[0] for k in res.keys()]
        std = [res[k]['fit'].params[1] for k in res.keys()]
        par_err = [np.sqrt(np.diagonal(res[k]['fit'].covar)) for k in res.keys()]
        plt.figure(figsize=(16, 10))
        ax = plt.subplot(111)
        ax.set_title('cumulative Gaussian params')
        ax.scatter(range(2 * N), centre, s=50, color=np.repeat(color_codes, repeats=2, axis=0), marker='o', label='mean')
        ax.scatter(range(2 * N), std, s=50, color=np.repeat(color_codes, repeats=2, axis=0), marker='v', label='std')
        ax.errorbar(range(2 * N), centre, yerr=[x[0] for x in par_err], label='mean', color='grey', ls='--')
        ax.errorbar(range(2 * N), std, yerr=[x[1] for x in par_err], label='std', color='silver', ls='--')
        xlabels = [f"{l}\n{a}" for l, a in zip(labels, angles)]
        ax.set_xticks(range(2 * N))
        ax.set_xticklabels(xlabels)
        ax.set_xlabel('hue')
        ax.set_ylabel('params')
        plt.legend()
        if savefig:
            plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_' + 'PF_params_plot_' + str(ntrial) + '_trials' + '.pdf')
        plt.show()

    def howcorrect(self, savefig=False):
        dfs, pool = self.sumxrl()
        allResponses = pool['allResponses']
        ntrial = pool['ntrial']
        num = int(len(allResponses) / 2)
        colorcodes = np.repeat(color4plot(num), 2, axis=0)

        plt.figure(figsize=(13, 8))
        plt.bar(allResponses.index, allResponses.apply(sum) / ntrial, color=colorcodes)
        plt.title(
            self.sub + '_' + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + str(ntrial) + 'trials')
        if savefig:
            plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_'
                        + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + 'correctness' + '.png')
        plt.show()

    """a short function: convert None to string"""

    def xstr(self, s):
        if s is None:
            return 'None'
        return str(s)

    """ Rearrange data by changing the response criteria"""
    def rearrange(self, savefig=False):
        dfs, pool = self.sumxrl()

        # Change the question: whether it is more plus? so you need to swap 0 and 1 during a minus reference
        pool_labels = pool['allResponses'].index
        pool['revResponses'] = pool['allResponses']
        for label in pool_labels:
            if label.endswith('m'):
                pool['revResponses'][label] = 1 - pool['allResponses'][label]

        # Combine each two conditions
        rearranged = pd.DataFrame(columns=['hue', 'intensity', 'response', 'ntrial',
                                           'combinedInten', 'combinedResp', 'combinedN', 'sems',
                                           'fit', 'pse', 'thre'])
        # stupid but straightforward way to combine...
        for ii in np.arange(0, len(pool_labels) - 1, 2):
            idx = ii//2
            rearranged.loc[idx, 'hue'] = 'hue_' + str(idx + 1)
            rearranged.loc[idx, 'intensity'] = np.hstack([pool['allIntensities'][ii], pool['allIntensities'][ii+1]])
            rearranged.loc[idx, 'response'] = np.hstack([pool['allResponses'][ii], pool['allResponses'][ii+1]])
            rearranged.loc[idx, 'ntrial'] = pool['ntrial'][0] * 2

            rearranged.loc[idx, 'combinedInten'],  \
            rearranged.loc[idx, 'combinedResp'],  \
            rearranged.loc[idx, 'combinedN'] = data.functionFromStaircase(rearranged.loc[idx, 'intensity'],
                                                                          rearranged.loc[idx, 'response'],
                                                                          bins='unique')
            rearranged.loc[idx, 'sems'] = [sum(rearranged.loc[idx, 'combinedN']) / n
                                           for n in rearranged.loc[idx, 'combinedN'] ]  # sems is defined as 1/weight in Psychopy

            guess = [5, 1]
            rearranged.loc[idx, 'fit'] = FitCumNormal(rearranged.loc[idx, 'combinedInten'],
                                         rearranged.loc[idx, 'combinedResp'],
                                         sems=rearranged.loc[idx, 'sems'] , guess=None,
                                         expectedMin=0.0, lapse=0.01)  # customized cumulative Gaussian
            rearranged.loc[idx, 'pse'] = rearranged.loc[idx, 'fit'].inverse(0.5-.01)
            rearranged.loc[idx, 'thre'] = rearranged.loc[idx, 'fit'].inverse(0.75-.01)


        return rearranged

    def rearrange_pfplot(self):
        rearranged = self.rearrange()
        ntrial = rearranged['ntrial'][0]
        num = len(rearranged)
        colorcodes = color4plot(num)

        fig, axes = plt.subplots(2, 4, figsize=(16, 10))
        fig.suptitle(self.sub + '_' + str(ntrial) + 'trials')
        print('label: ' + 'centre, ' + 'std, ' + 'ssq')
        for idx in np.arange(num):
            hue = rearranged.loc[idx, 'hue']
            hue_fit = rearranged.loc[idx, 'fit']

            # a list with [centre, sd] for the Gaussian distribution forming the cumulative
            print(hue + ':' + str(hue_fit.params) + ', ' + str(hue_fit.ssq))

            ax = axes.flatten()[idx]
            fontsize = 8
            for inten, resp, se in zip(rearranged.loc[idx, 'combinedInten'],
                                       rearranged.loc[idx, 'combinedResp'],
                                       rearranged.loc[idx, 'sems']):
                ax.plot(inten, resp, '.', color=colorcodes[idx], alpha=0.5, markersize=400 / se)

            smoothResp = pylab.arange(0.0, 1.0, .02)
            smoothInt = hue_fit.inverse(smoothResp)
            # smoothInt = pylab.arange(-6.0, 6.0, 0.05)
            # smoothResp = hue_fit.eval(smoothInt)

            ax.plot(smoothInt, smoothResp, '-', color=colorcodes[idx])  # plot fitted curve

            ax.plot([rearranged.loc[idx, 'pse'], rearranged.loc[idx, 'pse']],
                    [-10.0, 0.5], '--', color='grey')

            ax.plot([-10.0, rearranged.loc[idx, 'pse']],
                    [0.5, 0.5], '--', color='grey')

            ax.plot([rearranged.loc[idx, 'thre'], rearranged.loc[idx, 'thre']],
                    [-10.0, 0.75], '--', color='grey')

            ax.plot([-10.0, rearranged.loc[idx, 'thre']],
                    [0.75, 0.75], '--', color='grey')


            ssq = np.round(hue_fit.ssq, decimals=3)  # sum-squared error
            ax.text(3.5, 0.55, 'ssq = ' + str(ssq), fontsize=fontsize)
            ax.set_title(hue + ' ' + '%dtrials' % rearranged.loc[idx, 'ntrial'], fontsize=fontsize)
            ax.set_ylim([0.0, 1])
            ax.set_xlim([-15, 15])
            ax.tick_params(axis='both', which='major', labelsize=fontsize - 2)

        plt.setp(axes[-1, :], xlabel='hue angle')
        plt.setp(axes[:, 0], ylabel='test hue angle is more counterclockwise ("plus")')
        plt.show()


    def rearrange_paramplot(self):
        rearranged = self.rearrange()
        num = len(rearranged)
        hues = rearranged['hue']
        color_codes = color4plot(num)
        angles = [(n / float(num) * 360 + 22.5) for n in range(num)]
        centre = rearranged['fit'].map(lambda x: x.params[0])
        std = rearranged['fit'].map(lambda x: x.params[1])
        par_err = rearranged['fit'].map(lambda x: np.sqrt(np.diagonal(x.covar)))

        plt.figure(figsize=(12, 10))
        ax = plt.subplot(111)
        ax.set_title('cumulative Gaussian params')

        ax.errorbar(range(num), centre, yerr=[x[0] for x in par_err], label='mean/PSE', color='grey', ls='--')
        ax.errorbar(range(num), std, yerr=[x[1] for x in par_err], label='std/JND/threshold', color='black', ls='--')
        ax.scatter(range(num), centre, s=80, color=color_codes, marker='o', label='mean/PSE')
        ax.scatter(range(num), std, s=80, color=color_codes,  marker='v', label='std/JND/threshold')

        ax.plot(range(num), np.repeat(0, num), '--', color='silver')

        xlabels = [f"{l}\n{a}" for l, a in zip(hues, angles)]
        ax.set_xticks(range(num))
        ax.set_xticklabels(xlabels)
        ax.set_xlabel('hue')
        ax.set_ylabel('params')
        plt.legend()
        # if savefig:
        #     plt.savefig('data_analysis_LL/pf_plots/' + self.sub + '_' + 'PF_params_plot_' + str(ntrial) + '_trials' + '.pdf')
        plt.show()



"""examples"""
# ExploreData('ysu', sel_par=['cn2x8_LL_easy_a.yaml'], rm_ses=['0917T10']).rearrange_pfplot()
# ExploreData('ysu', sel_par=['cn2x8_LL_easy_a.yaml'], rm_ses=['0917T10']).rearrange_paramplot()