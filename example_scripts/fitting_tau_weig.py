import logging

import matplotlib.pyplot as plt
import numpy as np
from pypermod.simulator.simulator_basis import SimulatorBasis
from pypermod.utility import PlotLayout
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from pypermod.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from pypermod.fitter.tau_fitter import TauFitter


def get_tau(act_rec, t_rec, p_exp, p_rec):
    """
    Fit a tau to observed recovery ratio after given recovery time.
    The resulting tau is double-checked in a second
    simulation using the wb1->rb->wb2 protocol.
    :param act_rec: actually observed recovery ratio
    :param t_rec: recovery time of actually observed recovery
    :param p_exp: expenditure intensity for double-check
    :param p_rec: recovery intensity for double-check
    :return: fitted tau
    """
    tau = TauFitter.get_tau_for_act_rec(act_rec=act_rec, t_rec=t_rec)
    test_agent = WbalODEAgentFixTau(w_p=12800, cp=248, hz=10, tau=tau)
    caen_rec = SimulatorBasis.get_recovery_ratio_caen(test_agent, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
    assert abs(act_rec - caen_rec) < 1.0
    return tau


def f_tau_dcp_exp(dcp, a, b, c):
    """
    The function (f) to be fitted.
    The relationship between tau and dcp is assumed to be exponential.
    :param dcp: given dcp
    :param a: fitting param 1
    :param b: fitting param 2
    :param c: fitting param 3
    :return: result
    """
    return a * np.exp(dcp * b) + c


def fit_tau_weig(plot: bool = False):
    """
    uses procedure outlined in Weigend et al. 2021 to determine exponential relationship of tau to DCP derived from measures
    by Caen et al. 2019 and Weigend et al. 2021
    :param plot: whether a plot of the used data points and exponential fitting should be displayed
    :return: a,b,c of tau=a*e^(dcp*b)+c relationship
    """

    # intensities and group averages by Caen et al. 2019
    w_p = 12800
    cp = 248
    p4 = (w_p + 240 * cp) / 240
    p8 = (w_p + 480 * cp) / 480
    cp33 = cp * 0.33
    cp66 = cp * 0.66

    # separated ground truth values from the paper by Caen et al. 2019
    gt_t = [120, 240, 360]

    # ground truth actual recovery ratios derived by Weigend et al. 2021 from Caen et al. 2019
    gt_p4_cp33 = [55.0, 61.0, 70.5]
    gt_p8_cp33 = [42.0, 52.0, 59.5]
    gt_p4_cp66 = [49.0, 55.0, 58.5]
    gt_p8_cp66 = [38.0, 37.5, 50.0]

    # fit a tau to each setup and combine fittings into cp33 and cp66 groups
    tau_cp33s = []
    tau_cp66s = []
    for i, t in enumerate(gt_t):
        tau_cp33s.append(get_tau(gt_p4_cp33[i], t, p_exp=p4, p_rec=cp33))
        logging.info("fitted tau for {} P240 CP33 is: {:.2f}".format(t, tau_cp33s[-1]))
        tau_cp33s.append(get_tau(gt_p8_cp33[i], t, p_exp=p8, p_rec=cp33))
        logging.info("fitted tau for {} P480 CP33 is: {:.2f}".format(t, tau_cp33s[-1]))
        tau_cp66s.append(get_tau(gt_p4_cp66[i], t, p_exp=p4, p_rec=cp66))
        logging.info("fitted tau for {} P240 CP66 is: {:.2f}".format(t, tau_cp66s[-1]))
        tau_cp66s.append(get_tau(gt_p8_cp66[i], t, p_exp=p8, p_rec=cp66))
        logging.info("fitted tau for {} P480 CP66 is: {:.2f}".format(t, tau_cp66s[-1]))

    # data points to fit to
    dcp_cp33s = [cp - cp33] * len(tau_cp33s)
    dcp_cp66s = [cp - cp66] * len(tau_cp66s)
    x_data = np.array(dcp_cp33s + dcp_cp66s)
    y_data = np.array(tau_cp33s + tau_cp66s)

    # the tau function to fit
    # The model function, f(x, ...).  It must take the independent
    # variable as the first argument and the parameters to fit as
    # separate remaining arguments.
    tau_func = f_tau_dcp_exp

    # use scipy curve fit to obtain a,b,c
    popt, pcov = curve_fit(f=tau_func,
                           xdata=x_data,
                           ydata=y_data,
                           p0=np.array([546, -0.01, 316]))
    if plot:
        # estimate the r2 score for comparison
        pred = []
        for x in np.array(x_data):
            pred.append(tau_func(x, popt[0], popt[1], popt[2]))
        r2 = r2_score(y_data, pred)

        # plot the observations
        fig = plt.figure(figsize=(7, 4))
        PlotLayout.set_rc_params()
        ax = fig.add_subplot(1, 1, 1)
        ax.scatter(dcp_cp33s, tau_cp33s, label="CP33 observations")
        ax.scatter(dcp_cp66s, tau_cp66s, label="CP66 observations")

        # plot the fitted function
        plot_range = range(0, cp)
        fit = []
        for i in plot_range:
            fit.append(tau_func(i, popt[0], popt[1], popt[2]))
        ax.plot(range(0, cp), fit, label="best exponential fit (r2 = {})".format(round(r2, 2)))

        # finish layout
        ax.set_xlabel(r'$D_{CP}$')
        ax.set_ylabel(r'$\tau_{W\prime}$')
        ax.legend()
        plt.tight_layout()
        plt.show()

    return popt[0], popt[1], popt[2]


if __name__ == "__main__":
    # set logging level to print info
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    x, y, z = fit_tau_weig(plot=True)

    # print fitted parameters
    logging.info("fitted parameters for tau_weig: \n a = {} \n b = {} \n c = {} \n".format(x, y, z))
