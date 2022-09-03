import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from pypermod import config
from pypermod.agents.hyd_agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod.data_structure.athlete import Athlete

from pypermod.simulator.simulator_basis import SimulatorBasis
from pypermod.utility import PlotLayout

# set logging level to the highest level
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

hz = 1

# load athlete
athlete_path = os.path.join(config.paths["data_storage"],
                            "strava_study",
                            "athlete_0")
athlete = Athlete(path=athlete_path)

# Get CP and W'
cpmfits = athlete.get_cp_fitting_of_type_and_protocol(a_type=ActivityTypes.STANDARD_BIKE_BBB,
                                                      p_type=ProtocolTypes.TT)
best_fit = cpmfits.get_best_2p_fit()
cp = best_fit["cp"]
w_p = best_fit["w_p"]

# get hydraulic model configuration
conf = athlete.get_hydraulic_fitting_of_type_and_protocol(a_type=ActivityTypes.STANDARD_BIKE_BBB,
                                                          p_type=ProtocolTypes.TT)

# the agent to perform simulations
agent_ode = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
agent_bar = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
agent_hyd = ThreeCompHydAgent(hz=hz, lf=conf[0], ls=conf[1], m_u=conf[2], m_lf=conf[3],
                              m_ls=conf[4], the=conf[5], gam=conf[6], phi=conf[7])
agents = [agent_ode, agent_bar, agent_hyd]

# other agents exist too. We don't use them in this example
# agent_wei = WbalODEAgentWeigend(w_p, cp, hz=hz)
# agent_int = WbalIntAgentSkiba(w_p, cp)
# agent_lin = CpODEAgentBasisLinear(w_p=w_p, cp=cp, hz=hz)
# agent_2tm_lin = TwoCompHydAgent(an=w_p, cp=cp, phi=0.3, psi=0.7, hz=hz)
# agent_2tm_exp = TwoCompHydAgent(an=w_p, cp=cp, phi=0.5, psi=0.1, hz=hz)

for race in athlete.iterate_activities_of_type_and_protocol(a_type=ActivityTypes.STANDARD_BIKE,
                                                            p_type=ProtocolTypes.RACE):
    pow_course = race.power_data
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

    ax2.set_title(race.id)
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
