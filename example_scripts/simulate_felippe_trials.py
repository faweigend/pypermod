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

    # published group means
    w_p = 22000
    cp = 173

    p_exp = 223  # P6 taken from the paper
    p_rec = 0  # from paper too (passive recovery)
    # chosen to give enough detail in the beginning
    rec_times = np.arange(0, 910, 10)

    # fitted to Felippe et al. (w_p=22000, cp=173) with recoveries from Caen et al.
    # general settings for three component hydraulic agent
    ps = [
        [21194.58433754358,
         226708.80342773965,
         173.31388081883063,
         72.90901469091736,
         6.7880733987280815,
         0.7151315984284694,
         0.23156006731077192,
         0.2689211218914619]
    ]

    # ground truth measures as published in paper and converted into ratios (%)
    ground_truth_t = [180, 360, 900]
    ground_truth_v = [
        (142.0 / 377.0) * 100.0,
        (180.0 / 397.0) * 100.0,
        (254.0 / 400.0) * 100.0
    ]
    ground_truth_p_exp = [p_exp] * len(ground_truth_t)  # p_exp for every condition
    ground_truth_p_rec = [p_rec] * len(ground_truth_t)  # p_rec for every condition
    StudySimulator.get_standard_error_measures(w_p=w_p, cp=cp,
                                               hyd_agent_configs=ps, hz=hz,
                                               ground_truth_t=ground_truth_t,
                                               ground_truth_v=ground_truth_v,
                                               ground_truth_p_exp=ground_truth_p_exp,
                                               ground_truth_p_rec=ground_truth_p_rec)

    # use simulation function to obtain results
    results = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                 p_exp=p_exp, p_rec=p_rec, rec_times=rec_times, hz=hz)

    # set up the figure
    fig = plt.figure()
    ax = fig.add_subplot()
    PlotLayout.set_rc_params()

    # plot the ground truth
    ax.scatter(ground_truth_t, ground_truth_v,
               color=PlotLayout.get_plot_color("ground_truth"))

    # plot the simulated agent dynamics
    for agent_n, agent_d in results.items():
        ax.plot(rec_times,
                agent_d,
                color=PlotLayout.get_plot_color(agent_n),
                linestyle=PlotLayout.get_plot_linestyle(agent_n))

    # create legend
    handles = PlotLayout.create_standardised_legend(results.keys(), ground_truth=True)
    ax.legend(handles=handles)

    # finish layout
    # ax.set_title("Felippe et al. (2020)\n"r'$P6 \rightarrow  0$ W' " (but MVC)")
    ax.set_title(r'$P360 \rightarrow  0$ W' " (but MVC)")
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([0, 180, 360, 900])
    ax.set_ylabel("W' recovery ratio (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
