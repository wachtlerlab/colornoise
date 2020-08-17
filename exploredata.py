import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from natsort import index_natsorted, order_by_index
import pylab
import colorpalette_plus
import glob
import genconfig
import config_tools
import xlsxwriter

"""gnerate colors for plotting"""


def color4plot(num):
    _, colorcodes = colorpalette_plus.ColorPicker().circolors(numStim=num)
    return [x / 255 for x in colorcodes]


def plot_all_trials(xls_file, title, res_file=False, max_trials=None):
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
            resp_wrong_idx = list(np.where(responses == 0)[0])
            resp_correct_idx = list(np.where(responses == 1)[0])
            axs[ax_y, ax_x].plot(hue_vals, linestyle=':', color=color_codes[ax_y])
            axs[ax_y, ax_x].plot(hue_vals, linestyle='None', color=color_codes[ax_y], marker='o', fillstyle='none',
                                 markersize=5, markevery=resp_wrong_idx)
            axs[ax_y, ax_x].plot(hue_vals, linestyle='None', color=color_codes[ax_y], marker='o', fillstyle='full',
                                 markersize=5, markevery=resp_correct_idx)
            axs[ax_y, ax_x].set(xlabel='trials', ylabel='hue angle')
            axs[ax_y, ax_x].set_title(cur_stimulus)
            axs[ax_y, ax_x].label_outer()
            if max_trials:
                axs[ax_y, ax_x].set_xlim([0, max_trials])

    plt.show()
    if res_file:
        fig.savefig(res_file)


# plot_all_trials('data/ysu_lab_quest/20200521T1128L-L.xlsx', '20200521T1128L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1128L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu_lab_quest/20200521T1143L-L.xlsx', '20200521T1143L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1143L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu_lab_updown/20200521T1157L-L.xlsx', '20200521T1157L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1157L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu/20200810T1457L-L.xlsx', '20200810T1457L-L', 'pilot_data_fig/stairs_plot_20200810T1457L-L.pdf', max_trials=None)
# plot_all_trials('data/fschrader/20200811T1424L-L.xlsx', '20200811T1424L-L', 'pilot_data_fig/stairs_plot_20200811T1424L-L.pdf')

""""the main module for exploring data"""


