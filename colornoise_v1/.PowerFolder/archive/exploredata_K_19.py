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


def plot_all_trials(xls_file, title, res_file, max_trials=None):
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
            hue_vals = sheet_df['All Intensities']
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
    fig.savefig(res_file)


# plot_all_trials('data/ysu_lab_quest/20200521T1128L-L.xlsx', '20200521T1128L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1128L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu_lab_quest/20200521T1143L-L.xlsx', '20200521T1143L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1143L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu_lab_updown/20200521T1157L-L.xlsx', '20200521T1157L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1157L-L.pdf', max_trials=None)
# plot_all_trials('data/ysu_lab_updown/20200521T1216L-L.xlsx', '20200521T1216L-L.xlsx', 'ysu_test_figs/stairs_plot_20200521T1216L-L.pdf', max_trials=None)


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

        summary = dfs.groupby(level=0).agg({'standard_hue': 'unique',
                                            'ntrial': lambda x: sum(x) / count,
                                            'reversal value': [self.meanvalue, self.stdvalue],
                                            'all_responses': [self.meanvalue, self.stdvalue]})
        summary = summary.reindex(index=order_by_index(summary.index, index_natsorted(summary.index, reverse=False)))

        return dfs, summary

    """psychometric curve"""

    def fitpf(self):

        from psychopy import data
        import pylab
        import matplotlib.pyplot as plt

        dfs, _ = self.sumxrl()
        allIntensities = dfs.groupby(level=0)['all_intensities'].apply(np.hstack)
        allResponses = dfs.groupby(level=0)['all_responses'].apply(np.hstack)

        ntrial = dfs.groupby(level=0)['ntrial'].sum().unique()
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
            # fit = data.FitLogistic(combinedInten, combinedResp, guess=None)  # logistic
            # fit = data.FitWeibull(combinedInten, combinedResp, guess=[3, 0.5], display=1, expectedMin=0.5)  #< --- somehow errors
            thresh.append(fit.inverse(0.76))  # threshold
            print(label + ': % 0.3f' % fit.ssq)
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

        plt.savefig('pilot_data_fig/' + self.sub + '_'
                    + self.xstr(self.sel_par) + '_' + self.xstr(self.sel_ses) + '_' + str(ntrial) + 'trl' + '.pdf')
        plt.show()

        return allResponses, thresh

    def threshplot(self):
        allResponses, thresh = self.fitpf()
        labels = allResponses.index
        N = int(len(labels) / 2)
        color_codes = color4plot(N)

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
        plt.savefig('pilot_data_fig/' + self.sub + '_' + 'threshplot_' + str(len(allResponses[1])) + 'trials' + '.pdf')
        plt.show()

    """a short function: convert None to string"""

    def xstr(self, s):
        if s is None:
            return 'None'
        return str(s)


"""examples: check subjects"""

# # new design in Feb 2020
# sub = 'test'
# ExploreData(sub).plot()
# ExploreData(sub, parsel='config/cn16rnd_a_lin').plot()  # it is not linear steps in actual experiments

# sub = 'test'
# ExploreData(sub, onesel='20200214T1504').plot()


# par, xls, count = ExploreData('pilot').readxrl()

"""curve fitting"""

# ExploreData('test').fitpf()
# ExploreData('test_lin_final').fitpf()
# ExploreData('twachtler_new').fitpf()
# ExploreData('lin_final_b').fitpf()

# ExploreData('ysu_updown').fitpf()
# ExploreData('ysu_quest_start3').fitpf()
# ExploreData('ysu_lab_updown').fitpf()
# ExploreData('ysu_lab_quest').threshplot()
# ExploreData('ysu_quest_start5').fitpf()



# ExploreData('fschrader').fitpf()
# ExploreData('fschrader', sel_ses=['20200730T1039', '20200730T1122']).fitpf()
# ExploreData('pilot', sel_ses=['20200727T1509','20200727T1525']).fitpf()
# ExploreData('pilot', sel_ses=['20200730T1610', '20200730T1630']).fitpf()

# ExploreData('test_lin_final').fitpf()
