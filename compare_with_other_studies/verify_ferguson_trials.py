import logging

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors, plot_grayscale, plot_grayscale_linestyles, plot_colors_linestyles
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_ferguson_trials
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

    # fitted to Ferguson et al. (w_p = 21600 cp = 212) with recoveries from Caen et al.
    # general settings for three component hydraulic agent
    ps = [[19858.664401062637,
           381285.47724572546,
           211.56829509658024,
           84.1393682475386,
           9.876294372943931,
           0.7148516516658686,
           0.25013512969210605,
           0.2794394105229545]]

    # create the agents
    three_comp_hyd_agents = []
    for p in ps:
        three_comp_hyd_agents.append(ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                                       the=p[5], gam=p[6], phi=p[7]))

    results = simulate_ferguson_trials(three_comp_hyd_agents)

    # set up the figure
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    # Just get the ground truth values
    ground_truth_m_t = list(results["ground_truth"]["means"].keys())
    ground_truth_m_v = list(results["ground_truth"]["means"].values())
    ground_truth_m_e = list(results["ground_truth"]["stds"].values())

    ax.errorbar(ground_truth_m_t, ground_truth_m_v, ground_truth_m_e,
                linestyle='None', marker='o', capsize=3,
                color=color_lookup["ground_truth"], label=label_lookup["ground_truth"])

    hyd_agents = []
    # plot the agent dynamics
    for agent_n, agent_d in results["agents"].items():

        # collect hydraulic agents in list in case multiple are analysed
        if "ThreeCompHydAgent" in agent_n:
            hyd_agents.append(agent_d)
            continue

        # plot the ground truth
        ax.plot(agent_d,
                color=color_lookup[agent_n],
                linestyle=linestyle_lookup[agent_n],
                label=label_lookup[agent_n])

    linestyle = linestyle_lookup["ThreeCompHydAgent"]
    color = color_lookup["ThreeCompHydAgent"]
    label = label_lookup["ThreeCompHydAgent"]
    # add the number of agents if more than one is simulated
    if len(hyd_agents) > 1:
        label += "(" + str(len(hyd_agents)) + ")"

    # plot the hydraulic agents
    if len(hyd_agents) > 0:
        ax.plot(hyd_agents[0],
                linestyle=linestyle,
                color=color,
                label=label)

    if len(hyd_agents) > 1:
        for hyd_agent_data in hyd_agents[1:]:
            ax.plot(hyd_agent_data,
                    linestyle=linestyle,
                    color=color)

    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    # ax.set_title("Ferguson et al. (2010)\n"r'$P6 \rightarrow 20W$')
    ax.set_title(r'$P360 \rightarrow 20W$')
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([0, 120, 360, 900])
    # ax.set_xticklabels([int(x / 60) for x in ax.get_xticks()])
    ax.set_ylabel("W' recovery (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
