import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.wbal_agents.wbal_int_agent_fix_tau import WbalIntAgentFixTau
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

from handler.simple_fitter.tau_to_recovery_fitter import TauToRecoveryFitter

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # subject 4 351, 21600, 321, 596

    # individual subject measures taken from Skiba et al.
    w_ps = [28000, 25400, 22300, 18200, 17600, 14300]
    cps = [211, 220, 213, 277, 187, 221]
    s20_taus = [381, 375, 380, 380, 379, 421]
    ss_taus = [11873, 30758, 1319, 1395, 1635, 1816]
    ps = [
        [26396.49411500582, 81744.09846626854, 211.72532348786348, 95.39404138910494, 8.75513454961132,
         0.6293105401776019, 0.17651332386681884, 0.2835125522800205],
        [22544.87470793066, 124614.39433249395, 219.76230224862553, 97.87505373582397, 10.288353159119406,
         0.6492186931124297, 0.230318558209708, 0.31462245131492894],
        [19623.628106542685, 174184.29947002663, 212.63314963663035, 89.06115747885553, 10.708590347190906,
         0.6784870490880772, 0.2414705734136467, 0.2969622153974259],
        [19934.59531828574, 124373.59331120385, 277.1945534858878, 89.15763312590487, 8.734707806849812,
         0.8148213556456596, 0.0884587390563652, 0.16647443113151503],
        [16495.379908131436, 56610.491263040836, 186.44605790002686, 81.78617362915554, 8.623029886544,
         0.6871447654573044, 0.1075083261160869, 0.265890806836563],
        [14751.983993139125, 42183.45350495199, 220.96503012383155, 82.59933342925144, 7.050707450579132,
         0.7355767932963067, 0.025888496989920816, 0.19972035208983654]
    ]

    s20_ground_truth = []
    ss_ground_truth = []

    ss_results = defaultdict(list)
    s20_results = defaultdict(list)

    for i, w_p in enumerate(w_ps):
        # create the ground truth agent to use with ground truth taus
        cp = cps[i]

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

        # ode_tau = TauToRecoveryFitter.skiba_int_tau_to_ode_tau(s20_taus[i], cp, w_p)
        # agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, tau=ode_tau, hz=hz)

        agent = WbalIntAgentFixTau(w_p=w_p, cp=cp, tau=s20_taus[i], hz=hz)

        # estimate recovery ratio with established protocol
        s20_gt = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=s20_rec, t_rec=t_rec)
        s20_ground_truth.append(s20_gt)

        # now simulate with W'bal ODE agents
        skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
        bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
        weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
        p = ps[i]
        hydr = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2],
                             m_ans=p[3], m_anf=p[4], the=p[5], gam=p[6], phi=p[7])
        agents = [skib, bart, weig, hydr]
        for agent in agents:
            agent_s20 = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=s20_rec, t_rec=t_rec)
            s20_results[agent.get_name()].append(agent_s20)

    # now plot results and ground truth
    fig = plt.figure(figsize=(12, 6))
    PlotLayout.set_rc_params()
    ax1 = fig.add_subplot(1, 1, 1)

    # plot simulated data
    for p_res_key, p_res_val in s20_results.items():
        # plot s20 results
        ax1.scatter(np.arange(len(p_res_val)), p_res_val,
                    color=PlotLayout.get_plot_color(p_res_key),
                    marker=PlotLayout.get_plot_marker(p_res_key))
        ax1.scatter(np.arange(len(s20_ground_truth)), s20_ground_truth,
                    color=PlotLayout.get_plot_color("ground_truth"),
                    marker=PlotLayout.get_plot_marker("ground_truth"))

    # create legend
    handles = PlotLayout.create_standardised_legend(s20_results.keys(),
                                                    ground_truth=True,
                                                    scatter=True)
    ax1.legend(handles=handles)

    # finish layout
    ax1.set_title("p_exp: P240   p_rec: 20 watts   t_rec: 30")
    ax1.set_ylabel("W' recovery ratio (%)")
    ax1.set_xticks([1, 2, 3, 4, 5, 6])
    ax1.set_xticklabels([1, 2, 3, 5, 6, 7])
    ax1.set_xlabel("subjects")

    plt.show()
    plt.close(fig=fig)
