import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1
    # means from the paper
    w_p = 19200
    cp = 269

    p_exp = (w_p / 240) + cp  # 348 in the paper
    get = 179  # mean from the paper
    p_rec = get * 0.9  # recovery at 90% of GET

    rec_times = np.arange(0, 910, 10)

    # fitted to Caen et al. 2021 (w_p = 19200 cp = 269) with recoveries from Caen et al. (2019)
    # general settings for three component hydraulic agent
    ps = [
        [20677.1733445497,
         179472.5078726373,
         269.3909629386831,
         87.53155946812194,
         8.867173757279756,
         0.8086915379675802,
         0.12369693383481795,
         0.17661428891272302]
    ]

    results = StudySimulator.standard_comparison(w_p=w_p,
                                                 cp=cp,
                                                 hyd_agent_configs=ps,
                                                 p_exp=p_exp,
                                                 p_rec=p_rec,
                                                 rec_times=rec_times,
                                                 hz=hz)

    # the ground truth values from the paper
    ground_truth_m_t = [30, 60, 120, 180, 240, 300, 600, 900]  # time steps
    ground_truth_m_v = [28.6, 34.8, 44.2, 50.5, 55.1, 56.8, 73.7, 71.3]  # mean values
    ground_truth_m_e = [8.2, 11.1, 9.7, 12.1, 13.3, 16.4, 19.3, 20.8]  # std errors

    # set up the figure
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    # plot the ground truth obs
    ax.errorbar(ground_truth_m_t, ground_truth_m_v, ground_truth_m_e,
                linestyle='None', marker='o', capsize=3,
                color=PlotLayout.get_plot_color("ground_truth"))

    # plot the agent dynamics
    for agent_n, agent_d in results.items():
        ax.plot(rec_times,
                agent_d,
                color=PlotLayout.get_plot_color(agent_n),
                linestyle=PlotLayout.get_plot_linestyle(agent_n))

    # finalise layout
    # ax.set_title("Caen et al. (2021)")
    ax.set_title(r'$P240 \rightarrow 161$' " W")
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([30, 60, 120, 180, 240, 300, 600, 900])
    ax.set_xticklabels(ax.get_xticks(), rotation=-45, ha='center')
    ax.set_ylabel("W' recovery (%)")

    # get legend
    handles = PlotLayout.create_standardised_legend(agents=results.keys(),
                                                    ground_truth=True,
                                                    errorbar=True)
    ax.legend(handles=handles)

    # finish plot
    plt.tight_layout()
    plt.show()
    plt.close(fig=fig)
