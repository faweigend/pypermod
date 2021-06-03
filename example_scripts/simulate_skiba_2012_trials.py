import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.agents.wbal_agents.wbal_int_agent_fix_tau import WbalIntAgentFixTau
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # individual subject measures taken from Skiba et al.
    w_ps = [28000, 25400, 22300, 21600, 18200, 17600, 14300]
    cps = [211, 220, 213, 351, 277, 187, 221]
    s20_taus = [381, 375, 380, 321, 380, 379, 421]
    ss_taus = [11873, 30758, 1319, 596, 1395, 1635, 1816]

    s20_ground_truth = []
    ss_ground_truth = []

    ss_results = defaultdict(list)
    s20_results = defaultdict(list)

    for i, w_p in enumerate(w_ps):
        # create the ground truth agent to use with ground truth taus
        cp = cps[i]
        agent = WbalIntAgentFixTau(w_p=w_p, cp=cp, hz=hz)

        # estimate protocol intensities
        p360 = w_p / 360 + cp
        p240 = w_p / 240 + cp
        p720 = w_p / 720 + cp
        p_exp = p360 + (p360 - cp) / 2
        ss_rec = p360 - (p360 - cp) / 2
        s20_rec = 20
        t_rec = 30

        # double-check if red-definitions are true
        assert p_exp - p240 < 0.01
        assert ss_rec - p720 < 0.01

        # set tau and estimate recovery ratio with established protocol
        agent.tau = s20_taus[i]
        s20_gt = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=s20_rec, t_rec=t_rec)
        s20_ground_truth.append(s20_gt)

        # set tau for severe recovery and gain and estimate recovery ratio with established protocol
        agent.tau = ss_taus[i]
        ss_gt = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=s20_rec, t_rec=t_rec)
        ss_ground_truth.append(ss_gt)

        # now simulate with W'bal ODE agents
        skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
        bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
        weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
        agents = [skib, bart, weig]
        for agent in agents:
            agent_s20 = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=s20_rec, t_rec=t_rec)
            agent_ss = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=ss_rec, t_rec=t_rec)
            s20_results[agent.get_name()].append(agent_s20)
            ss_results[agent.get_name()].append(agent_ss)

    # fitted three component hydraulic model to measures
    # by individual subject (CP, W', and Caen et al. recovery)
    ps = []

    # now plot results and ground truth
    fig = plt.figure(figsize=(12, 6))
    PlotLayout.set_rc_params()
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)

    # plot simulated data
    for p_res_key, p_res_val in s20_results.items():
        # plot s20 results
        ax1.scatter(np.arange(len(p_res_val)), p_res_val,
                    color=PlotLayout.get_plot_color(p_res_key),
                    marker=PlotLayout.get_plot_marker(p_res_key))
        ax1.scatter(np.arange(len(s20_ground_truth)), s20_ground_truth,
                    color=PlotLayout.get_plot_color("ground_truth"),
                    marker=PlotLayout.get_plot_marker("ground_truth"))
        # plot ss results
        ax2.scatter(np.arange(len(p_res_val)), ss_results[p_res_key],
                    color=PlotLayout.get_plot_color(p_res_key),
                    marker=PlotLayout.get_plot_marker(p_res_key))
        ax2.scatter(np.arange(len(ss_ground_truth)), ss_ground_truth,
                    color=PlotLayout.get_plot_color("ground_truth"),
                    marker=PlotLayout.get_plot_marker("ground_truth"))

    # create legend
    handles = PlotLayout.create_standardised_legend(s20_results.keys(),
                                                    ground_truth=True,
                                                    scatter=True)
    ax2.legend(handles=handles)

    # finish layout
    ax1.set_title("p_exp: P240   p_rec: 20 watts   t_rec: 30")
    ax2.set_title("p_exp: P240   p_rec: P720 watts   t_rec: 30")
    ax1.set_ylabel("W' recovery ratio (%)")
    ax1.set_xlabel("subjects")
    ax2.set_xlabel("subjects")

    plt.show()
    plt.close(fig=fig)
