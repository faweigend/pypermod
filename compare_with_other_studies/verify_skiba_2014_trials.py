import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib

from w_pm_modeling.performance_modeling_utility import plot_colors, plot_labels
from w_pm_modeling.visualise.skiba_vs_three_comp import simulate_skiba_2014_trials
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12
    hz = 1

    # measures taken from Caen et al. and recovery from caen et al
    w_p = 18200
    cp = 248
    p = [14335.825204662337,
         103316.88385607829,
         248.0477696141307,
         89.77545639058155,
         11.172641323450746,
         0.7277490178203669,
         0.14839391698946602,
         0.2616777430775353]

    # ferguson measures and recovery from caen et al
    # w_p = 21600
    # cp = 212
    # p = [14698.709985579007,
    #      137692.33752132586,
    #      211.9752880322048,
    #      93.01911977151642,
    #      13.362496665694193,
    #      0.6139167894356594,
    #      0.2800546157882695,
    #      0.3676931450425235]

    # create the agent
    three_comp_agent = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                         the=p[5], gam=p[6], phi=p[7])

    results = simulate_skiba_2014_trials(three_comp_agent, w_p=w_p, cp=cp, plot=True)

    # set up the figure
    fig = plt.figure()
    ax = fig.add_subplot()

    plot_results = defaultdict(list)
    for k, v in results.items():
        for k2, v2 in v.items():
            plot_results[k2].append(v2)

    names = [str(x) for x in list(results.keys())]

    for p_res_key, p_res_val in plot_results.items():
        if "T_" in p_res_key:
            ax.scatter(names[:len(p_res_val)], p_res_val, label=plot_labels[p_res_key], color=plot_colors[p_res_key])
            ax.plot(names[:len(p_res_val)], p_res_val, color=plot_colors[p_res_key])

    ax.legend()
    ax.set_title("Skiba et al. (2014)\np_exp: P4   p_rec: 20W   protocol: (t_exp, t_rec)")
    ax.set_ylabel("TTE (s)")
    ax.set_xlabel("protocol")
    plt.show()
    plt.close(fig=fig)
