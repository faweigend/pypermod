import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pypermod.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout
from pypermod.simulator.study_simulator import StudySimulator

import pypermod.config as pypconfig


def compare_bartram_dataset(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Bartram et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # data is in the recovery_study subdirectory of data_storage
    # see git structure in src at https://github.com/faweigend/pypermod
    data = pd.read_csv(os.path.join(pypconfig.paths["data_storage"],
                                    "recovery_study",
                                    "bartram.csv"))

    # CP and W' are constants in Bartram data set. Take the values from the first row
    w_p = data["wp"].iloc[0]
    cp = data["cp"].iloc[0]

    # recovery intensities tested by Bartram et al.
    p_recs = data["p_rec"]
    # p_work and t_rec are constants. Take values from first row
    p_work = data["p_work"].iloc[0]  # p_work is a constant. Take value from first row
    t_rec = data["t_rec"].iloc[0]

    # get observations from data
    ground_truth_v = data["obs"]

    # the time window the plot covers
    plot_rec_times = np.arange(0, 130, 10)

    # three component hydraulic agent configuration fitted to
    # W' and CP group averages reported by Bartram et al.
    p = [
        23111.907625379536,
        65845.27856132743,
        391.57216549178816,
        148.88277278309968,
        24.148071239095923,
        0.7300850921939723,
        0.010572800716668246,
        0.24210496214582158
    ]

    # setup all used agents
    bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    hyd = ThreeCompHydAgent(hz=hz, lf=p[0], ls=p[1], m_u=p[2], m_ls=p[3], m_lf=p[4],
                            the=p[5], gam=p[6], phi=p[7])
    agents = [skib, weig, hyd, bart]

    # run simulations for all dcp conditions
    dcp_results = []
    for p_rec in p_recs:
        result = StudySimulator.standard_comparison(agents=agents, p_work=p_work, p_rec=p_rec, rec_times=plot_rec_times)
        dcp_results.append(result)

    # create overview plot if required
    if plot:
        # plot setup
        PlotLayout.set_rc_params()
        fig, axes = plt.subplots(nrows=1, ncols=len(dcp_results),
                                 sharex=True, sharey=True,
                                 figsize=(10, 4))

        for i, result in enumerate(dcp_results):
            for p_res_key, p_res_val in result.items():
                axes[i].plot(plot_rec_times, p_res_val,
                             color=PlotLayout.get_plot_color(p_res_key),
                             linestyle=PlotLayout.get_plot_linestyle(p_res_key))
            axes[i].scatter(t_rec, ground_truth_v[i], color=PlotLayout.get_plot_color("ground_truth"))

        for i, ax in enumerate(axes):
            ax.set_title("$P_{\mathrm{work}} = P100$\n" +
                         "$P_{\mathrm{rec}}  = D_{CP}$" +
                         "{}".format(cp - p_recs[i]))

            ax.set_xticks([0, t_rec, plot_rec_times[-1]])
            ax.set_xticklabels([0, t_rec, plot_rec_times[-1]])
            ax.grid(axis="y", linestyle=':', alpha=0.5)

            if i == 2:
                ax.set_xlabel("$T_{\mathrm{rec}}$ (seconds)")
            if i == 0:
                ax.set_ylabel("recovery ratio (%)")
                ax.set_yticks([25, 50, 75])
                ax.set_yticklabels([25, 50, 75])

        # Create the legend
        handles = PlotLayout.create_standardised_legend(agents=dcp_results[0].keys(), ground_truth=True)
        fig.legend(handles=handles, loc='upper center', ncol=5)
        # finish plot
        plt.tight_layout()
        plt.subplots_adjust(top=0.74, bottom=0.13)
        plt.show()
        plt.close(fig=fig)

    # assemble results dict for big comparison
    ret_results = {}
    names = ["DCP0", "DCP50", "DCP100", "DCP150", "DCP200"]
    for i, name in enumerate(names):
        comp_name = "P100 {} T60".format(name)
        ret_results[comp_name] = {
            PlotLayout.get_plot_label("cp"): cp,
            PlotLayout.get_plot_label("w'"): w_p,
            PlotLayout.get_plot_label("p_work"): p_work,
            PlotLayout.get_plot_label("p_rec"): p_recs[i],
            PlotLayout.get_plot_label("t_rec"): 60,
            PlotLayout.get_plot_label("ground_truth"): ground_truth_v[i]
        }
        for k, v in dcp_results[i].items():
            if k == bart.get_name():
                continue
            ret_results[comp_name][PlotLayout.get_plot_label(k)] = round(v[np.where(plot_rec_times == t_rec)[0][0]], 1)

    return ret_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    compare_bartram_dataset(plot=True, hz=10)
