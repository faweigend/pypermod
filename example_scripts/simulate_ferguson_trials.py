import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator


def simulate_ferguson(plot: bool = False, hz: int = 1) -> dict:
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
    sims = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                 p_exp=p_exp, p_rec=p_rec, rec_times=rec_times, hz=hz)
    # display overview plot if required
    if plot is True:
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
        # ax.set_title("Ferguson et al. (2010)\n"r'$P6 \rightarrow 20W$')
        ax.set_title("expenditure intensity: P360\nrecovery intensity: 20 watts")
        ax.set_xlabel("recovery bout duration (sec)")
        ax.set_xticks([0, 120, 360, 900])
        ax.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")

        plt.subplots_adjust(right=0.96)
        plt.show()
        plt.close(fig=fig)

    ret_results = {}
    # assemble results dict for big comparison
    for i, t in enumerate(ground_truth_t):
        name = "P240 20 watts T{}".format(t)
        ret_results[name] = {
            PlotLayout.get_plot_label("p_exp"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_rec,
            PlotLayout.get_plot_label("t_rec"): t,
            PlotLayout.get_plot_label("ground_truth"): ground_truth_v[i]
        }
        for k, v in sims.items():
            ret_results[name][PlotLayout.get_plot_label(k)] = round(
                v[np.where(rec_times == t)[0][0]], 1)

    return ret_results


if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_ferguson(plot=True, hz=10)
