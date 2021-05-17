import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulation.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # averaged values from paper
    cp = 241
    w_p = 21100

    # predefined intensities from paper
    p6_p = 329
    sev = 270
    hig = 173
    med = 95
    low = 20

    # ground truth values from paper
    ground_truth_n = ["sev", "hig", "med", "low"]
    ground_truth_v = [323, 557, 759, 1224]
    ground_truth_e = [29, 90, 243, 497]

    # fitted to Chidnok et al. (w_p=21100, cp=241) with recovery from Caen et al.
    # general settings for three component hydraulic agent
    ps = [
        [20047.50153689523,
         115140.99890071881,
         240.68973456248304,
         95.20145903978242,
         10.205583305433073,
         0.7283879087791809,
         0.15441713985950212,
         0.24669788914354474]
    ]

    results = StudySimulator.simulate_chidnok_trials(w_p=w_p, cp=cp,
                                                     hyd_agent_configs=ps,
                                                     p6_p=p6_p, sev=sev, hig=hig,
                                                     med=med, low=low)

    # initiate the plot
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    # plot ground truth obs
    ax.errorbar(np.arange(len(ground_truth_v)), ground_truth_v, ground_truth_e,
                linestyle='None', marker='o', capsize=3,
                color=PlotLayout.get_plot_color("ground_truth"),
                label=PlotLayout.get_plot_label("ground_truth"))

    # plot simulated agent data
    for p_res_key, p_res_val in results.items():
        color = PlotLayout.get_plot_color(p_res_key)
        linestyle = PlotLayout.get_plot_linestyle(p_res_key)
        ax.scatter(np.arange(len(p_res_val)), p_res_val, color=color)
        ax.plot(np.arange(len(p_res_val)), p_res_val, color=color,
                linestyle=linestyle)

    # finalise Layout
    ax.set_title(r'$P240 \rightarrow (S,H,M,L)$')
    ax.set_xlabel("recovery bout intensity")
    ax.set_ylabel("TTE (seconds)")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["S", "H", "M", "L"])

    # Create the legend
    for p_res_key, p_res_val in results.items():
        if "ThreeCompHyd" in p_res_key:
            continue
        ax.plot([],
                color=PlotLayout.get_plot_color(p_res_key),
                linestyle=PlotLayout.get_plot_linestyle(p_res_key),
                label=PlotLayout.get_plot_label(p_res_key))
    hyd_label = PlotLayout.get_plot_label("ThreeCompHydAgent")
    hyd_label += "({})".format(len(ps)) if len(ps) > 1 else ""
    ax.plot([],
            color=PlotLayout.get_plot_color("ThreeCompHydAgent"),
            linestyle=PlotLayout.get_plot_linestyle("ThreeCompHydAgent"),
            label=hyd_label)
    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    # finish plot
    plt.tight_layout()
    plt.show()
    plt.close(fig=fig)
