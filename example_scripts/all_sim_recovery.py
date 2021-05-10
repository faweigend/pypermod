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

    # the agent to perform simulations
    agent_sk15 = CpAgentSkiba2015(20000, 200, hz=1)
    agent_bart = CpAgentBartram(20000, 200, hz=1)
    agent_sk12 = CpAgentSkiba2012(20000, 200)

    agents = [agent_sk12, agent_sk15, agent_bart]

    # run simulations to obtain power data
    sim = SimulatorBasis()

    matplotlib.rcParams['font.size'] = 12

    # plot the data
    fig = plt.figure(figsize=(8, 5))

    # set up plot
    ax2 = fig.add_subplot(2, 1, 1)
    ax = fig.add_subplot(2, 1, 2, sharex=ax2)

    for agent in agents:
        times, powers, balances = sim.simulate_test_run(agent)
        ax2.plot(times,
                 balances,
                 color=plot_colors[agent.get_name()],
                 label=plot_labels[agent.get_name()])

    # plot curves
    times, powers, balances = sim.simulate_test_run(agent_sk15)
    ax.plot(times, powers, color='black', label="intensity")

    # if exhaustion is not None:
    #     area = []
    #     for i in range(1, len(exhaustion)):
    #         if exhaustion[i] != exhaustion[i - 1]:
    #             area.append(times[i])
    #             if len(area) > 1:
    #                 ax.axvspan(area[0], area[1], color='red', alpha=0.3)
    #                 area.clear()

    ax.set_ylim([0, agent_sk15.cp * 2.5])
    ax.axhline(y=agent_sk15.cp, linestyle="--", color='red', label="critical power (CP)")

    # label plot
    # ax.set_title('W\' balance plot')
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
    ax.set_xticklabels(int(x / 60) for x in ax.get_xticks())

    # legends
    ax.legend()
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    # plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
