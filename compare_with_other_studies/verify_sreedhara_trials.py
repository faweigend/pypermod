import logging

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors, plot_grayscale, plot_colors_linestyles, plot_grayscale_linestyles
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_sreedhara_trials
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

    # fitted to Sreedhara et al. (w_p = 12082 cp = 302)
    # averages from paper W' and CP measures and
    # Caen et al. recovery measures
    p = [            16847.124347298122,
            84121.41847324179,
            302.58742411581034,
            74.46271992319922,
            6.142624655991003,
            0.8866234723310764,
            0.013290340188260058,
            0.0874563364053417]

    # create the agent
    three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                         the=p[5], gam=p[6], phi=p[7])

    results = simulate_sreedhara_trials(three_comp_agent)

    # set up the figure
    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(1, 3, 1)
    ax2 = fig.add_subplot(1, 3, 2, sharey=ax1)
    ax3 = fig.add_subplot(1, 3, 3, sharey=ax1)

    # Sreedhara plots
    intensities = list(results["ground_truth"].values())

    low_int = intensities[0]
    ax1.scatter(low_int.keys(), low_int.values(), color=color_lookup["ground_truth"],
                label=label_lookup["ground_truth"])
    med_int = intensities[1]
    ax2.scatter(med_int.keys(), med_int.values(), color=color_lookup["ground_truth"],
                label=label_lookup["ground_truth"])
    hig_int = intensities[2]
    ax3.scatter(hig_int.keys(), hig_int.values(), color=color_lookup["ground_truth"],
                label=label_lookup["ground_truth"])

    for agent_name, agent_trials in results["agents"].items():
        # get values of trial dict
        trial_vals = list(agent_trials.values())
        # plot results in corresponding axis
        ax1.plot(trial_vals[0],
                 color=color_lookup[agent_name],
                 linestyle=linestyle_lookup[agent_name],
                 label=label_lookup[agent_name])

        ax2.plot(trial_vals[1],
                 color=color_lookup[agent_name],
                 linestyle=linestyle_lookup[agent_name],
                 label=label_lookup[agent_name])

        ax3.plot(trial_vals[2],
                 color=color_lookup[agent_name],
                 linestyle=linestyle_lookup[agent_name],
                 label=label_lookup[agent_name])

    p_rec_l = 20  # low intensity from paper too
    p_rec_m = 188.1  # med intensity
    p_rec_h = 255.5  # high intensity
    cp = 302

    ax1.legend()
    fig.suptitle("Sreedhara et al. (2020)")
    # ax1.set_title(r'$P4 \rightarrow  20W$')
    # ax2.set_title(r'$P4 \rightarrow  {:0>2}W$'.format(p_rec_m))
    # ax3.set_title(r'$P4 \rightarrow  {:0>2}W$'.format(p_rec_h ))
    ax1.set_title(r'$P4 \rightarrow  L$')
    ax2.set_title(r'$P4 \rightarrow  M$')
    ax3.set_title(r'$P4 \rightarrow  H$')
    ax1.set_ylabel("W'bal as percent of total W' (%)")

    for ax in [ax1, ax2, ax3]:
        ax.set_xticks([0, 120, 360, 900])
        ax.set_xticklabels([int(x / 60) for x in ax.get_xticks()])

        ax.set_yticks([-10, 0, 10, 20, 30, 40, 50])
        ax.set_yticklabels([x + 50 for x in ax.get_yticks()])

    plt.tight_layout()
    plt.subplots_adjust(top=0.85, bottom=0.15, )
    fig.text(0.5, 0.04, 'recovery duration (min)', ha='center')

    plt.show()
    plt.close(fig=fig)
