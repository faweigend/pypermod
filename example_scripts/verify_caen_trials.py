import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_labels, plot_colors
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_caen_trials
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12
    # matplotlib.rcParams['pdf.fonttype'] = 42
    # matplotlib.rcParams['ps.fonttype'] = 42
    hz = 1

    # measures taken from Caen et al.
    # general settings for skiba agent
    w_p = 18200
    cp = 248

    # fitted to Bartram et al. and Ferguson et al. recovery measures
    p = [5012.488046094979,
         23971.106659972895,
         246.78924534522548,
         111.89115426178523,
         34.264846411055714,
         0,
         0.36811418822330305,
         0.9528765891217723]

    # create the agent
    three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                         the=p[5], gam=p[6], phi=p[7])

    results = simulate_caen_trials(three_comp_agent, w_p=w_p, cp=cp)

    # set up the figure
    fig = plt.figure(figsize=(10, 10))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2, sharey=ax1)
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4, sharey=ax3)

    plot_results = defaultdict(list)
    for k, v in results.items():
        for k2, v2 in v.items():
            plot_results[k2].append(v2)

    names = [int(x[2]) for x in list(results.keys())]

    for p_res_key, p_res_val in plot_results.items():
        ax1.scatter([0] + names[:3], [0] + p_res_val[:3], label=plot_labels[p_res_key], color=plot_colors[p_res_key])
        ax1.plot([0] + names[:3], [0] + p_res_val[:3], color=plot_colors[p_res_key])

        ax2.scatter([0] + names[3:6], [0] + p_res_val[3:6], label=plot_labels[p_res_key], color=plot_colors[p_res_key])
        ax2.plot([0] + names[3:6], [0] + p_res_val[3:6], color=plot_colors[p_res_key])

        ax3.scatter([0] + names[6:9], [0] + p_res_val[6:9], label=plot_labels[p_res_key], color=plot_colors[p_res_key])
        ax3.plot([0] + names[6:9], [0] + p_res_val[6:9], color=plot_colors[p_res_key])

        ax4.scatter([0] + names[9:], [0] + p_res_val[9:], label=plot_labels[p_res_key], color=plot_colors[p_res_key])
        ax4.plot([0] + names[9:], [0] + p_res_val[9:], color=plot_colors[p_res_key])

    ax1.legend()
    fig.suptitle("Caen et al. (2019)")
    # ax1.set_title("p_exp: {}  p_rec: {}".format(round(list(results.keys())[0][0], 2),
    #                                             list(results.keys())[0][1]))
    # ax2.set_title("p_exp: {}  p_rec: {}".format(round(list(results.keys())[4][0], 2),
    #                                             list(results.keys())[4][1]))
    # ax3.set_title("p_exp: {}  p_rec: {}".format(round(list(results.keys())[7][0], 2),
    #                                             list(results.keys())[7][1]))
    # ax4.set_title("p_exp: {}  p_rec: {}".format(round(list(results.keys())[9][0], 2),
    #                                             list(results.keys())[9][1]))
    ax1.set_title("p_exp: p4    p_rec: cp33")
    ax2.set_title("p_exp: p4    p_rec: cp66")
    ax3.set_title("p_exp: p8    p_rec: cp33")
    ax4.set_title("p_exp: p8    p_rec: cp66")
    ax1.set_ylabel("W' recovery (%)")
    ax3.set_ylabel("W' recovery (%)")
    ax3.set_xlabel("t_rec (s)")
    ax4.set_xlabel("t_rec (s)")

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks([0, 120, 240, 360])

    plt.tight_layout()
    plt.subplots_adjust(top=0.90)
    plt.show()
    plt.close(fig=fig)