class ExploreData():
    def __init__(self, sub, sel_par=None, sel_ses=None):
        """
        :param sub: the subject
        :param sel_par: parameter keywords, e.g. ['cn16_quest_LL_a', 'cn16_quest_LL_b']
        :param sel_ses: session keywords, e.g. ['20200730T1039L-L', '202007301122L-L']
        """
        self.sub = sub
        self.sel_par = sel_par
        self.sel_ses = sel_ses
        self.huenum = 8

    def readxrl(self):
        """
        :param xrl: a *.xrl file
        :return: par: a dataframe merging params for all selected sessions
        :return: xls: a dataframe merging results for all selected sessions
        """
        xrl = 'data/' + self.sub + '/' + self.sub + '.xrl'
        with open(xrl) as f:
            lines = f.read().splitlines()
            finished = [line for line in lines if line.endswith('.xlsx')]

            if self.sel_par is not None:
                finished = [line for line in finished if any(p in line for p in self.sel_par)]
            if self.sel_ses is not None:
                finished = [line for line in finished if any(s in line for s in self.sel_ses)]

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

    def fitpf(self, savefig=False):

        from psychopy import data
        import pylab
        import matplotlib.pyplot as plt

        dfs, pool = self.sumxrl()
        allIntensities = pool['allIntensities']
        allResponses = pool['allResponses']
        ntrial = pool['ntrial']
        num = int(len(allIntensities) / 2)
        colorcodes = np.repeat(color4plot(num), 2, axis=0)

        # curve fitting and plotting for each condition
        fig, axes = plt.subplots(4, 4, figsize=(16, 10))
        fig.suptitle(self.sub)
        thresh = []
        for idx, label in enumerate(allResponses.index):
            intensities = abs(allIntensities[label])
            responses = allResponses[label]

            # bin data and fit to PF
            combinedInten, combinedResp, combinedN = data.functionFromStaircase(intensities, responses,
                                                                                bins='unique')  # optimal: bins='unique'
            fit = data.FitCumNormal(combinedInten, combinedResp, guess=None, expectedMin=0.5)  # cumulative Gaussian
            thresh.append(fit.inverse(0.76))  # threshold
            # print(label + ': % 0.3f' % fit.ssq)
            # plot
            ax = axes.flatten()[idx]
            fontsize = 8
            ax.plot(combinedInten, combinedResp, 'o', fillstyle='none', color='grey', alpha=.5,
                    markersize=5)  # plot combined data points
            # ax.plot(intensities, responses, 'o', color='grey', alpha=.5, markersize=3)  # plot all data points
            # smoothInt = pylab.arange(min(combinedInten), max(combinedInten), 0.1)  # x for fitted curve
            # smoothResp = fit.eval(smoothInt)  # y for fitted curve
            smoothResp = pylab.arange(0.5, 1, 0.02)
            smoothInt = fit.inverse(smoothResp)
            ax.plot(smoothInt, smoothResp, '-', color=colorcodes[idx])  # plot fitted curve
            ax.plot([thresh[idx], thresh[idx]], [0, 0.76], '--', color='grey')
            ax.plot([0, thresh[idx]], [0.76, 0.76], '--', color='grey')
            ax.set_title(label + ' ' + 'threshold = %0.3f' % thresh[idx], fontsize=fontsize)
            ax.set_ylim([0.5, 1])
            ax.set_xlim([0, 6])
            ax.tick_params(axis='both', which='major', labelsize=fontsize - 2)

        plt.setp(axes[-1, :], xlabel='hue angle')
        plt.setp(axes[:, 0], ylabel='correctness')

        if savefig is True:
            plt.savefig('pilot_data_fig/' + self.sub + '_'
                        + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + str(ntrial) + 'trl' + '.png')

        plt.show()

        return allResponses, thresh

    def threshplot(self, radar=False, savefig=False):
        allResponses, thresh = self.fitpf()
        labels = allResponses.index
        N = int(len(labels) / 2)
        color_codes = color4plot(N)

        if radar is False:
            angles = np.repeat([(n/float(N) * 360) for n in range(N)], 2, axis=0)
            plt.figure(figsize=(16, 10))
            ax = plt.subplot(111)
            ax.set_title('hue discrimination threshold')
            ax.scatter(range(2*N), thresh, color=np.repeat(color_codes, repeats=2, axis=0), s=45)
            ax.plot(thresh, '--', color='grey')
            xlabels = [f"{l}\n{a}" for l, a in zip(labels, angles)]
            ax.set_xticks(range(2*N))
            ax.set_xticklabels(xlabels)
            ax.set_xlabel('hue')
            ax.set_ylabel('threshold')
            if savefig:
                plt.savefig('pilot_data_fig/' + self.sub + '_' + 'threshplot_radar_' + str(len(allResponses[1])) + 'trials' + '.pdf')
            plt.show()
        else:
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]
            ax = plt.subplot(111, polar=True)
            ax.set_theta_offset(0)
            ax.set_theta_direction(1)
            plt.xticks(angles[:-1], [a / np.pi * 180 for a in angles])
            ax.set_rlabel_position(0)
            plt.yticks([0, 2, 4], ["0", "2", "4"], color="grey", size=7)
            plt.ylim(-0.5, 6)

            thresh_m = thresh[::2]
            thresh_m += thresh_m[:1]
            thresh_p = thresh[1::2]
            thresh_p += thresh_p[:1]
            ax.plot(angles, thresh_m, linestyle='--', linewidth=1, label='m')
            ax.plot(angles, thresh_p, linestyle='--', linewidth=1, label='p')
            for idx, c in enumerate(color_codes):
                ax.plot(angles[idx], thresh_m[idx], marker='o', fillstyle='full', markersize=8, color=c)
                ax.plot(angles[idx], thresh_p[idx], marker='<', markersize=8, color=c)

            plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            if savefig:
                plt.savefig('pilot_data_fig/' + self.sub + '_' + 'threshplot_radar_' + str(len(allResponses[1])) + 'trials' + '.pdf')
            plt.show()

    def howcorrect(self, savefig=False):
        dfs, pool = self.sumxrl()
        allResponses = pool['allResponses']
        ntrial = pool['ntrial']
        num = int(len(allResponses) / 2)
        colorcodes = np.repeat(color4plot(num), 2, axis=0)

        plt.figure(figsize=(13, 8))
        plt.bar(allResponses.index, allResponses.apply(sum)/ntrial, color=colorcodes)
        plt.title(self.sub + '_' + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + str(ntrial) + 'trials')
        if savefig:
            plt.savefig('pilot_data_fig/' + self.sub + '_'
                        + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + 'correctness' + '.png')
        plt.show()

    """a short function: convert None to string"""

    def xstr(self, s):
        if s is None:
            return 'None'
        return str(s)


"""examples"""

# par, xls, count = ExploreData('pilot').readxrl()

# ExploreData('pilot', sel_ses=['20200730T1610', '20200730T1630']).fitpf()
# ExploreData('fschrader', sel_ses=['20200730T1039', '20200730T1122']).fitpf()
# ExploreData('ysu', sel_ses=['20200805T1213', '20200805T1232', '20200806T1514']).fitpf()
# ExploreData('fschrader').fitpf()
# ExploreData('ysu', sel_ses=['20200814T1057', '20200814T1137']).howcorrect(savefig=True)