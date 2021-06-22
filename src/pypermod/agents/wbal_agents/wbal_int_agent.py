import logging
import math
from abc import abstractmethod

import numpy as np
from pypermod.agents.cp_agent_basis import CpAgentBasis


class WbalIntAgent(CpAgentBasis):
    """
    The virtual agent model. Integral agents need the entire exercise to be
    known before estimations can be made. A convolutional integral is applied.
    """

    @abstractmethod
    def _get_tau_to_dcp(self, dcp: float):
        """
        Estimate tau from given dcp
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """

    def get_expenditure_dynamics(self, p_exp, dcp: float = None):
        """
        returns expenditure dynamics given intensity p. Position 0 in the resulting array is time step 1.
        :param p_exp: constant exercise intensity
        :param dcp: (optional) average difference to CP used for the determination of tau
        :return: W'bal history
        """

        # no expenditure below or at CP
        if p_exp <= self._cp:
            logging.warning("Not possible to model expenditure for p <= CP")
            return np.nan

        # a custom DCP might be set to experiment with behaviour...
        if dcp is None:
            # ... if not, DCP is 0 in this case because it is a TTE
            dcp = 0

        tau = self._get_tau_to_dcp(dcp)

        # use parent class method
        return self._get_expenditure_dynamics(p_exp=p_exp, tau=tau)

    def get_tte(self, p_exp: float):
        """
        estimates the time until exhaustion at given constant exercise intensity in Watts
        :param p_exp: constant exercise intensity in Watts
        :return: tte in seconds
        """
        dynamics = self.get_expenditure_dynamics(p_exp=p_exp)
        return len(dynamics)

    def get_recovery_dynamics(self, p_rec: float, max_steps: int):
        """
        Returns recovery dynamics given recovery power p. Position 0 in the resulting array is the initial w'bal.
        The integral approach does not consider changes in p_rec during recovery estimations.
        :param p_rec: recovery bout intensity in Watts
        :param max_steps: when to stop
        :return: W'bal history
        """

        if p_rec >= self._cp:
            logging.warning("Not possible to model recovery for p >= CP")
            return np.nan

        dcp = self._cp - p_rec
        tau = self._get_tau_to_dcp(dcp)

        w_bal_hist = [0]
        w_exp = self._w_p

        # EQ (2) in Skiba et al. 2012
        t = 1
        while t <= max_steps and w_bal_hist[-1] < self._w_p:
            sum_t = w_exp * pow(math.e, -t / tau)

            # apply limits
            sum_t = min(sum_t, self._w_p)
            w_bal = self._w_p - sum_t
            w_bal_hist.append(w_bal)
            t += 1

        # because it started with the initial time step using wp
        return w_bal_hist

    def estimate_w_p_bal_to_data(self, data):
        """
        initiate processing data and kick off W'bal history estimation
        :param data:
        :return resulting W'bal history
        """
        np_data = np.array(data)
        # dcp only works if power demand is below CP at any point
        if np.any((np_data - self._cp) < 0):
            dcp = self._cp - np.mean(np_data[(np_data - self._cp) < 0])
        else:
            logging.warning("No recovery found in data. DCP set to 0")
            dcp = 0
        tau = self._get_tau_to_dcp(dcp)
        # use parent class method
        return self._process_data(data, tau)

    def _process_data(self, data: np.array, tau: float):
        """
        walks through data and creates the corresponding W'bal history
        :param data: power demand data to simulate
        :param tau: recovery time constant to use
        :return: W'bal history
        """

        # ensure type
        np_data = np.array(data)
        w_bal_hist = []

        # Wexp is the expended energy above CP or 0 if below CP
        np_exp = np.where((np_data - self._cp) > 0, np_data - self._cp, 0)

        # EQ (2) in Skiba et al. 2012
        for t in range(0, len(np_data)):
            sum_t = 0.0
            for u in range(0, t + 1):
                sum_t += np_exp[u] * pow(math.e, -(t - u) / tau)

            # apply limits
            sum_t = min(sum_t, self._w_p)
            w_bal_hist.append(self._w_p - sum_t)

        return w_bal_hist

    def _get_expenditure_dynamics(self, p_exp: float, tau: float):
        """
        returns expenditure dynamics given intensity p. Position 0 in the resulting array is time step 1.
        :param p_exp: constant exercise intensity in Watts
        :return: W'bal history
        """
        # Wexp is the expended energy above CP (here a constant)
        np_exp = p_exp - self._cp

        w_bal_hist = [self._w_p]
        # EQ (2) in Skiba et al. 2012
        t = 0
        max_steps = 5000
        while w_bal_hist[-1] > 0 and t < max_steps:
            sum_t = 0.0
            for u in range(0, t + 1):
                sum_t += np_exp * pow(math.e, -(t - u) / tau)

            # apply limits and append
            sum_t = min(sum_t, self._w_p)
            w_bal_hist.append(self._w_p - sum_t)
            t += 1

        if t >= max_steps:
            raise UserWarning("exhaustion not reached")

        # skip the first entry to conform to implementation by Clarke
        return w_bal_hist[1:]
