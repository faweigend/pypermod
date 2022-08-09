import logging

import matplotlib.pyplot as plt
from pypermod.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from pypermod.fitter.tau_fit import TauFitter
from pypermod.utility import PlotLayout
from pypermod.simulator.simulator_basis import SimulatorBasis


def fit_taus_chidnok(plot: bool = False):
    """
    uses procedure outlined in Weigend et al. 2021 to determine tau values for W'bal-ode according to results reported
    by Chidnok et al. They prescribed a protocol of intermittent exercise of 60 second work bouts and 30 second recovery
    bouts until exhaustion. The intensity of recovery bouts varies. Please see the paper for more details.
    :param plot: whether debug plots should be displayed
    :return: three tau values, one for each protocol [tau_high, tau_med, tau_low]
    """

    hz = 1

    # averaged values from paper by Chidnok et al.
    cp = 241
    w_p = 21100
    # predefined intensities from paper by Chidnok et al.
    p6_p = 329
    # sev = 270 watts from Chidnok et al. is above CP and therefore ignored
    hig = 173
    med = 95
    low = 20
    # prescribed trials and reported mean time to exhaustions
    ground_truth_v = [557, 759, 1224]
    trials = [(p6_p, hig), (p6_p, med), (p6_p, low)]

    # fit tau to each protocol
    taus = []
    for i, t in enumerate(trials):
        # get tau using the designed fitter
        agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz)
        tau = TauFitter.get_tau_for_chidnok(agent=agent,
                                            p_exp=t[0],
                                            p_rec=t[1],
                                            tte=ground_truth_v[i])

        # check an agent with the exact fitted tau
        agent_fit = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau)
        # ... one with a slightly higher fitted tau ...
        agent_plus = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau + 0.5)
        # ... and one with a slightly lower fitted tau
        agent_minus = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau - 0.5)

        # let each agent simulate the whole protocol
        whole_protocol = ([t[0]] * 60 * hz + [t[1]] * 30 * hz) * 20
        bal = SimulatorBasis.simulate_course(agent=agent_fit, course_data=whole_protocol)
        bal_plus = SimulatorBasis.simulate_course(agent=agent_plus, course_data=whole_protocol)
        bal_minus = SimulatorBasis.simulate_course(agent=agent_minus, course_data=whole_protocol)

        # verify that resulting time to exhaustion of increased(plus) and decreased(minus) tau
        # are further away from targeted time to exhaustion
        tte_fit = bal.index(0) + 1  # plus 1 because time step 0 is the first second
        tte_plus = bal_plus.index(0) + 1
        tte_minus = bal_minus.index(0) + 1
        tte_gt = ground_truth_v[i]  # ground truth

        # check if fitted tau is an actual local minimum
        assert abs(tte_fit - tte_gt) <= abs(tte_plus - tte_gt)
        assert abs(tte_fit - tte_gt) <= abs(tte_minus - tte_gt)

        # store result
        taus.append(tau)

        # plot debug observations if required
        if plot:
            fig = plt.figure(figsize=(8, 5))
            PlotLayout.set_rc_params()
            ax = fig.add_subplot(1, 1, 1)
            ax.plot(bal_minus[:bal_minus.index(0) + 1], linewidth=5, color="tab:orange",
                    label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau - 0.5, 2)))
            ax.plot(bal[:bal.index(0) + 1], linewidth=2, color="tab:blue",
                    label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau, 2)))
            ax.plot(bal_plus[:bal_plus.index(0) + 1], linewidth=3, color="tab:green",
                    label="$W'_{bal-ode}\;with\;\mathcal{T} = $" + str(round(tau + 0.5, 2)))
            ax.scatter([bal.index(0), bal_plus.index(0), bal_minus.index(0)], [0, 0, 0],
                       label="points of exhaustion", color="red")
            ax.set_xticks([0, 59, 89, bal_plus.index(0), ground_truth_v[i] - 1, bal.index(0)])
            ax.set_xticklabels([1, 60, 90, tte_plus, tte_gt, tte_fit], rotation=-45)
            ax.axvline(ground_truth_v[i], label="target ground truth", color="grey", linestyle="--")
            ax.set_title("Chidnok protocol with recovery intensity {} watts".format(t[1]))
            ax.set_ylabel("$W'_{bal}$ (joules)")
            ax.set_xlabel("time (sec)")
            ax.legend()

            # small zoomed-in detail window
            insert_ax = ax.inset_axes([0.55, 0.50, 0.4, 0.4])
            insert_ax.scatter([bal.index(0), bal_minus.index(0)], [0, 0],
                              label="points of exhaustion", color="red",
                              s=60)
            insert_ax.plot(bal[:tte_fit], color="tab:blue", linewidth=3)
            insert_ax.plot(bal_minus[:tte_minus], color="tab:orange", linewidth=5)
            insert_ax.set_xlim((tte_fit - 2, tte_fit + 1))
            insert_ax.set_ylim((0, bal[tte_fit - 2]))
            insert_ax.set_xticks([bal.index(0), bal_minus.index(0)])
            insert_ax.set_xticklabels([tte_fit, tte_minus])
            insert_ax.set_title("detail view")

            plt.tight_layout()
            plt.show()

    return taus


if __name__ == "__main__":
    # set logging level to print info
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # obtain fitted taus and print them
    tau_high, tau_med, tau_low = fit_taus_chidnok(plot=True)
    logging.info("high: {} med: {} low {}".format(tau_high, tau_med, tau_low))
