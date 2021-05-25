import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    hz = 1

    # measures taken from Caen et al.
    # general settings for skiba agent
    w_p = 18200
    cp = 248

    # power level and recovery level estimations for the trials
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66
    rec_times = np.arange(0, 370, 10)

    # fitted to Bartram et al. and Ferguson et al. recovery measures
    ps = [
        # [
        #     15526.629149872091,
        #     68352.75597080137,
        #     248.19813883137562,
        #     96.80164094813664,
        #     10.247146084511353,
        #     0.7397944818727281,
        #     0.07576781919703725,
        #     0.23674229355251739
        # ]
    ]

    # run simulations for all four conditions
    results_p4_cp_33 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_exp=p_4,
                                                          p_rec=cp_33, rec_times=rec_times, hz=hz)
    results_p4_cp_66 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_exp=p_4,
                                                          p_rec=cp_66, rec_times=rec_times, hz=hz)
    results_p8_cp_33 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_exp=p_8,
                                                          p_rec=cp_33, rec_times=rec_times, hz=hz)
    results_p8_cp_66 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_exp=p_8,
                                                          p_rec=cp_66, rec_times=rec_times, hz=hz)

    # separated ground truth values from the paper
    ground_truth_t = [120, 240, 360]
    ground_truth_p4_cp33 = [55.0, 61.0, 70.5]
    ground_truth_p4_cp66 = [49.0, 55.0, 58.5]
    ground_truth_p8_cp33 = [42.0, 52.0, 59.5]
    ground_truth_p8_cp66 = [38.0, 37.5, 50.0]

    # TODO: add combined ground truth measures
    # combined ground truth values with std error
    ground_truth_p4_v = [51.8, 57.7, 64.0]
    ground_truth_p4_e = [2.8, 4.3, 5.8]
    ground_truth_p8_v = [40.1, 44.8, 54.8]
    ground_truth_p8_e = [3.9, 3.0, 3.8]

    # set up the figure
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(10, 10))
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
    # fig.suptitle("Caen et al. (2019)")
    # ax1.set_title(r'$P4 \rightarrow CP33$')
    # ax2.set_title(r'$P4 \rightarrow CP66$')
    # ax3.set_title(r'$P8 \rightarrow CP33$')
    # ax4.set_title(r'$P8 \rightarrow CP66$')
    # create legend
    # handles = PlotLayout.create_standardised_legend(agents=results_p8_cp_33.keys(),
    #                                                 ground_truth=True)

    # START presentation additions
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp, hz=hz)
    sk2012_cp33_rec = np.array(agent_skiba_2012.get_recovery_dynamics(cp_33, rec_times[-1])) / w_p * 100.0
    sk2012_cp66_rec = np.array(agent_skiba_2012.get_recovery_dynamics(cp_66, rec_times[-1])) / w_p * 100.0
    ax1.plot(np.arange(0, rec_times[-1] + 1), sk2012_cp33_rec,
             color=PlotLayout.get_plot_color(agent_skiba_2012.get_name()))
    ax2.plot(np.arange(0, rec_times[-1] + 1), sk2012_cp66_rec,
             color=PlotLayout.get_plot_color(agent_skiba_2012.get_name()))
    ax3.plot(np.arange(0, rec_times[-1] + 1), sk2012_cp33_rec,
             color=PlotLayout.get_plot_color(agent_skiba_2012.get_name()))
    ax4.plot(np.arange(0, rec_times[-1] + 1), sk2012_cp66_rec,
             color=PlotLayout.get_plot_color(agent_skiba_2012.get_name()))
    ax1.set_title(r'$Exp\;High \rightarrow Rec\;Low$')
    ax2.set_title(r'$Exp\;High \rightarrow Rec\;High$')
    ax3.set_title(r'$Exp\;Low \rightarrow Rec\;Low$')
    ax4.set_title(r'$Exp\;Low \rightarrow Rec\;High$')
    keys = list(results_p8_cp_33.keys())
    keys.append(agent_skiba_2012.get_name())
    handles = PlotLayout.create_standardised_legend(agents=keys, ground_truth=True)
    ax1.axhline(40, linestyle=":", color="tab:gray", alpha=0.5)
    ax2.axhline(40, linestyle=":", color="tab:gray", alpha=0.5)
    ax3.axhline(40, linestyle=":", color="tab:gray", alpha=0.5)
    ax4.axhline(40, linestyle=":", color="tab:gray", alpha=0.5)
    # END presentation additions

    ax1.set_ylabel("W' recovery (%)")
    ax3.set_ylabel("W' recovery (%)")
    ax3.set_xlabel("recovery bout duration (sec)")
    ax4.set_xlabel("recovery bout duration (sec)")
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks([0, 120, 240, 360])
    ax1.legend(handles=handles)

    # finish plot
    plt.tight_layout()
    plt.subplots_adjust(top=0.90)
    plt.show()
    plt.close(fig=fig)
