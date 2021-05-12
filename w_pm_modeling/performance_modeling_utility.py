from collections import defaultdict

import matplotlib
import w_pm_modeling.performance_modeling_config

plot_labels = {
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

    @staticmethod
    def set_rc_params():
        # plot font and font size settings
        matplotlib.rcParams['font.size'] = 12
        matplotlib.rcParams['pdf.fonttype'] = 42
        matplotlib.rcParams['ps.fonttype'] = 42

    @staticmethod
    def get_plot_color(item_str: str):
        if w_pm_modeling.performance_modeling_config.black_and_white is True:
            return plot_grayscale[item_str]
        else:
            return plot_color_scheme[item_str]

    @staticmethod
    def get_plot_label(item_str: str):
        return plot_labels[item_str]

    @staticmethod
    def get_plot_linestyle(item_str: str):
        if w_pm_modeling.performance_modeling_config.black_and_white is True:
            return plot_grayscale_linestyles[item_str]
        else:
            return plot_color_linestyles[item_str]
