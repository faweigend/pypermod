import logging

import matplotlib.pyplot as plt
import numpy as np
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout
from pypermod.simulator.study_simulator import StudySimulator


def compare_ferguson_dataset(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Ferguson et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # published means from the paper
    w_p = 21600
    cp = 212

    p_exp = 269  # P6 taken from the paper
    p_rec = 20  # from paper too
    # defined to provide enough detail in the short time frames
    rec_times = np.arange(0, 910, 10)

    # fitted to Ferguson et al. (w_p = 21600 cp = 212) with recoveries from Caen et al.
    # general settings for three component hydraulic agent
    p = [
        18730.04887669842,
        81030.54914024667,
        211.5583717747421,
        94.30913367766424,
        18.75659352000352,
        0.6343242626696716,
        0.204894046277973,
        0.3363619580983015
    ]

    # ground truth measures from the paper
    ground_truth_t = [120, 360, 900]
    ground_truth_v = [37, 65, 86]  # means
    ground_truth_e = [5, 6, 4]  # stds

    agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, lf=p[0], ls=p[1],
                                  m_u=p[2], m_ls=p[3], m_lf=p[4],
                                  the=p[5], gam=p[6], phi=p[7])

    agents = [agent_bartram, agent_skiba_2015, agent_fit_caen, agent_hyd]

    # run the simulations
    sims = StudySimulator.standard_comparison(agents=agents, p_work=p_exp, p_rec=p_rec, rec_times=rec_times)
    # display overview plot if required
    if plot:
        # set up the figure
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(8, 5))
        ax = fig.add_subplot()

        # plot the ground truth
        ax.errorbar(ground_truth_t, ground_truth_v, ground_truth_e,
                    linestyle='None', marker='o', capsize=3,
                    color=PlotLayout.get_plot_color("ground_truth"))

        # plot the simulated agent dynamics
        for agent_n, agent_d in sims.items():
            ax.plot(rec_times,
                    agent_d,
                    color=PlotLayout.get_plot_color(agent_n),
                    linestyle=PlotLayout.get_plot_linestyle(agent_n))

        # create legend
        handles = PlotLayout.create_standardised_legend(sims.keys(), ground_truth=True, errorbar=True)
        ax.legend(handles=handles)

        # finish layout
        ax.set_title("$P_{exp} = P360$ \n      $P_{rec}   = $20 watts")
        ax.set_xlabel("$T_{rec}$ (sec)")
        ax.set_xticks([0, 120, 360, 900])
        ax.set_ylabel("recovery ratio (%)")

        plt.subplots_adjust(right=0.96)
        plt.show()
        plt.close(fig=fig)

    ret_results = {}
    # assemble results dict for big comparison
    for i, t in enumerate(ground_truth_t):
        name = "P240 20 watts T{}".format(t)
        ret_results[name] = {
            PlotLayout.get_plot_label("cp"): cp,
            PlotLayout.get_plot_label("w'"): w_p,
            PlotLayout.get_plot_label("p_work"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_rec,
            PlotLayout.get_plot_label("t_rec"): t,
            PlotLayout.get_plot_label("ground_truth"): ground_truth_v[i]
        }
        for k, v in sims.items():
            ret_results[name][PlotLayout.get_plot_label(k)] = round(
                v[np.where(rec_times == t)[0][0]], 1)

    return ret_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    compare_ferguson_dataset(plot=True, hz=10)
