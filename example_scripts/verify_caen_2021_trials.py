import logging

import matplotlib
import matplotlib.pyplot as plt
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.performance_modeling_utility import plot_colors, plot_colors_linestyles, \
    plot_grayscale_linestyles, plot_grayscale
from w_pm_modeling.simulation.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # plot font and font size settings
    matplotlib.rcParams['font.size'] = 12
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    # optional black and white layout
    black_and_white = False

    # set design according to desired color scheme
    if black_and_white is True:
        plot_linestyle = plot_grayscale_linestyles
        plot_color = plot_grayscale
    else:
        plot_linestyle = plot_colors_linestyles
        plot_color = plot_colors

    hz = 10

    # fitted to Caen et al. 2021 (w_p = 19200 cp = 269) with recoveries from Caen et al. (2019)
    # general settings for three component hydraulic agent
    ps = [[20677.1733445497,
           179472.5078726373,
           269.3909629386831,
           87.53155946812194,
           8.867173757279756,
           0.8086915379675802,
           0.12369693383481795,
           0.17661428891272302]]

    # create the agents
    three_comp_hyd_agents = []
    for p in ps:
        three_comp_hyd_agents.append(ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                                       the=p[5], gam=p[6], phi=p[7]))

    results = StudySimulator.simulate_caen_2021_trials(three_comp_hyd_agents)

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

    # ax.set_title("Caen et al. (2021)")
    ax.set_title(r'$P240 \rightarrow 161$' " W")
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([30, 60, 120, 180, 240, 300, 600, 900])
    ax.set_xticklabels(ax.get_xticks(), rotation=-45, ha='center')
    ax.set_ylabel("W' recovery (%)")

    plt.tight_layout()
    plt.show()
    plt.close(fig=fig)
