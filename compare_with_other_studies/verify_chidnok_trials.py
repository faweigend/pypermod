import logging

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_colors, plot_labels, plot_grayscale, plot_colors_linestyles, plot_grayscale_linestyles
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_chidnok_trials

from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12
    hz = 1
    black_and_white = False

    # Define lookups depending on color or grayscale
    if black_and_white is True:
        color_lookup = plot_grayscale
        linestyle_lookup = plot_grayscale_linestyles
        label_lookup = plot_labels
    else:
        color_lookup = plot_colors
        linestyle_lookup = plot_colors_linestyles
        label_lookup = plot_labels

    # fitted to Chidnok et al. (w_p=21100, cp=241) with recovery from Caen et al.
    # general settings for three component hydraulic agent
    p = [20047.50153689523,
         115140.99890071881,
         240.68973456248304,
         95.20145903978242,
         10.205583305433073,
         0.7283879087791809,
         0.15441713985950212,
         0.24669788914354474]

    three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                         the=p[5], gam=p[6], phi=p[7])

    results = simulate_chidnok_trials(three_comp_agent,
                                      plot=False)

    # now the final comparison plot
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    for p_res_key, p_res_val in results.items():

        label = label_lookup[p_res_key]
        color = color_lookup[p_res_key]
        linestyle = linestyle_lookup[p_res_key]

        names = [str(x) for x in p_res_val.keys()]
        times = [int(x["T"]) for x in p_res_val.values()]

        # special handling for ground truth with errors
        if p_res_key == "ground_truth":
            errors = [int(x["std"]) for x in p_res_val.values()]
            ax.errorbar(names, times, errors,
                        linestyle='None', marker='o', capsize=3,
                        color=color_lookup["ground_truth"],
                        label=label_lookup["ground_truth"])
        else:
            ax.scatter(names, times, color=color)
            ax.plot(names, times, color=color, linestyle=linestyle, label=label)

    # sort the legend into the right order
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)

    ax.set_title(r'$P240 \rightarrow (S,H,M,L)$')
    ax.set_xlabel("recovery bout intensity")
    ax.set_ylabel("TTE (seconds)")
    ax.set_xticklabels(["S", "H", "M", "L"])

    plt.tight_layout()
    plt.show()
    plt.close(fig=fig)
