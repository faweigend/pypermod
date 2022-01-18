from collections import defaultdict

import matplotlib
import numpy as np
import pypermod.config
from matplotlib.collections import LineCollection
from matplotlib.container import ErrorbarContainer
from matplotlib.lines import Line2D

plot_labels = {
    "hyd_h": "$AnF$ fill-level",
    "cp": "CP",
    "w'": "$W^\prime$",
    "p_work": "$P_{work}$",
    "p_rec": "$P_{rec}$",
    "t_rec": "$T_{rec}$",
    "WbalODEAgentWeigend": "$W^\prime_{weig}$",
    "WbalIntAgentSkiba": "$W^\prime_{bal-int}$",
    "WbalODEAgentSkiba": "$W^\prime_{skib}$",
    "WbalODEAgentBartram": "$W^\prime_{bart}$",
    "WbalODEAgentFixTau": "fixTau",
    "ThreeCompHydAgent": "$hydraulic_{weig}$",
    "ground_truth": "observations",
    "intensity": "intensity"
}

plot_marker = {
    "WbalODEAgentWeigend": "^",
    "WbalIntAgentSkiba": "-",
    "WbalODEAgentSkiba": "*",
    "WbalODEAgentBartram": "+",
    "WbalODEAgentFixTau": "o",
    "ThreeCompHydAgent": "v",
    "ground_truth": "X",
}

# used in verification plots
plot_color_scheme = {
    "hyd_h": "tab:olive",
    "WbalODEAgentWeigend": "black",
    "WbalODEAgentFixTau": "tab:orange",
    "WbalIntAgentSkiba": "tab:orange",
    "WbalODEAgentSkiba": "tab:red",
    "WbalODEAgentBartram": "tab:purple",
    "ThreeCompHydAgent": "tab:green",
    "ground_truth": "tab:blue",
    "intensity": "tab:blue"
}

# used in verification plots
plot_grayscale = {
    "intensity": (0.6, 0.6, 0.6),
    "WbalIntAgentSkiba": (0, 0, 0),
    "WbalODEAgentFixTau": (0.55, 0.55, 0.55),
    "WbalODEAgentSkiba": (0.55, 0.55, 0.55),
    "WbalODEAgentBartram": (0.5, 0.5, 0.5),
    "ThreeCompHydAgent": (0.05, 0.05, 0.05),
    "ground_truth": (0.6, 0.6, 0.6),
}

plot_color_linestyles = defaultdict(lambda: "-")

plot_grayscale_linestyles = {
    "WbalIntAgentSkiba": "-.",
    "WbalODEAgentSkiba": "-.",
    "WbalODEAgentBartram": "--",
    "ThreeCompHydAgent": ":",
    "ground_truth": "-",
    "intensity": "-",
    "WbalODEAgentFixTau": "-"
}


def insert_with_key_enumeration(agent, agent_data: list, results: dict):
    """
    Checks if agent with the same name has stored data already in the given dict and enumerates in that case
    :param agent: agent that produced data
    :param agent_data: simulated data
    :param results: dict to store data into
    :return: dict with inserted data/name pair
    """
    # add to results dict and don't double agent names
    if agent.get_name() not in results:
        results[agent.get_name()] = agent_data
    else:
        # add index to agent name if another agent of same type was simulated before
        new_name = agent.get_name() + "_" + str(
            sum([agent.get_name() in s for s in list(results.keys())]))
        results[new_name] = agent_data
    return results


