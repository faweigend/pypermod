import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.cp_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.cp_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.cp_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # measures taken from Bartram et al.
    w_p = 23300
    cp = 393

    # arbitrarily defined recovery intensity
    p_recs = [cp - 50, cp - 100, cp - 150, cp - 200]
    p_exp = cp + (0.3 * w_p) / 30
    t_rec = 60

    # three component hydraulic agent configuration
    p = [28295.84803812729,
         115866.92894681037,
         393.69013448575697,
         125.81789182612417,
         10.42071828931923,
         0.8323218320947604,
         0.034587477091268214,
         0.13458173082205677]

    # now simulate with W'bal ODE agents
    skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    hydr = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2],
                             m_ans=p[3], m_anf=p[4], the=p[5], gam=p[6], phi=p[7])
    agents = [skib, bart, weig, hydr]

    # use simulation function to obtain results
    results = defaultdict(list)
    for agent in agents:
        for p_rec in p_recs:
            rec_ratio = StudySimulator.get_recovery_ratio_caen(agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
            results[agent.get_name()].append(rec_ratio)

    # make bartram agent observations the ground truth
    results["ground_truth"] = results.pop(bart.get_name())

    # plot setup
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)

    for p_res_key, p_res_val in results.items():
        ax.scatter(np.arange(len(p_res_val)), p_res_val,
                   color=PlotLayout.get_plot_color(p_res_key),
                   marker=PlotLayout.get_plot_marker(p_res_key))

    ax.set_title(r'$P100$')
    ax.set_xlabel("recovery intensity (watts)")
    ax.set_xticks(np.arange(len(p_recs)))
    ax.set_xticklabels(p_recs)
    ax.set_ylabel("W' recovery ratio (%)")

    # Create the legend
    handles = PlotLayout.create_standardised_legend(agents=results.keys(),
                                                    scatter=True)
    ax.legend(handles=handles)

    # finish plot
    plt.show()
    plt.close(fig=fig)
