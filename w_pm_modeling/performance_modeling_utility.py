from collections import defaultdict

import matplotlib
import numpy as np
import w_pm_modeling.performance_modeling_config
from matplotlib.collections import LineCollection
from matplotlib.container import ErrorbarContainer
from matplotlib.lines import Line2D

plot_labels = {
    "CpAgentFitCaen" : "fitCaen",
    "CpAgentSkiba2012": "skiba2012",
    "CpAgentSkiba2015": "skiba2015",
    "CpAgentBartram": "bartram",
    "ThreeCompHydAgent": "hydraulic",
    "ground_truth": "observation",
    "T_CpAgentSkiba2012": "skiba2012",
    "T_CpAgentSkiba2015": "skiba2015",
    "T_CpAgentBartram": "bartram",
    "T_ThreeCompHydAgent": "hydraulic",
    "T_ground_truth": "observation",
    "intensity": "intensity"
}

# used in verification plots
plot_color_scheme = {
    "CpAgentFitCaen" : "black",
    "skiba2012": "tab:orange",
    "skiba2015": "tab:red",
    "bartram": "tab:purple",
    "hydraulic": "tab:green",
    "CpAgentSkiba2012": "tab:orange",
    "CpAgentSkiba2015": "tab:red",
    "CpAgentBartram": "tab:purple",
    "ThreeCompHydAgent": "tab:green",
    "ground_truth": "tab:blue",
    "T_CpAgentSkiba2012": "tab:orange",
    "T_CpAgentSkiba2015": "tab:red",
    "T_CpAgentBartram": "tab:purple",
    "T_ThreeCompHydAgent": "tab:green",
    "T_ground_truth": "tab:blue",
    "intensity": "tab:blue"
}

# used in verification plots
plot_grayscale = {
    "intensity": (0.6, 0.6, 0.6),
    "skiba2012": (0, 0, 0),
    "skiba2015": (0.55, 0.55, 0.55),
    "bartram": (0.5, 0.5, 0.5),
    "hydraulic": (0.05, 0.05, 0.05),
    "CpAgentSkiba2012": (0, 0, 0),
    "CpAgentSkiba2015": (0.55, 0.55, 0.55),
    "CpAgentBartram": (0.5, 0.5, 0.5),
    "ThreeCompHydAgent": (0.05, 0.05, 0.05),
    "ground_truth": (0.6, 0.6, 0.6),
    "T_CpAgentSkiba2012": (0, 0, 0),
    "T_CpAgentSkiba2015": (0.55, 0.55, 0.55),
    "T_CpAgentBartram": (0.5, 0.5, 0.5),
    "T_ThreeCompHydAgent": (0.05, 0.05, 0.05),
    "T_ground_truth": (0.6, 0.6, 0.6)
}

plot_color_linestyles = defaultdict(lambda: "-")

plot_grayscale_linestyles = {
    "skiba2012": "-.",
    "skiba2015": "-.",
    "bartram": "--",
    "hydraulic": ":",
    "CpAgentSkiba2012": "-.",
    "CpAgentSkiba2015": "-.",
    "CpAgentBartram": "--",
    "ThreeCompHydAgent": ":",
    "ground_truth": "-",
    "T_CpAgentSkiba2012": "-.",
    "T_CpAgentSkiba2015": "-.",
    "T_CpAgentBartram": "--",
    "T_ThreeCompHydAgent": ":",
    "T_ground_truth": "-",
    "intensity": "-"
}


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

    @staticmethod
    def create_standardised_legend(agents, ground_truth: bool = False, errorbar: bool = False):
        """
        Creates a legend in standardised format
        :param agents: list of agent names used for the lookup of color, linestyle, etc.
        :param ground_truth: whether a ground truth label should be added
        :param errorbar: whether the ground truth label should have errorbars for std
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
            handles.append(Line2D([], [],
                                  color=PlotLayout.get_plot_color(p_res_key),
                                  linestyle=PlotLayout.get_plot_linestyle(p_res_key),
                                  label=PlotLayout.get_plot_label(p_res_key)))

        # summarise hydraulic agents in one entry
        hyd_label = PlotLayout.get_plot_label("ThreeCompHydAgent")
        if hyd_num > 1:
            hyd_label += " ({})".format(hyd_num)
        handles.append(Line2D([], [],
                              color=PlotLayout.get_plot_color("ThreeCompHydAgent"),
                              linestyle=PlotLayout.get_plot_linestyle("ThreeCompHydAgent"),
                              label=hyd_label))

        # plot the ground truth legend entry if required
        if ground_truth is True:
            if errorbar is True:
                line = Line2D([], [], linestyle='None', marker='o',
                              color=PlotLayout.get_plot_color("ground_truth"))
                barline = LineCollection(np.empty((2, 2, 2)))
                err = ErrorbarContainer((line, [line], [barline]), has_xerr=False, has_yerr=True,
                                        label=PlotLayout.get_plot_label("ground_truth"))
                handles.append(err)
            else:
                handles.append(Line2D([], [],
                                      linestyle='None', marker='o',
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
        if w_pm_modeling.performance_modeling_config.black_and_white is True:
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
    def get_plot_linestyle(item_str: str):
        """
        Returns the assigned linestyle for given item. It considers different settings for black and white.
        :param item_str: lookup item as string
        :return: linestyle for given item
        """
        # use lookup according to grayscale setting
        if w_pm_modeling.performance_modeling_config.black_and_white is True:
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
