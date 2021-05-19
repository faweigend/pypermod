import logging
import math

import numpy as np
from w_pm_modeling.agents.integral_agent_basis import IntegralAgentBasis


class CpIntegralAgentBasis(IntegralAgentBasis):
    """
    The virtual agent model employing the 2 parameter CP model for expenditure and providing a template
    for various recovery kinetics. Integral agents need the entire exercise to be known before estimations can be made.
    In the skiba2012 case that is because the recovery constant is estimated from the average recovery intensity
    of the whole exercise.
    * performance above CP drains W' in a linear fashion
    """

    def __init__(self, w_p: float, cp: float, hz: int):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """

        super().__init__(hz=hz)

        # constants
        self._w_p = w_p
        self._cp = cp

    @property
    def cp(self):
        """:return: critical power"""
        return self._cp

    @property
    def w_p(self):
        """:return: anaerobic capacity"""
        return self._w_p

    def get_expenditure_dynamics(self, p: float, w_bal: float = None):
        """
        returns expenditure dynamics given intensity p. Position 0 in the resulting array is time step 1.
        :param p:
        :param w_bal:
        :return: W'bal history starting with time step 1
        """

        # set start W' bal
        if w_bal is None:
            w_bal = self._w_p

        # no expenditure below or at CP
        if p <= self._cp:
            logging.warning("Not possible to model expenditure for p <= CP")
            return np.nan

        # reset internal params
        self.reset()

        # set parameters for expenditure estimation
        self._w_bal_hist = [w_bal]

        while self._get_last_entry() > 0:
            self._expend(p)

        # because it started with the initial time step using wp
        self._w_bal_hist = self._w_bal_hist[1:]
        return self._w_bal_hist

    def get_tte(self, p: float, w_bal: float = None):
        """
        estimates the time until exhaustion with given power
        :param p:
        :param w_bal: the W'bal to start with
        :return: tte in seconds
        """
        if w_bal is None:
            w_bal = self._w_p
        dynamics = self.get_expenditure_dynamics(p=p, w_bal=w_bal)
        return len(dynamics)

    def get_recovery_dynamics(self, p_rec: float, init_w_bal: float = None, max_t: float = 5000):
        """
        Returns recovery dynamics given recovery power p. Position 0 in the resulting array is the initial w'bal.
        The integral approach does not consider changes in p_rec during recovery estimations.
        :param p_rec: recovery bout intensity
        :param init_w_bal: the W'bal to start recovery from
        :param max_t: maximal time steps to be computed
        :return: W'bal history starting at second 0
        """
        # reset internal params
        self.reset()

        if p_rec >= self._cp:
            logging.warning("Not possible to model recovery for p >= CP")
            return np.nan

        # set needed parameters for recovery estimation
        if init_w_bal is None:
            self._w_bal_hist = [0.0]
        else:
            self._w_bal_hist = [init_w_bal]

        self._dcp = self._cp - p_rec
        self._u = self._hz_t
        self._w_u = self._w_p - self._get_last_entry()

        while self._get_last_entry() < self._w_p and self._t < max_t:
            self._t += 1
            # consider hz for recovery steps
            self._hz_t = self._t / self._hz
            self._recover()

        # because it started with the initial time step using wp
        return self._w_bal_hist

    def estimate_w_p_bal_to_data(self, data):
        """
        simple setter for the data to be processed with a trigger to initiate processing
        :param data:
        :return resulting W'bal history
        """
        return self._process_data(data)

    def _process_data(self, data):
        """
        walks through stored data and creates the corresponding W'bal history
        """
        np_data = np.array(data)
        w_bal_hist = []

        # dcp only works if power demand is below CP at any point
        if np.any(np_data[(np_data - self._cp) < 0]):
            dcp = self._cp - np.mean(np_data[(np_data - self._cp) < 0])
        else:
            dcp = 0

        # Wexp is the cumulative sum of expended energy above CP
        np_exp = np.where((np_data - self._cp) > 0, np_data - self._cp, 0)

        # EQ (3) in Skiba et al. 2012
        tau = 546 * pow(math.e, (-0.01 * dcp)) + 316

        # EQ (2) in Skiba et al. 2012
        for t in range(len(np_data)):
            sum_t = 0
            for u in range(t):
                sum_t += np_exp[u] * pow(math.e, -(t - u) / tau)
            w_bal_hist.append(self._w_p - sum_t)

        return w_bal_hist
