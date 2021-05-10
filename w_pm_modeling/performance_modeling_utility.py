from collections import defaultdict

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
plot_colors = {
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

plot_colors_linestyles = defaultdict(lambda: "-")

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
