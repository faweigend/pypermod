import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from pypermod import config

from pypermod.simulator.simulator_basis import SimulatorBasis
from pypermod.utility import PlotLayout

from pypermod.agents.wbal_agents.wbal_int_agent_skiba import WbalIntAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_linear import CpODEAgentBasisLinear
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from threecomphyd.agents.two_comp_hyd_agent import TwoCompHydAgent

from example_scripts.strava_data.strava_to_activity import strava_to_activity

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # agent parameters
    cp = 285
    w_p = 21296

    # hydraulic configuration
    conf = [
        20483.578851118305,
        54119.517965096005,
        284.1878643271425,
        129.37694316427448,
        19.113019370136378,
        0.7148379713482587,
        0.013721751604313055,
        0.26277097070768024
    ]

    # the agent to perform simulations
    agent_ode = WbalODEAgentSkiba(w_p, cp, hz=hz)
    agent_bar = WbalODEAgentBartram(w_p, cp, hz=hz)
    agent_hyd = ThreeCompHydAgent(hz=hz, lf=conf[0], ls=conf[1], m_u=conf[2], m_lf=conf[3],
                                  m_ls=conf[4], the=conf[5], gam=conf[6], phi=conf[7])
    agents = [agent_ode, agent_bar, agent_hyd]

    # other agents exist too. We don't use them in this example
    # agent_wei = WbalODEAgentWeigend(w_p, cp, hz=hz)
    # agent_int = WbalIntAgentSkiba(w_p, cp)
    # agent_lin = CpODEAgentBasisLinear(w_p=w_p, cp=cp, hz=hz)
    # agent_2tm_lin = TwoCompHydAgent(an=w_p, cp=cp, phi=0.3, psi=0.7, hz=hz)
    # agent_2tm_exp = TwoCompHydAgent(an=w_p, cp=cp, phi=0.5, psi=0.1, hz=hz)

    datapath = os.path.join(config.paths["data_storage"],
                            "strava_data",
                            "athlete_0",
                            "race_0.fit")
    na = strava_to_activity(datapath=datapath)
    pow_course = na.power_data

    pow_times = np.arange(len(pow_course))

    # we start predicted W'bal with second 1 because simulations omit the initial time step 0
    sim_times = pow_times + 1

    # set up plot
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(8, 5))

    ax2 = fig.add_subplot(2, 1, 1)
    ax = fig.add_subplot(2, 1, 2, sharex=ax2)

    # use simulator for every agent and plot result
    for agent in agents:
        balances = SimulatorBasis.simulate_course(agent, course_data=pow_course)

        if agent == agent_hyd:
            balances = np.array(balances) * w_p

        ax2.plot(sim_times,
                 balances,
                 color=PlotLayout.get_plot_color(agent.get_name()),
                 label=PlotLayout.get_plot_label(agent.get_name()))

    # plot power demands
    ax.plot(pow_times, pow_course, color='black', label="intensity")

    ax2.set_title(na.id)
    # format axis
    ax.set_ylabel("power output (W)")
    ax.set_xlabel("time (sec)")
    ax.set_yticks([agent_ode.cp])
    ax.set_yticklabels(["CP"])
    ax.tick_params(axis='y', colors='red')
    ax.axhline(y=cp, linestyle="--", color='red', label="critical power (CP)")
    # format x ticks to minutes

    ax2.set_ylabel(r'$W^\prime$' + " balance (J)")
    ax2.set_yticks([0, agent_ode.w_p])
    ax2.set_yticklabels([0, r'$W^\prime$'])
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    plt.tight_layout()
    plt.show()
