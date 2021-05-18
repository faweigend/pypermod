import logging

import matplotlib
import matplotlib.pyplot as plt
from performance_modeling.w_pm_modeling.agents.cp_agents.cp_agent_bartram import CpAgentBartram
from performance_modeling.w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from performance_modeling.w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015
from performance_modeling.w_pm_modeling.simulation.simulator_basis import SimulatorBasis

from utility import plot_colors, plot_labels

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    matplotlib.rcParams['font.size'] = 12

    # agent parameters
    cp = 200
    w_p = 20000

    # the agent to perform simulations
    agent_sk15 = CpAgentSkiba2015(w_p, cp, hz=1)
    agent_bart = CpAgentBartram(w_p, cp, hz=1)
    agent_sk12 = CpAgentSkiba2012(w_p, cp)

    agents = [agent_sk12, agent_sk15, agent_bart]

    # Simulator takes agents and runs them through a simulation course
    sim = SimulatorBasis()

    # set up plot
    fig = plt.figure(figsize=(8, 5))
    ax2 = fig.add_subplot(2, 1, 1)
    ax = fig.add_subplot(2, 1, 2, sharex=ax2)

    # use simulator for every agent and plot result
    for agent in agents:
        times, powers, balances = sim.simulate_test_run(agent)
        ax2.plot(times,
                 balances,
                 color=plot_colors[agent.get_name()],
                 label=plot_labels[agent.get_name()])

    # plot power demands
    times, powers, balances = sim.simulate_test_run(agent_sk15)
    ax.plot(times, powers, color='black', label="intensity")

    # format axis
    ax.set_ylim([0, cp * 2.5])
    ax.axhline(y=cp, linestyle="--", color='red', label="critical power (CP)")

    # label plot
    ax.set_ylabel("exercise intensity")
    ax2.set_ylabel("W' balance")
    ax.set_xlabel("time (min)")

    ax.set_yticks([agent_sk15.cp])
    ax.set_yticklabels(["CP"])

    ax2.set_yticks([0, agent_sk15.w_p])
    ax2.set_yticklabels([0, "W'"])

    # format x ticks to minutes
    ax.set_xticks(range(0, int(times[-1]) + 5, 180))
    ax.set_xticklabels(int(x / 60) for x in ax.get_xticks())

    # legends
    ax.legend()
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    # plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
