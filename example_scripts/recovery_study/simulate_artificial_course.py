import logging

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pypermod.agents.wbal_agents.wbal_int_agent_skiba import WbalIntAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_linear import CpODEAgentBasisLinear
from pypermod.simulator.simulator_basis import SimulatorBasis
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12

    hz = 1

    # agent parameters
    cp = 200
    w_p = 20000

    # the agent to perform simulations
    agent_lin = CpODEAgentBasisLinear(w_p=w_p, cp=cp, hz=hz)
    agent_ode = WbalODEAgentSkiba(w_p, cp, hz=hz)
    agent_wei = WbalODEAgentWeigend(w_p, cp, hz=hz)
    agent_int = WbalIntAgentSkiba(w_p, cp)
    agent_bar = WbalODEAgentBartram(w_p, cp, hz=hz)

    inter = 180
    # the power demands over the artificial course
    pow_course = [150] * inter + \
                 [250] * inter + \
                 [150] * inter + \
                 [250] * inter + \
                 [250] * inter + \
                 [150] * inter + \
                 [150] * inter + \
                 [250] * inter + \
                 [200] * inter
    pow_times = np.arange(len(pow_course))

    # we start predicted W'bal with second 1 because simulations omit the initial time step 0
    sim_times = pow_times + 1

    agents = [agent_int, agent_lin]

    # set up plot
    fig = plt.figure(figsize=(8, 5))
    ax2 = fig.add_subplot(2, 1, 1)
    ax = fig.add_subplot(2, 1, 2, sharex=ax2)

    # use simulator for every agent and plot result
    for agent in agents:
        balances = SimulatorBasis.simulate_course(agent, course_data=pow_course)
        ax2.plot(sim_times,
                 balances,
                 color=PlotLayout.get_plot_color(agent.get_name()),
                 label=PlotLayout.get_plot_label(agent.get_name()))

    # plot power demands
    ax.plot(pow_times, pow_course, color='black', label="intensity")

    # format axis
    ax.set_ylim([0, cp * 2.5])
    ax.set_ylabel("power output (watts)")
    ax.set_xlabel("time (min)")
    ax.set_yticks([agent_ode.cp])
    ax.set_yticklabels(["CP"])
    ax.tick_params(axis='y', colors='red')
    ax.axhline(y=cp, linestyle="--", color='red', label="critical power (CP)")
    # format x ticks to minutes
    ax.set_xticks(range(0, len(pow_course) + 5, 180))
    ax.set_xticklabels(int(x / 60) for x in ax.get_xticks())

    ax2.set_ylabel(r'$W^\prime$' + " balance (joules)")
    ax2.set_yticks([0, agent_ode.w_p])
    ax2.set_yticklabels([0, r'$W^\prime$'])
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    plt.tight_layout()
    plt.show()