class PlotLayout:
    """
    Helperclass to standardise the layout for all plots
    """

    @staticmethod
    def set_rc_params():
        """
        Sets standardised font and fontsize
        """
        # plot font and font size settings
        matplotlib.rcParams['font.size'] = 12
        matplotlib.rcParams['pdf.fonttype'] = 42
        matplotlib.rcParams['ps.fonttype'] = 42
        matplotlib.rcParams['axes.labelsize'] = 11
        matplotlib.rcParams['axes.titlesize'] = 12
        matplotlib.rcParams['xtick.labelsize'] = 12
        matplotlib.rcParams['ytick.labelsize'] = 12
        matplotlib.rcParams['legend.fontsize'] = 11

    @staticmethod
    def create_standardised_legend(agents, ground_truth: bool = False, errorbar: bool = False, scatter: bool = False):
        """
        Creates a legend in standardised format
        :param agents: list of agent names used for the lookup of color, linestyle, etc.
        :param ground_truth: whether a ground truth label should be added
        :param errorbar: whether the ground truth label should have errorbars for std
        :param scatter: whether handles are for a scatter plot (uses markers)
        :return: a list of legend handles
        """

        # will be filled with proxies
        handles = []

        # count hydraulic agents for info in label
        hyd_num = sum(["ThreeCompHydAgent" in s for s in agents])

        # Create proxies for ever agent
        for p_res_key in agents:
            # skip hydraulic agents. They are summarised as one after the loop
            if "ThreeCompHyd" in p_res_key:
                continue

            # plot either line or marker
            if scatter is True:
                markerstyle = PlotLayout.get_plot_marker(p_res_key)
                linestyle = None
                linewidths = 0
            else:
                markerstyle = None
                linewidths = 1.5
                linestyle = PlotLayout.get_plot_linestyle(p_res_key)

            # finally add the handle
            handles.append(Line2D([], [],
                                  color=PlotLayout.get_plot_color(p_res_key),
                                  linestyle=linestyle,
                                  marker=markerstyle,
                                  linewidth=linewidths,
                                  label=PlotLayout.get_plot_label(p_res_key)))

        # summarise hydraulic agents in one entry
        if hyd_num > 0:
            hyd_label = PlotLayout.get_plot_label("ThreeCompHydAgent")
            if hyd_num > 1:
                hyd_label += " ({})".format(hyd_num)
            # plot either line or marker
            if scatter is True:
                markerstyle = PlotLayout.get_plot_marker("ThreeCompHydAgent")
                linestyle = None
                linewidths = 0
            else:
                markerstyle = None
                linewidths = 1.5
                linestyle = PlotLayout.get_plot_linestyle("ThreeCompHydAgent")
            # finally add the handle
            handles.append(Line2D([], [],
                                  color=PlotLayout.get_plot_color("ThreeCompHydAgent"),
                                  linestyle=linestyle,
                                  marker=markerstyle,
                                  linewidth=linewidths,
                                  label=hyd_label))

        # plot the ground truth legend entry if required
        if ground_truth is True:
            if errorbar is True:
                line = Line2D([], [],
                              linestyle='None',
                              marker='o',
                              color=PlotLayout.get_plot_color("ground_truth"))
                barline = LineCollection(np.empty((2, 2, 2)))
                err = ErrorbarContainer((line, [line], [barline]),
                                        has_xerr=False,
                                        has_yerr=True,
                                        label=PlotLayout.get_plot_label("ground_truth"))
                handles.append(err)
            else:
                handles.append(Line2D([], [],
                                      linestyle='None',
                                      marker='o',
                                      color=PlotLayout.get_plot_color("ground_truth"),
                                      label=PlotLayout.get_plot_label("ground_truth")))

        return handles

    @staticmethod
    def get_plot_color(item_str: str):
        """
        Returns the assigned color for given item. It considers different settings for black and white.
        :param item_str: lookup item as string
        :return: color label for given item
        """
        # use lookup according to grayscale setting
        if pypermod.config.black_and_white is True:
            lookup = plot_grayscale
        else:
            lookup = plot_color_scheme

        return PlotLayout.__use_lookup(lookup, item_str)

    @staticmethod
    def get_plot_label(item_str: str):
        """
        Returns the assigned label for given item.
        :param item_str: lookup item as string
        :return: label for given item
        """
        return plot_labels[item_str]

    @staticmethod
    def get_plot_marker(item_str: str):
        """
        Returns the assigned marker style for given item.
        :param item_str: lookup item as string
        :return: label for given item
        """
        return plot_marker[item_str]

    @staticmethod
    def get_plot_linestyle(item_str: str):
        """
        Returns the assigned linestyle for given item. It considers different settings for black and white.
        :param item_str: lookup item as string
        :return: linestyle for given item
        """
        # use lookup according to grayscale setting
        if pypermod.config.black_and_white is True:
            lookup = plot_grayscale_linestyles
        else:
            lookup = plot_color_linestyles

        return PlotLayout.__use_lookup(lookup, item_str)

    @staticmethod
    def __use_lookup(lookup, item_str):
        """
        Helper function to look up item_str in corresponding dictionary. Special cases for enumerated
        hydraulic models are considered.
        :param lookup: the dictionary to look the given item_str up in
        :param item_str: item to look up
        :return: looked up value
        """
        # check for hydraulic agents with numbers
        if type(lookup) is not defaultdict and item_str not in lookup:
            if "ThreeCompHydAgent" in item_str:
                return lookup["ThreeCompHydAgent"]
            else:
                raise UserWarning("{} not in {}".format(item_str, lookup))

        return lookup[item_str]
