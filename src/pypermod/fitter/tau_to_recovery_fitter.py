import math

import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from pypermod.agents.wbal_agents.wbal_int_agent_fix_tau import WbalIntAgentFixTau
from pypermod.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from pypermod.simulator.simulator_basis import SimulatorBasis


class TauToRecoveryFitter:
    """
    Provides functions to fit a Tau for W'bal models (ode or int) to given recovery ratios or
    recovery estimation protocols
    """

    @staticmethod
    def exp_rec(tau: float, t_rec: float, act_rec: float):
        """
        Returns the absolute difference of an exponential recovery function with given Tau and the expected recovery.
        :param tau: tau to be used for the exponential recovery as implemented by W'bal models
        :param t_rec: recovery time
        :param act_rec: actual (observed) recovery after given recovery time
        :return: absolute difference between estimated recovery using tau and given act_rec
        """
        ratio = (1.0 - pow(math.e, -t_rec / tau)) * 100.0
        return abs(act_rec - ratio)

    @staticmethod
    def skiba_int_tau_to_ode_tau(tau: float, cp: float, w_p: float):
        p360 = w_p / 360 + cp
        p_exp = p360 + (p360 - cp) / 2
        s20_rec = 20
        hz = 1

        agent = WbalIntAgentFixTau(w_p=w_p, cp=cp, tau=tau, hz=hz)
        whole_test = ([p_exp] * 60 + [s20_rec] * 30) * 20
        bal = agent.estimate_w_p_bal_to_data(whole_test)
        tte = bal.index(0)

        fit_tau = minimize_scalar(TauToRecoveryFitter.skiba_rec_ode,
                                  args=(w_p, cp, tte),
                                  bounds=(100, 1000),
                                  method='bounded')
        return fit_tau["x"]

    @staticmethod
    def skiba_rec_ode(tau: float, w_p: float, cp: float, tte: int):
        p360 = w_p / 360 + cp
        p_exp = p360 + (p360 - cp) / 2
        s20_rec = 20
        hz = 1
        agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz)
        agent.tau = tau

        whole_test = ([p_exp] * 60 + [s20_rec] * 30) * 20
        whole_test = whole_test[:tte]

        bal = []
        while not agent.is_exhausted() and len(whole_test) > 0:
            agent.set_power(whole_test.pop(0))
            agent.perform_one_step()
            bal.append(agent.get_w_p_balance())

        if not agent.is_exhausted():
            end_t = 0
        else:
            end_t = agent.get_time()

        if end_t >= tte:
            return bal[tte - 1]
        else:
            return w_p * (tte - end_t)

    @staticmethod
    def chidnok_rec_int(tau: float, w_p: float, cp: float, p_exp: float, p_rec: float, tte: int):
        """
        a function with objective to minimise according to best fit to Chidnok protocol
        :param tau:
        :param w_p:
        :param cp:
        :param p_exp:
        :param p_rec:
        :param tte:
        :return:
        """
        # create integral agent
        agent = WbalIntAgentFixTau(w_p=w_p, cp=cp, hz=1)
        agent.tau = tau

        # create protocol with max length of TTE
        whole_test = ([p_exp] * 60 + [p_rec] * 30) * 20
        whole_test = whole_test[:tte]

        # estimate wbal and find point of exhaustion
        bal = SimulatorBasis.simulate_course(agent, whole_test)
        try:
            end_t = bal.index(0)
        except ValueError:
            end_t = 60 * 30 * 20

        if end_t >= tte:
            # balance at tte to minimize
            return bal[tte - 1]
        else:
            # if exhaustion not reached, minimise according to distance to tte
            return w_p * (tte - end_t)

    @staticmethod
    def chidnok_rec_ode(tau: float, w_p: float, cp: float, p_exp: float, p_rec: float, tte: int):
        hz = 1
        agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau)

        whole_test = ([p_exp] * 60 * hz + [p_rec] * 30 * hz) * 20

        bal = []
        while not agent.is_exhausted() and len(whole_test) > 0:
            agent.set_power(whole_test.pop(0))
            agent.perform_one_step()
            bal.append(agent.get_w_p_balance())

        if not agent.is_exhausted():
            end_t = 0  # worst case -> maximal distance to tte
        else:
            end_t = agent.get_time()

        if end_t >= tte:
            return bal[tte - 1]
        else:
            return w_p * (tte - end_t)

    @staticmethod
    def get_tau_for_chidnok_int(w_p: float, cp: float, p_exp: float, p_rec: float, tte: int):
        """
        fits a time constant tau to given chidnok trial setup
        :return: best found tau
        """
        fit_tau = minimize_scalar(TauToRecoveryFitter.chidnok_rec_int,
                                  args=(w_p, cp, p_exp, p_rec, tte),
                                  bounds=(100, 1000),
                                  method='bounded')
        return fit_tau["x"]

    @staticmethod
    def get_tau_for_chidnok_ode(w_p: float, cp: float, p_exp: float, p_rec: float, tte: int):
        """
        fits a time constant tau to given chidnok trial setup
        :return: best found tau
        """
        fit_tau = minimize_scalar(TauToRecoveryFitter.chidnok_rec_ode,
                                  args=(w_p, cp, p_exp, p_rec, tte),
                                  bounds=(100, 500),
                                  method='bounded')
        return fit_tau["x"]

    @staticmethod
    def get_tau_for_act_rec(act_rec: float, t_rec: float):
        """
        fits a time constant tau to given recovery ratio with an iterative process
        :param act_rec:
        :param t_rec:
        :return: best found tau
        """
        fit_tau = minimize(TauToRecoveryFitter.exp_rec, x0=np.array([200]), args=(t_rec, act_rec))
        return fit_tau.x[0]
