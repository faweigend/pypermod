import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator


def simulate_caen_2019_trials(plot: bool = False):
    hz = 1

    # measures taken from Caen et al. 2019
    w_p = 18200
    cp = 248

    # power level and recovery level intensities according to Caen et al.
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
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

    # run simulations for all four conditions
    results_p4_cp_33 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=[p], p_exp=p_4,
                                                          p_rec=cp_33, rec_times=rec_times, hz=hz)
    results_p4_cp_66 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=[p], p_exp=p_4,
                                                          p_rec=cp_66, rec_times=rec_times, hz=hz)
    results_p8_cp_33 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=[p], p_exp=p_8,
                                                          p_rec=cp_33, rec_times=rec_times, hz=hz)
    results_p8_cp_66 = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=[p], p_exp=p_8,
                                                          p_rec=cp_66, rec_times=rec_times, hz=hz)

    # combined ground truth values with std error
    ground_truth_t = [120, 240, 360]
    ground_truth_p4_v = [51.8, 57.7, 64.0]
    ground_truth_p4_e = [2.8, 4.3, 5.8]
    ground_truth_p8_v = [40.1, 44.8, 54.8]
    ground_truth_p8_e = [3.9, 3.0, 3.8]

    # set up the figure
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(10, 5))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)

    # plot ground truth obs
    ax1.errorbar(ground_truth_t, ground_truth_p4_v, ground_truth_p4_e, linestyle='None', marker='o', capsize=3,
                 color=PlotLayout.get_plot_color("ground_truth"))
    ax2.errorbar(ground_truth_t, ground_truth_p8_v, ground_truth_p8_e, linestyle='None', marker='o', capsize=3,
                 color=PlotLayout.get_plot_color("ground_truth"))

    # plot simulated agent data
    for p_res_key, p_res_val in results_p4_cp_33.items():
        # combine CP33 and CP66 as it's done in Caen et al.
        p4_vals = (np.array(p_res_val) + np.array(results_p4_cp_66[p_res_key])) / 2
        p8_vals = (np.array(results_p8_cp_33[p_res_key]) + np.array(results_p8_cp_66[p_res_key])) / 2
        # plot results
        ax1.plot(rec_times, p4_vals, color=PlotLayout.get_plot_color(p_res_key))
        ax2.plot(rec_times, p8_vals, color=PlotLayout.get_plot_color(p_res_key))

    # finalise layout
    fig.suptitle("Caen et al. (2019)")
    ax1.set_title(r'P4')
    ax2.set_title(r'P8')
    # create legend
    handles = PlotLayout.create_standardised_legend(agents=results_p8_cp_33.keys(),
                                                    ground_truth=True,
                                                    errorbar=True)

    ax1.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
    ax1.set_xlabel("recovery bout duration (sec)")
    ax2.set_xlabel("recovery bout duration (sec)")
    for ax in [ax1, ax2]:
        ax.set_xticks([0, 120, 240, 360])
    ax1.legend(handles=handles)

    # finish plot
    plt.tight_layout()
    plt.subplots_adjust(top=0.90)
    plt.show()
    plt.close(fig=fig)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_caen_2019_trials(plot=True)
