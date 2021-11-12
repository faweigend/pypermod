import logging

import matplotlib.pyplot as plt
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.simulator.simulator_basis import SimulatorBasis
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # agent parameters
    cp = 200
    w_p = 20000

    # the agent to perform simulations
    agent_ode = WbalODEAgentSkiba(w_p, cp, hz=hz)
    agent_wei = WbalODEAgentWeigend(w_p, cp, hz=hz)
    agent_bar = WbalODEAgentBartram(w_p, cp, hz=hz)

    inter = 180
    # the power demands over the artificial course
    course = [100] * inter + \
             [250] * inter + \
             [100] * inter + \
             [250] * inter + \
             [50] * inter + \
             [50] * inter + \
             [50] * inter + \
             [300] * inter + \
             [200] * inter

    agents = [agent_ode, agent_bar, agent_wei]

    # set up plot
    fig = plt.figure(figsize=(8, 5))
    ax2 = fig.add_subplot(2, 1, 1)
    ax = fig.add_subplot(2, 1, 2, sharex=ax2)

    # use simulator for every agent and plot result
    for agent in agents:
        balances = SimulatorBasis.simulate_course(agent, course_data=course)
        ax2.plot(balances,
                 color=PlotLayout.get_plot_color(agent.get_name()),
                 label=PlotLayout.get_plot_label(agent.get_name()))

    # plot power demands
    ax.plot(course, color='black', label="intensity")

    # format axis
    ax.set_ylim([0, cp * 2.5])

    # label plot
    ax.set_ylabel("power output (watts)")
    ax2.set_ylabel(r'$W^\prime$' + " balance (joules)")
    ax.set_xlabel("time (min)")

    ax.set_yticks([agent_ode.cp])
    ax.set_yticklabels(["CP"])
    ax.tick_params(axis='y', colors='red')
    ax.axhline(y=cp, linestyle="--", color='red', label="critical power (CP)")

    ax2.set_yticks([0, agent_ode.w_p])
    ax2.set_yticklabels([0, r'$W^\prime$'])

    # format x ticks to minutes
    ax.set_xticks(range(0, len(course) + 5, 180))
    ax.set_xticklabels(int(x / 60) for x in ax.get_xticks())

    # legends
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    # plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
