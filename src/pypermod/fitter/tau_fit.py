import math

import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from pypermod.agents.wbal_agents.wbal_int_agent_fix_tau import WbalIntAgentFixTau
from pypermod.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from pypermod.simulator.simulator_basis import SimulatorBasis


class TauFitter:
    """
    Provides functions to fit a Tau for W'bal models (ode or int) to recovery ratios or
    recovery estimation protocols
    """

    @staticmethod
    def f_exp_rec(tau: float, t_rec: float, act_rec: float):
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
    def get_tau_for_act_rec(act_rec: float, t_rec: float):
        """
        fits a time constant tau to given recovery ratio with an iterative process
        :param act_rec:
        :param t_rec:
        :return: best found tau
        """
        fit_tau = minimize(TauFitter.f_exp_rec, x0=np.array([200]), args=(t_rec, act_rec))
        return fit_tau.x[0]

    @staticmethod
    def f_chidnok_ode(tau: float, agent: WbalODEAgentFixTau, p_exp: float, p_rec: float, act_tte: int):
        """
        function to be minimized. Estimates predicted time to exhaustion of a W'bal-ode agent with given tau with the
        protocol prescribed by Chidnok et al. (60 sec p_work into 30 sec p_rec until exhaustion).
        :param tau: tau for W'bal-ode agent
        :param agent: agent with w' and cp and hz setting
        :param p_exp: intensity for work bouts
        :param p_rec: intensity for recovery bouts
        :param act_tte: expected ground truth time to exhaustion
        :return: difference measure to be minimized
        """

        # one estimation per second was found to be sufficient
        hz = 1
        if agent.hz != hz:
            raise UserWarning("Agent hz has to be set to {}".format(hz))

        # reset everything
        agent.reset()
        agent.set_tau(tau)

        # create whole test protocol
        whole_test = ([p_exp] * 60 * hz + [p_rec] * 30 * hz) * 20

        # simulate protocol until exhaustion
        bal = []
        while not agent.is_exhausted() and len(whole_test) > 0:
            agent.set_power(whole_test.pop(0))
            agent.perform_one_step()
            bal.append(agent.get_w_p_balance())

        if not agent.is_exhausted():
            # if agent not exhausted after 20 intervals
            end_t = 0  # worst case -> maximal distance to tte
        else:
            # otherwise note time of exhaustion
            end_t = agent.get_time()

        if end_t >= act_tte:
            # minimise w'bal at expected time of exhaustion
            return bal[act_tte - 1]
        else:
            # minimise distance to time to exhaustion
            return agent.w_p * (act_tte - end_t)

    @staticmethod
    def f_chidnok_int(tau: float, agent: WbalIntAgentFixTau, p_exp: float, p_rec: float, act_tte: int):
        """
        function to be minimized. Estimates predicted time to exhaustion of a W'bal-int agent with given tau with the
        protocol prescribed by Chidnok et al. (60 sec p_work into 30 sec p_rec until exhaustion).
        :param tau: tau for W'bal-ode agent
        :param agent: agent with w' and cp and hz setting
        :param p_exp: intensity for work bouts
        :param p_rec: intensity for recovery bouts
        :param act_tte: expected ground truth time to exhaustion
        :return: difference measure to be minimized
        """
        # one estimation per second was found to be sufficient
        hz = 1
        if agent.hz != hz:
            raise UserWarning("Agent hz has to be set to {}".format(hz))

        # reset everything
        agent.reset()
        agent.set_tau(tau)

        # create protocol with max length of TTE
        whole_test = ([p_exp] * 60 + [p_rec] * 30) * 20
        whole_test = whole_test[:act_tte]

        # estimate wbal and find point of exhaustion
        bal = SimulatorBasis.simulate_course(agent, whole_test)
        try:
            end_t = bal.index(0)
        except ValueError:
            end_t = 60 * 30 * 20

        if end_t >= act_tte:
            # balance at tte to minimize
            return bal[act_tte - 1]
        else:
            # if exhaustion not reached, minimise according to distance to tte
            return agent.w_p * (act_tte - end_t)

    @staticmethod
    def get_tau_for_chidnok(agent, p_exp: float, p_rec: float, tte: int):
        """
        fits a time constant tau to given chidnok trial setup
        :return: best found tau
        """

        # distinguish between possible agent types
        if isinstance(agent, WbalODEAgentFixTau):
            opt_func = TauFitter.f_chidnok_ode
        elif isinstance(agent, WbalIntAgentFixTau):
            opt_func = TauFitter.f_chidnok_int
        else:
            raise UserWarning("Agent type has to be {} or {}".format(WbalIntAgentFixTau, WbalODEAgentFixTau))

        # find optimal tau
        fit_tau = minimize_scalar(opt_func,
                                  args=(agent, p_exp, p_rec, tte),
                                  bounds=(100, 500),
                                  method='bounded')
        return fit_tau["x"]
