import logging

import matplotlib.pyplot as plt
import numpy as np
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout
from pypermod.simulator.study_simulator import StudySimulator


def compare_caen_2021_dataset(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Caen et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """
    # means from the paper
    w_p = 19200
    cp = 269

    p_exp = (w_p / 240) + cp  # 348 in the paper
    get = 179  # mean from the paper
    p_rec = get * 0.9  # recovery at 90% of GET -> results in pretty much 60% CP

    rec_times = np.arange(0, 910, 10)

    # fitted to Caen et al. 2021 (w_p = 19200 cp = 269) with recoveries from Caen et al. (2019)
    # general settings for three component hydraulic agent
    p = [
        17631.060154686846,
        46246.12685807986,
        267.2841865716247,
        117.58879540373458,
        20.086989783398884,
        0.6761473340497611,
        0.010446724632575614,
        0.28907732540761866
    ]

    agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, lf=p[0], ls=p[1],
                                  m_u=p[2], m_ls=p[3], m_lf=p[4],
                                  the=p[5], gam=p[6], phi=p[7])

    agents = [agent_bartram, agent_skiba_2015, agent_fit_caen, agent_hyd]

    results = StudySimulator.standard_comparison(agents=agents,
                                                 p_work=p_exp,
                                                 p_rec=p_rec,
                                                 rec_times=rec_times)

    # the ground truth values from the paper
    ground_truth_t = [30, 60, 120, 180, 240, 300, 600, 900]  # time steps
    ground_truth_v = [28.6, 34.8, 44.2, 50.5, 55.1, 56.8, 73.7, 71.3]  # mean values
    ground_truth_e = [8.2, 11.1, 9.7, 12.1, 13.3, 16.4, 19.3, 20.8]  # std errors

    if plot:
        # set up the figure
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(8, 5))
        ax = fig.add_subplot()

        # plot the ground truth obs
        ax.errorbar(ground_truth_t, ground_truth_v, ground_truth_e,
                    linestyle='None', marker='o', capsize=3,
                    color=PlotLayout.get_plot_color("ground_truth"))

        # plot the agent dynamics
        for agent_n, agent_d in results.items():
            ax.plot(rec_times,
                    agent_d,
                    color=PlotLayout.get_plot_color(agent_n),
                    linestyle=PlotLayout.get_plot_linestyle(agent_n))

        # finalise layout
        ax.set_title("$P_{\mathrm{work}} = P240$ \n         $P_{\mathrm{rec}}$  = 161 watts")
        ax.set_xlabel("$T_{\mathrm{rec}}$ (seconds)")
        ax.set_xticks([30, 60, 120, 180, 240, 300, 600, 900])
        ax.set_xticklabels(ax.get_xticks(), rotation=-45, ha='center')
        ax.set_ylabel("recovery ratio (%)")

        # get legend
        handles = PlotLayout.create_standardised_legend(agents=results.keys(),
                                                        ground_truth=True,
                                                        errorbar=True)
        ax.legend(handles=handles)

        # finish plot
        plt.tight_layout()
        plt.show()
        plt.close(fig=fig)

    # assemble results dict for comparison
    ret_results = {}
    for i, t in enumerate(ground_truth_t):
        name = "P240 CP60 T{}".format(t)
        ret_results[name] = {
            PlotLayout.get_plot_label("cp"): cp,
            PlotLayout.get_plot_label("w'"): w_p,
            PlotLayout.get_plot_label("p_work"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_rec,
            PlotLayout.get_plot_label("t_rec"): t,
            PlotLayout.get_plot_label("ground_truth"): ground_truth_v[i]
        }
        for k, v in results.items():
            ret_results[name][PlotLayout.get_plot_label(k)] = round(v[np.where(rec_times == t)[0][0]], 1)
    return ret_results


if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    compare_caen_2021_dataset(plot=True, hz=10)
