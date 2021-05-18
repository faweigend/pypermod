import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulation.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # published means from the paper
    w_p = 21600
    cp = 212

    p6 = 269  # taken from the paper
    p_rec = 20  # from paper too
    # defined to provide enough detail in the short time frames
    rec_times = np.arange(0, 910, 10)

    # fitted to Ferguson et al. (w_p = 21600 cp = 212) with recoveries from Caen et al.
    # general settings for three component hydraulic agent
    ps = [
        [19858.664401062637,
           381285.47724572546,
           211.56829509658024,
           84.1393682475386,
           9.876294372943931,
           0.7148516516658686,
           0.25013512969210605,
           0.2794394105229545]
    ]

    # ground truth measures from the paper
    ground_truth_t = [120, 360, 900]
    ground_truth_v = [37, 65, 86]  # means
    ground_truth_e = [5, 6, 4]  # stds

    # run the simulations
    results = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                 p_exp=p6, p_rec=p_rec, rec_times=rec_times, hz=hz)

    # set up the figure
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()
    PlotLayout.set_rc_params()

    # plot the ground truth
    ax.errorbar(ground_truth_t, ground_truth_v, ground_truth_e,
                linestyle='None', marker='o', capsize=3,
                color=PlotLayout.get_plot_color("ground_truth"))

    # plot the simulated agent dynamics
    for agent_n, agent_d in results.items():
        ax.plot(rec_times,
                agent_d,
                color=PlotLayout.get_plot_color(agent_n),
                linestyle=PlotLayout.get_plot_linestyle(agent_n))

    # create legend
    handles = PlotLayout.create_standardised_legend(results.keys(), ground_truth=True, errorbar=True)
    ax.legend(handles=handles)

    # finish layout
    # ax.set_title("Ferguson et al. (2010)\n"r'$P6 \rightarrow 20W$')
    ax.set_title(r'$P360 \rightarrow 20W$')
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([0, 120, 360, 900])
    ax.set_ylabel("W' recovery (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
