import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulator.study_simulator import StudySimulator


def simulate_weigend(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Weigend et al. 2021
    derived from Caen et al. 2019.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # measures taken from Caen et al. 2019
    w_p = 18200
    cp = 248

    # power level and recovery level intensities according to Caen et al.
    p240 = w_p / 240 + cp
    p480 = w_p / 480 + cp
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66
    rec_times = np.arange(0, 370, 10)

    # hydraulic parameters fitted to W' and CP by Caen et al. 2019
    p = [
        15526.629149872091,
        68352.75597080137,
        248.19813883137562,
        96.80164094813664,
        10.247146084511353,
        0.7397944818727281,
        0.07576781919703725,
        0.23674229355251739
    ]

    agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1],
                                  m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7])

    agents = [agent_bartram, agent_skiba_2015, agent_fit_caen, agent_hyd]

    # run simulations for all four conditions
    results_p4_cp_33 = StudySimulator.standard_comparison(agents=agents, p_exp=p240, p_rec=cp_33, rec_times=rec_times)
    results_p4_cp_66 = StudySimulator.standard_comparison(agents=agents, p_exp=p240, p_rec=cp_66, rec_times=rec_times)
    results_p8_cp_33 = StudySimulator.standard_comparison(agents=agents, p_exp=p480, p_rec=cp_33, rec_times=rec_times)
    results_p8_cp_66 = StudySimulator.standard_comparison(agents=agents, p_exp=p480, p_rec=cp_66, rec_times=rec_times)

    # separated ground truth values derived by Weigend et al. from Caen et al.
    ground_truth_t = [120, 240, 360]
    ground_truth_p4_cp33 = [55.0, 61.0, 70.5]
    ground_truth_p4_cp66 = [49.0, 55.0, 58.5]
    ground_truth_p8_cp33 = [42.0, 52.0, 59.5]
    ground_truth_p8_cp66 = [38.0, 37.5, 50.0]

    # plot overview if required
    if plot:
        # set up the figure
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(10, 8))
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
            ax1.plot(rec_times, p_res_val, color=PlotLayout.get_plot_color(p_res_key))
            ax2.plot(rec_times, results_p4_cp_66[p_res_key], color=PlotLayout.get_plot_color(p_res_key))
            ax3.plot(rec_times, results_p8_cp_33[p_res_key], color=PlotLayout.get_plot_color(p_res_key))
            ax4.plot(rec_times, results_p8_cp_66[p_res_key], color=PlotLayout.get_plot_color(p_res_key))

        # finalise layout
        ax1.set_title("exercise intensity: P240\nrecovery: 33% of CP")
        ax2.set_title("exercise intensity: P240\nrecovery: 66% of CP")
        ax3.set_title("exercise intensity: P480\nrecovery: 33% of CP")
        ax4.set_title("exercise intensity: P480\nrecovery: 66% of CP")

        # create legend
        handles = PlotLayout.create_standardised_legend(agents=results_p8_cp_33.keys(),
                                                        ground_truth=True)

        ax1.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
        ax3.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
        ax3.set_xlabel("recovery bout duration (sec)")
        ax4.set_xlabel("recovery bout duration (sec)")
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
                PlotLayout.get_plot_label("ground_truth"): gt[j],
                PlotLayout.get_plot_label("p_exp"): p240 if "P240" in names[i] else p480,
                PlotLayout.get_plot_label("p_rec"): cp_33 if "CP33" in names[i] else cp_66,
                PlotLayout.get_plot_label("t_rec"): t
            }
            for k, v in res[i].items():
                results[names[i] + " T{}".format(t)][PlotLayout.get_plot_label(k)] = round(
                    v[np.where(rec_times == t)[0][0]], 1)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_weigend(plot=True)
