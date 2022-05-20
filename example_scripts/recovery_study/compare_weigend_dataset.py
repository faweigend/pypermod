import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout
from pypermod.simulator.study_simulator import StudySimulator

import pypermod.config as pyconfig


def compare_weigend_dataset(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Weigend et al. 2021
    derived from Caen et al. 2019.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """
    # data is in the recovery_study subdirectory of data_storage
    # see git structure in src at https://github.com/faweigend/pypermod
    data = pd.read_csv(os.path.join(pyconfig.paths["data_storage"],
                                    "recovery_study",
                                    "weigend.csv"))

    # CP and W' are constants in Weigend data set. Take the values from the first row
    w_p = data["wp"].iloc[0]
    cp = data["cp"].iloc[0]

    # power level and recovery level intensities according to Weigend et al.
    p240 = data["p_work"].iloc[0]
    p480 = data["p_work"].iloc[6]  # second intensity from 7th row on
    cp_33 = data["p_rec"].iloc[0]
    cp_66 = data["p_rec"].iloc[3]  # second intensity in 4th row

    # separated ground truth values derived by Weigend et al. from Caen et al.
    ground_truth_t = data["t_rec"].iloc[0:3]
    ground_truth_p4_cp33 = data["obs"].iloc[0:3]
    ground_truth_p4_cp66 = data["obs"].iloc[3:6]
    ground_truth_p8_cp33 = data["obs"].iloc[6:9]
    ground_truth_p8_cp66 = data["obs"].iloc[9:12]

    # the time window to be covered by the plot
    plot_rec_times = np.arange(0, 370, 10)

    # hydraulic parameters fitted to W' and CP by Caen et al. 2019
    p = [
        18042.056916563655,
        46718.177938027344,
        247.39628102450715,
        106.77042879166977,
        16.96027055119397,
        0.715113715965181,
        0.01777338005017555,
        0.24959503053279475
    ]

    agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, lf=p[0], ls=p[1],
                                  m_u=p[2], m_ls=p[3], m_lf=p[4],
                                  the=p[5], gam=p[6], phi=p[7])

    agents = [agent_bartram, agent_skiba_2015, agent_fit_caen, agent_hyd]

    # run simulations for all four conditions
    results_p4_cp_33 = StudySimulator.standard_comparison(agents=agents, p_work=p240, p_rec=cp_33,
                                                          rec_times=plot_rec_times)
    results_p4_cp_66 = StudySimulator.standard_comparison(agents=agents, p_work=p240, p_rec=cp_66,
                                                          rec_times=plot_rec_times)
    results_p8_cp_33 = StudySimulator.standard_comparison(agents=agents, p_work=p480, p_rec=cp_33,
                                                          rec_times=plot_rec_times)
    results_p8_cp_66 = StudySimulator.standard_comparison(agents=agents, p_work=p480, p_rec=cp_66,
                                                          rec_times=plot_rec_times)

    # plot overview if required
    if plot:
        # set up the figure
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(10.5, 8.5))
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2, sharey=ax1)
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4, sharey=ax3)

        # plot ground truth obs
        color = PlotLayout.get_plot_color("ground_truth")
        linestyle = PlotLayout.get_plot_linestyle("ground_truth")
        ax1.scatter(ground_truth_t, ground_truth_p4_cp33, color=color, linestyle=linestyle)
        ax2.scatter(ground_truth_t, ground_truth_p4_cp66, color=color, linestyle=linestyle)
        ax3.scatter(ground_truth_t, ground_truth_p8_cp33, color=color, linestyle=linestyle)
        ax4.scatter(ground_truth_t, ground_truth_p8_cp66, color=color, linestyle=linestyle)

        # plot simulated agent data
        for p_res_key, p_res_val in results_p4_cp_33.items():
            ax1.plot(plot_rec_times, p_res_val, color=PlotLayout.get_plot_color(p_res_key))
            ax2.plot(plot_rec_times, results_p4_cp_66[p_res_key], color=PlotLayout.get_plot_color(p_res_key))
            ax3.plot(plot_rec_times, results_p8_cp_33[p_res_key], color=PlotLayout.get_plot_color(p_res_key))
            ax4.plot(plot_rec_times, results_p8_cp_66[p_res_key], color=PlotLayout.get_plot_color(p_res_key))

        # finalise layout
        ax1.set_title("$P_{\mathrm{work}} = P240$\n         $P_{\mathrm{rec}}$  = 33% of $CP$")
        ax2.set_title("$P_{\mathrm{work}} = P240$\n         $P_{\mathrm{rec}}$  = 66% of $CP$")
        ax3.set_title("$P_{\mathrm{work}} = P480$\n         $P_{\mathrm{rec}}$  = 33% of $CP$")
        ax4.set_title("$P_{\mathrm{work}} = P480$\n         $P_{\mathrm{rec}}$  = 66% of $CP$")

        # create legend
        handles = PlotLayout.create_standardised_legend(agents=results_p8_cp_33.keys(),
                                                        ground_truth=True)

        ax1.set_ylabel("recovery ratio (%)")
        ax3.set_ylabel("recovery ratio (%)")
        ax3.set_xlabel("$T_{\mathrm{rec}}$ (seconds)")
        ax4.set_xlabel("$T_{\mathrm{rec}}$ (seconds)")
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_xticks([0, 120, 240, 360])
        ax1.legend(handles=handles)

        # finish plot
        plt.tight_layout()
        # plt.subplots_adjust(top=0.90)
        plt.show()
        plt.close(fig=fig)

    # assemble results dict for big comparison
    results = {}
    names = ["P240 CP33", "P240 CP66", "P480 CP33", "P480 CP66"]
    gts = [ground_truth_p4_cp33, ground_truth_p4_cp66, ground_truth_p8_cp33, ground_truth_p8_cp66]
    res = [results_p4_cp_33, results_p4_cp_66, results_p8_cp_33, results_p8_cp_66]
    for i, gt in enumerate(gts):
        for j, t in enumerate(ground_truth_t):
            results[names[i] + " T{}".format(t)] = {
                PlotLayout.get_plot_label("cp"): cp,
                PlotLayout.get_plot_label("w'"): w_p,
                PlotLayout.get_plot_label("ground_truth"): gt.iloc[j],
                PlotLayout.get_plot_label("p_work"): p240 if "P240" in names[i] else p480,
                PlotLayout.get_plot_label("p_rec"): cp_33 if "CP33" in names[i] else cp_66,
                PlotLayout.get_plot_label("t_rec"): t
            }
            for k, v in res[i].items():
                results[names[i] + " T{}".format(t)][PlotLayout.get_plot_label(k)] = round(
                    v[np.where(plot_rec_times == t)[0][0]], 1)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    compare_weigend_dataset(plot=True)
