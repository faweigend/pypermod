import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 10

    # averages from paper
    w_p = 12082
    cp = 302

    # exercise intensity at p4
    t_exp = 240
    p_exp = (w_p / t_exp) + cp

    # recovery intensities
    p_rec_l = 20  # low intensity from paper too
    p_rec_m = 188.1  # med intensity
    p_rec_h = 255.5  # high intensity

    rec_times = np.arange(0, 910, 10)

    # fitted to Sreedhara et al. (w_p = 12082 cp = 302)
    # averages from paper W' and CP measures and
    # Caen et al. recovery measures
    ps = [
        [
            16847.124347298122,
            84121.41847324179,
            302.58742411581034,
            74.46271992319922,
            6.142624655991003,
            0.8866234723310764,
            0.013290340188260058,
            0.0874563364053417
        ]
    ]

    # ground truth values from paper
    ground_truth_t = [120, 360, 900]
    ground_truth_l_v = [33.7, 40.62, 39.01]
    ground_truth_m_v = [18.95, 31.51, 19.2]
    ground_truth_h_v = [3.31, 6.47, -15.53]

    # simulate all agents
    l_results = StudySimulator.simulate_sreedhara_trials(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_rec=p_rec_l,
                                                         p_exp=p_exp, t_exp=t_exp, rec_times=rec_times, hz=hz)
    m_results = StudySimulator.simulate_sreedhara_trials(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_rec=p_rec_m,
                                                         p_exp=p_exp, t_exp=t_exp, rec_times=rec_times, hz=hz)
    h_results = StudySimulator.simulate_sreedhara_trials(w_p=w_p, cp=cp, hyd_agent_configs=ps, p_rec=p_rec_h,
                                                         p_exp=p_exp, t_exp=t_exp, rec_times=rec_times, hz=hz)

    # set up the figure
    fig = plt.figure(figsize=(12, 6))
    PlotLayout.set_rc_params()
    ax1 = fig.add_subplot(1, 3, 1)
    ax2 = fig.add_subplot(1, 3, 2, sharey=ax1)
    ax3 = fig.add_subplot(1, 3, 3, sharey=ax1)

    # plot ground truth
    ax1.scatter(ground_truth_t, ground_truth_l_v, color=PlotLayout.get_plot_color("ground_truth"))
    ax2.scatter(ground_truth_t, ground_truth_m_v, color=PlotLayout.get_plot_color("ground_truth"))
    ax3.scatter(ground_truth_t, ground_truth_h_v, color=PlotLayout.get_plot_color("ground_truth"))

    # plot simulated agent data
    for agent_name, agent_data in l_results.items():
        ax1.plot(rec_times, agent_data,
                 color=PlotLayout.get_plot_color(agent_name),
                 linestyle=PlotLayout.get_plot_linestyle(agent_name))
        ax2.plot(rec_times, m_results[agent_name],
                 color=PlotLayout.get_plot_color(agent_name),
                 linestyle=PlotLayout.get_plot_linestyle(agent_name))
        ax3.plot(rec_times, h_results[agent_name],
                 color=PlotLayout.get_plot_color(agent_name),
                 linestyle=PlotLayout.get_plot_linestyle(agent_name))

    # create legend
    handles = PlotLayout.create_standardised_legend(l_results.keys(), ground_truth=True)
    ax1.legend(handles=handles)

    # finish layout
    fig.suptitle("Sreedhara et al. (2020)")
    # ax1.set_title(r'$P4 \rightarrow  20W$')
    # ax2.set_title(r'$P4 \rightarrow  {:0>2}W$'.format(p_rec_m))
    # ax3.set_title(r'$P4 \rightarrow  {:0>2}W$'.format(p_rec_h ))
    ax1.set_title(r'$P4 \rightarrow  L$')
    ax2.set_title(r'$P4 \rightarrow  M$')
    ax3.set_title(r'$P4 \rightarrow  H$')
    ax1.set_ylabel("W'bal as percent of total W' (%)")

    for ax in [ax1, ax2, ax3]:
        ax.set_xticks([0, 120, 360, 900])
        ax.set_xticklabels([int(x / 60) for x in ax.get_xticks()])

        ax.set_yticks([-10, 0, 10, 20, 30, 40, 50])
        ax.set_yticklabels([x + 50 for x in ax.get_yticks()])

    plt.tight_layout()
    plt.subplots_adjust(top=0.85, bottom=0.15, )
    fig.text(0.5, 0.04, 'recovery duration (min)', ha='center')
    plt.show()
    plt.close(fig=fig)
