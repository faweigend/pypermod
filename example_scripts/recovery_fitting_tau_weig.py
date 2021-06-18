import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from w_pm_modeling.fitter.tau_to_recovery_fitter import TauToRecoveryFitter

if __name__ == "__main__":

    # an agent with adjustable time constant tau
    tau_agent = WbalODEAgentFixTau(w_p=12800, cp=248, hz=10)

    # intensities used by Caen et al.
    p4 = (tau_agent.w_p + 240 * tau_agent.cp) / 240
    p8 = (tau_agent.w_p + 480 * tau_agent.cp) / 480
    cp33 = tau_agent.cp * 0.33
    cp66 = tau_agent.cp * 0.66

    # separated ground truth values from the paper by Caen et al.
    ground_truth_t = [120, 240, 360]
    ground_truth_p4_cp33 = [55.0, 61.0, 70.5]
    ground_truth_p4_cp66 = [49.0, 55.0, 58.5]
    ground_truth_p8_cp33 = [42.0, 52.0, 59.5]
    ground_truth_p8_cp66 = [38.0, 37.5, 50.0]

    # combine intensities in DCP groups
    gt_cp33 = ground_truth_p4_cp33 + ground_truth_p8_cp33
    gt_cp66 = ground_truth_p4_cp66 + ground_truth_p8_cp66


    def get_tau(agent, rec_ratio, t_rec):
        """
        double-check with Caen simulation
        :param agent:
        :param rec_ratio:
        :param t_rec:
        :return:
        """
        tau = TauToRecoveryFitter.get_tau_for_rec(agent.w_p, rec=rec_ratio, t_rec=t_rec)
        # tau_agent.tau = tau
        # caen_rec = SimulatorBasis.get_recovery_ratio_caen(agent, p_exp=p4, p_rec=cp33, t_rec=t_rec)
        # assert abs(rec_ratio - caen_rec) < 1.0
        return tau


    # fit tau to each obseravtions
    tau_cp33 = []
    tau_cp66 = []
    for i, t in enumerate(ground_truth_t):
        tau_cp33.append(get_tau(tau_agent, ground_truth_p4_cp33[i], t))
        print("{} P240 CP33: {:.2f}".format(t, tau_cp33[-1]))
        tau_cp33.append(get_tau(tau_agent, ground_truth_p8_cp33[i], t))
        print("{} P480 CP33: {:.2f}".format(t, tau_cp33[-1]))
        tau_cp66.append(get_tau(tau_agent, ground_truth_p4_cp66[i], t))
        print("{} P240 CP66: {:.2f}".format(t, tau_cp66[-1]))
        tau_cp66.append(get_tau(tau_agent, ground_truth_p8_cp66[i], t))
        print("{} P480 CP66: {:.2f}".format(t, tau_cp66[-1]))


    def skib_tau_func(dcp, a, b, c):
        """
        the relationship between tau and dcp is assumed to be exponential
        :param dcp:
        :param a:
        :param b:
        :param c:
        :return:
        """
        return a * np.exp(b * dcp) + c


    def bart_tau_func_three(dcp, a, b, c):
        """
        the relationship between tau and dcp is assumed to be exponential
        :param dcp:
        :param a:
        :param b:
        :param c:
        :return:
        """
        return a * pow(dcp, b) + c


    def bart_tau_func_two(dcp, a, b):
        """
        the relationship between tau and dcp is assumed to be exponential
        :param dcp:
        :param a:
        :param b:
        :return:
        """
        return a * pow(dcp, b)


    # the tau function to fit
    tau_func = bart_tau_func_three

    # The model function, f(x, ...).  It must take the independent
    # variable as the first argument and the parameters to fit as
    # separate remaining arguments.
    popt, pcov = curve_fit(tau_func,
                           np.array([tau_agent.cp - cp33] * len(tau_cp33) + [tau_agent.cp - cp66] * len(tau_cp66)),
                           np.array(tau_cp33 + tau_cp66),
                           [2287.2, -0.688, 0])

    # estimate the r2 score for comparison
    true = np.array(tau_cp33 + tau_cp66)
    pred = []
    for d in np.array([tau_agent.cp - cp33] * len(tau_cp33) + [tau_agent.cp - cp66] * len(tau_cp66)):
        pred.append(tau_func(d, popt[0], popt[1], popt[2]))
    r2 = r2_score(true, pred)

    # plot the observations
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter([tau_agent.cp - cp33] * len(tau_cp33), tau_cp33, label="CP33 observations")
    ax.scatter([tau_agent.cp - cp66] * len(tau_cp66), tau_cp66, label="CP66 observations")

    # plot the fitted function
    fit = []
    for i in range(-10, tau_agent.cp):
        fit.append(tau_func(i, popt[0], popt[1], popt[2]))
    print(popt[0], popt[1], popt[2])

    ax.plot(range(-10, tau_agent.cp), fit, label="best exponential fit (r2 = {})".format(round(r2, 2)))

    # finish layout
    ax.set_xlabel(r'$D_{CP}$')
    ax.set_ylabel(r'$\tau_{W\prime}$')
    ax.legend()
    plt.show()
