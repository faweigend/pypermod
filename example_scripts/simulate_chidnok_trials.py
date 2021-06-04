import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator


def simulate_chidnok(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Caen et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # averaged values from paper
    cp = 241
    w_p = 21100

    # predefined intensities from paper
    p_exp = 329
    hig = 173
    med = 95
    low = 20

    # assemble for simulation
    p_recs = [hig, med, low]
    t_rec = 30

    # ground truth values from paper
    # cut ["sev", 323, 29]
    # sev = 270
    # ground_truth_v = [557, 759, 1224]
    # ground_truth_e = [90, 243, 497]
    ground_truth_fitted = [165.19, 124.81, 107.46]
    ground_truth_fit_ratio = [16.67, 21.67, 24.58]

    # fitted to Chidnok et al. (w_p=21100, cp=241) with recovery from Caen et al.
    # general settings for three component hydraulic agent
    p = [20047.50153689523,
         115140.99890071881,
         240.68973456248304,
         95.20145903978242,
         10.205583305433073,
         0.7283879087791809,
         0.15441713985950212,
         0.24669788914354474]

    agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1],
                                  m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7])

    agents = [agent_bartram, agent_skiba_2015, agent_fit_caen, agent_hyd]

    results = defaultdict(list)
    for i, p_rec in enumerate(p_recs):
        for agent in agents:
            ratio = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
            results[agent.get_name()].append(ratio)

    # plot overview if required
    if plot is True:
        # initiate the plot
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot()

        # plot ground truth obs
        ax.scatter(np.arange(len(ground_truth_fit_ratio)),
                   ground_truth_fit_ratio,
                   color=PlotLayout.get_plot_color("ground_truth"),
                   marker=PlotLayout.get_plot_marker("ground_truth"),
                   s=60)

        # plot simulated agent data
        for p_res_key, p_res_val in results.items():
            ax.scatter(np.arange(len(p_res_val)),
                       p_res_val,
                       color=PlotLayout.get_plot_color(p_res_key),
                       marker=PlotLayout.get_plot_marker(p_res_key),
                       s=60)

        # finalise Layout
        ax.set_title("expenditure {} watts\nrecovery time {} sec".format(p_exp, t_rec))
        ax.set_xlabel("recovery bout intensity (watts)")
        ax.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
        ax.set_xticks([0, 1, 2])
        ax.set_xlim((-0.5, 2.5))
        ax.set_xticklabels(p_recs)
        ax.grid(axis="y", linestyle=':', alpha=0.5)

        # create legend
        handles = PlotLayout.create_standardised_legend(agents=results.keys(),
                                                        ground_truth=True,
                                                        scatter=True)
        ax.legend(handles=handles)

        # finish plot
        plt.tight_layout()
        plt.show()
        plt.close(fig=fig)

    # assemble dict for model comparison
    ret_results = {}
    for i, p_rec in enumerate(p_recs):
        name = "329 watts {} watts T30".format(p_rec)
        ret_results[name] = {
            PlotLayout.get_plot_label("p_exp"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_rec,
            PlotLayout.get_plot_label("t_rec"): 30,
            PlotLayout.get_plot_label("ground_truth"): round(ground_truth_fit_ratio[i], 1)
        }
        for k, v in results.items():
            ret_results[name][PlotLayout.get_plot_label(k)] = round(v[i], 1)
    return ret_results


if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_chidnok(plot=True)
