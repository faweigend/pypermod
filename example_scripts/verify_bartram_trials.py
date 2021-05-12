import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulation.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 10
    # measures taken from Bartram et al.
    w_p = 23300
    cp = 393

    # arbitrarily defined recovery intensity
    prec = 20
    p_exp = cp + (0.3 * w_p) / 30
    rec_times = np.arange(0, 420, 5)

    # three component hydraulic agent configuration
    ps = [[28295.84803812729,
           115866.92894681037,
           393.69013448575697,
           125.81789182612417,
           10.42071828931923,
           0.8323218320947604,
           0.034587477091268214,
           0.13458173082205677]]

    # use simulation function to obtain results
    results = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                 p_exp=p_exp, p_rec=prec, rec_times=rec_times)

    # plot setup
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    hyd_agents = []
    for p_res_key, p_res_val in results.items():

        # collect hydraulic agents in list in case multiple are analysed
        if "ThreeCompHydAgent" in p_res_key:
            hyd_agents.append(p_res_val)
            continue

        # get assigned colors and styles for agent types
        ax.plot(rec_times,
                p_res_val,
                linestyle=PlotLayout.get_plot_linestyle(p_res_key),
                color=PlotLayout.get_plot_color(p_res_key),
                label=PlotLayout.get_plot_label(p_res_key))

    # set hydraulic agent design according to desired color scheme
    linestyle = PlotLayout.get_plot_linestyle("ThreeCompHydAgent")
    color = PlotLayout.get_plot_color("ThreeCompHydAgent")
    label = PlotLayout.get_plot_label("ThreeCompHydAgent")

    if len(hyd_agents) > 1:
        label += "(" + str(len(hyd_agents)) + ")"

    # plot the first hydraulic agent with label
    if len(hyd_agents) > 0:
        ax.plot(rec_times,
                hyd_agents[0],
                linestyle=linestyle,
                color=color,
                label=label)

    # add additional ones of more are available
    if len(hyd_agents) > 1:
        for hyd_agent_data in hyd_agents[1:]:
            ax.plot(rec_times,
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
