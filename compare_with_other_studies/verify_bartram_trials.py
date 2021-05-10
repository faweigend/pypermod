import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors, plot_colors_linestyles, plot_grayscale_linestyles, plot_grayscale
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_bartram_trials
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    black_and_white = False

    hz = 10

    # measures taken from Caen et al.
    # general settings for skiba agent
    w_p = 23300  # 18200
    cp = 393  # 248
    prec = 20

    ps = [[28295.84803812729,
           115866.92894681037,
           393.69013448575697,
           125.81789182612417,
           10.42071828931923,
           0.8323218320947604,
           0.034587477091268214,
           0.13458173082205677]]

    three_comp_agents = []
    # create the agents
    for p in ps:
        three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                             the=p[5], gam=p[6], phi=p[7])
        three_comp_agents.append(three_comp_agent)

    results = simulate_bartram_trials(three_comp_agents, w_p=w_p, cp=cp, prec=prec)

    # set up the figure
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    plot_results = defaultdict(list)
    for k, v in results.items():
        for k2, v2 in v.items():
            plot_results[k2].append(float(v2))

    names = [int(x) for x in list(results.keys())]

    hyd_agents = []
    for p_res_key, p_res_val in plot_results.items():

        # collect hydraulic agents in list in case multiple are analysed
        if "ThreeCompHydAgent" in p_res_key:
            hyd_agents.append(p_res_val)
            continue

        # set design according to desired color scheme
        if black_and_white is True:
            linestyle = plot_grayscale_linestyles[p_res_key]
            color = plot_grayscale[p_res_key]
            label = plot_labels[p_res_key]
        else:
            linestyle = plot_colors_linestyles[p_res_key]
            color = plot_colors[p_res_key]
            label = plot_labels[p_res_key]

        ax.plot([0] + names,
                [0.0] + p_res_val,
                linestyle=linestyle,
                color=color,
                label=label)

    # set hydraulic agent design according to desired color scheme
    if black_and_white is True:
        linestyle = plot_grayscale_linestyles["ThreeCompHydAgent"]
        color = plot_grayscale["ThreeCompHydAgent"]
        label = plot_labels["ThreeCompHydAgent"]
    else:
        linestyle = plot_colors_linestyles["ThreeCompHydAgent"]
        color = plot_colors["ThreeCompHydAgent"]
        label = plot_labels["ThreeCompHydAgent"]
        if len(hyd_agents) > 1:
            label += "(" + str(len(hyd_agents)) + ")"

    # plot the hydraulic agents
    if len(hyd_agents) > 0:
        ax.plot([0] + names,
                [0.0] + hyd_agents[0],
                linestyle=linestyle,
                color=color,
                label=label)

    if len(hyd_agents) > 1:
        for hyd_agent_data in hyd_agents[1:]:
            ax.plot([0] + names,
                    [0.0] + hyd_agent_data,
                    linestyle=linestyle,
                    color=color)

    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    # assign recovery intensity label
    if prec < 50:
        prec_label = "{}W".format(prec)
    else:
        prec_label = "{:0>2}CP".format(round((prec / cp) * 100.0))

    ax.set_title(r'$P100$' +
                 r'$\rightarrow {}$'.format(prec_label))
    # ax.set_title("p_rec: 0")
    ax.set_xlabel("recovery bout duration (sec)")
    ax.set_xticks([120, 240, 360])
    #ax.set_xticklabels([int(x / 60) for x in ax.get_xticks()])
    ax.set_ylabel("W' recovery (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
