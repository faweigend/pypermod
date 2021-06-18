import matplotlib.pyplot as plt
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from w_pm_modeling.simulator.simulator_basis import SimulatorBasis
from w_pm_modeling.performance_modeling_utility import PlotLayout

from handler.simple_fitter.tau_to_recovery_fitter import TauToRecoveryFitter

if __name__ == "__main__":

    # integral fittings
    # tau hig = 575.4354880396651
    # tau med = 421.5942777689478
    # tau low = 358.4483193342969

    # differential fittings
    # tau hig = 165.18618033787732
    # tau med = 124.81202219606148
    # tau low = 107.45698149305554

    hz = 1

    # averaged values from paper
    cp = 241
    w_p = 21100

    # predefined intensities from paper
    p6_p = 329
    # sev = 270 # this one is above CP!
    hig = 173
    med = 95
    low = 20

    ground_truth_v = [557, 759, 1224]
    trials = [(p6_p, hig), (p6_p, med), (p6_p, low)]

    # fit tau to each protocol
    for i, t in enumerate(trials):
        # get tau using the designed fitter
        tau = TauToRecoveryFitter.get_tau_for_chidnok_ode(w_p=w_p, cp=cp,
                                                          p_exp=t[0],
                                                          p_rec=t[1],
                                                          tte=ground_truth_v[i])

        # double-check found tau in simulation
        agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau)
        agent2 = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau + 0.5)
        agent3 = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau - 0.5)
        whole_test = ([t[0]] * 60 * hz + [t[1]] * 30 * hz) * 20
        bal = SimulatorBasis.simulate_course(agent=agent, course_data=whole_test)
        bal2 = SimulatorBasis.simulate_course(agent=agent2, course_data=whole_test)
        bal3 = SimulatorBasis.simulate_course(agent=agent3, course_data=whole_test)

        # print tau and tte error
        print(abs(bal.index(0) + 1 - ground_truth_v[i]))
        print(tau)

        # plot the observations
        fig = plt.figure(figsize=(8, 5))
        PlotLayout.set_rc_params()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(bal3[:bal3.index(0) + 1], linewidth=5, color="tab:orange",
                label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau - 0.5, 2)))
        ax.plot(bal[:bal.index(0) + 1], linewidth=2, color="tab:blue",
                label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau, 2)))
        ax.plot(bal2[:bal2.index(0) + 1], linewidth=3, color="tab:green",
                label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau + 0.5, 2)))
        ax.scatter([bal.index(0), bal2.index(0), bal3.index(0)], [0, 0, 0], label="points of exhaustion", color="red")
        ax.set_xticks([0, 59, 89, bal2.index(0), ground_truth_v[i] - 1, bal.index(0)])
        ax.set_xticklabels([1, 60, 90, bal2.index(0) + 1, ground_truth_v[i], bal.index(0) + 1], rotation=-45)
        ax.axvline(ground_truth_v[i], label="target ground truth", color="grey", linestyle="--")
        ax.set_title("Chidnok protocol with recovery intensity {} watts".format(t[1]))
        ax.set_ylabel("$W'_{bal}$ (joules)")
        ax.set_xlabel("time (sec)")
        ax.legend()

        # small zoomed-in detail window
        insert_ax = ax.inset_axes([0.55, 0.50, 0.4, 0.4])
        insert_ax.scatter([bal.index(0), bal3.index(0)], [0, 0], label="points of exhaustion", color="red", s=60)
        insert_ax.plot(bal[:(bal.index(0) + 1)], color="tab:blue", linewidth=3)
        insert_ax.plot(bal3[:(bal3.index(0) + 1)], color="tab:orange", linewidth=5)
        insert_ax.set_xlim((bal.index(0) - 1, bal.index(0) + 2))
        insert_ax.set_ylim((0, bal[bal.index(0) - 1]))
        insert_ax.set_xticks([bal.index(0), bal3.index(0)])
        insert_ax.set_xticklabels([bal.index(0)+1, bal3.index(0)+1])
        insert_ax.set_title("detail view")

        plt.tight_layout()
        plt.show()
