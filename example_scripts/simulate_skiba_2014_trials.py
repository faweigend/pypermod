import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulation.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # measures taken from Caen et al. and recovery from caen et al
    w_p = 18200
    cp = 248

    # t_exp, t_rec combinations as tested by Skiba et al.
    trials = [(20, 5), (20, 10), (20, 20), (20, 30), (40, 30), (60, 30)]

    # fitted three component hydraulic model to measures by Caen et al. (CP, W', and recovery)
    ps = [
        [14335.825204662337,
         103316.88385607829,
         248.0477696141307,
         89.77545639058155,
         11.172641323450746,
         0.7277490178203669,
         0.14839391698946602,
         0.2616777430775353]
    ]

    # run simulation for all agents
    results = StudySimulator.simulate_skiba_2014_trials(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                        trials=trials, hz=hz)

    # set up the figure
    fig = plt.figure()
    ax = fig.add_subplot()
    PlotLayout.set_rc_params()

    # plot simulated data
    for p_res_key, p_res_val in results.items():
        ax.scatter(np.arange(len(trials)), p_res_val, color=PlotLayout.get_plot_color(p_res_key))
        ax.plot(np.arange(len(trials)), p_res_val, color=PlotLayout.get_plot_color(p_res_key))

    # create legend
    handles = PlotLayout.create_standardised_legend(results.keys())
    ax.legend(handles=handles)

    # finish layout
    ax.set_title("Skiba et al. (2014)\np_exp: P4   p_rec: 20W   protocol: (t_exp, t_rec)")
    ax.set_ylabel("TTE (s)")
    ax.set_xlabel("protocol")
    ax.set_xticks(np.arange(len(trials)))
    ax.set_xticklabels(labels=trials)

    plt.show()
    plt.close(fig=fig)
