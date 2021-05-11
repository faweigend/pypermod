import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors, plot_colors_linestyles, \
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

    # measures taken from Bartram et al.
    w_p = 23300
    cp = 393

    # arbitrarily defined recovery intensity
    prec = 20
    times = list(np.arange(0, 420, 5))

    # three component hydraulic agent configuration
    ps = [[28295.84803812729,
           115866.92894681037,
           393.69013448575697,
           125.81789182612417,
           10.42071828931923,
           0.8323218320947604,
           0.034587477091268214,
           0.13458173082205677]]

    # instantiate the hydraulic agent or agents if multiple configurations
    three_comp_agents = []
    for p in ps:
        three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                             the=p[5], gam=p[6], phi=p[7])
        three_comp_agents.append(three_comp_agent)

    # use simulation function to obtain results
    results = StudySimulator.simulate_bartram_trials(three_comp_agents, w_p=w_p, cp=cp, prec=prec, times=times)

    # plot setup
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    hyd_agents = []
    for p_res_key, p_res_val in results.items():

        # collect hydraulic agents in list in case multiple are analysed
        if "ThreeCompHydAgent" in p_res_key:
            hyd_agents.append(p_res_val)
            continue

        # get assigned colors and styles for agent types
        ax.plot(times,
                p_res_val,
                linestyle=plot_linestyle[p_res_key],
                color=plot_color[p_res_key],
                label=plot_labels[p_res_key])

    # set hydraulic agent design according to desired color scheme
    linestyle = plot_linestyle["ThreeCompHydAgent"]
    color = plot_color["ThreeCompHydAgent"]
    label = plot_labels["ThreeCompHydAgent"]

    if len(hyd_agents) > 1:
        label += "(" + str(len(hyd_agents)) + ")"

    # plot the first hydraulic agent with label
    if len(hyd_agents) > 0:
        ax.plot(times,
                hyd_agents[0],
                linestyle=linestyle,
                color=color,
                label=label)

    # add additional ones of more are available
    if len(hyd_agents) > 1:
        for hyd_agent_data in hyd_agents[1:]:
            ax.plot(times,
                    hyd_agent_data,
                    linestyle=linestyle,
                    color=color)

    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()

    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    # assign plot labels
    if prec < 50:
        prec_label = "{}W".format(prec)
    else:
        prec_label = "{:0>2}CP".format(round((prec / cp) * 100.0))

    ax.set_title(r'$P100$' +
                 r'$\rightarrow {}$'.format(prec_label))
    ax.set_xlabel("recovery bout duration (sec)")
    # ax.set_xticks([120, 240, 360])
    ax.set_ylabel("W' recovery (%)")

    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
