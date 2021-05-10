import logging

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors, plot_grayscale, plot_grayscale_linestyles, plot_colors_linestyles
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_felippe_trials
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12
    black_and_white = False
    hz = 1

    # Define lookups depending on color or grayscale
    if black_and_white is True:
        color_lookup = plot_grayscale
        linestyle_lookup = plot_grayscale_linestyles
        label_lookup = plot_labels
    else:
        color_lookup = plot_colors
        linestyle_lookup = plot_colors_linestyles
        label_lookup = plot_labels

    # fitted to Felippe et al. (w_p=22000, cp=173) with recoveries from Caen et al.
    # general settings for three component hydraulic agent
    p = [21194.58433754358,
         226708.80342773965,
         173.31388081883063,
         72.90901469091736,
         6.7880733987280815,
         0.7151315984284694,
         0.23156006731077192,
         0.2689211218914619]

    # create the agents
    three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1],
                                         m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                         the=p[5], gam=p[6], phi=p[7])

    results = simulate_felippe_trials(three_comp_agent)

    # set up the figure
    fig = plt.figure()
    ax = fig.add_subplot()

    # Just get the ground truth values
    ground_truth_t = list(results["ground_truth"].keys())
    ground_truth_v = list(results["ground_truth"].values())

    # plot the ground truth
    ax.scatter(ground_truth_t, ground_truth_v, color=color_lookup["ground_truth"], label=label_lookup["ground_truth"])
    # ax.plot([0] + ground_truth_t, [0] + ground_truth_v,
    #         color=color_lookup["ground_truth"],
    #         linestyle=linestyle_lookup["ground_truth"])

    # plot the agent dynamics
    for agent_n, agent_d in results["agents"].items():
        # plot the ground truth
        ax.plot(agent_d,
                color=color_lookup[agent_n],
                linestyle=linestyle_lookup[agent_n],
                label=label_lookup[agent_n])

    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    # ax.set_title("Felippe et al. (2020)\n"r'$P6 \rightarrow  0$ W' " (but MVC)")
    ax.set_title(r'$P360 \rightarrow  0$ W' " (but MVC)")
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([0, 180, 360, 900])
    #ax.set_xticklabels([int(x / 60) for x in ax.get_xticks()])
    ax.set_ylabel("W' recovery (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
